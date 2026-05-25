"""
agence_ia.py — Fonctionnalités IA de l'agence de location de voitures.

4 briques : tarification dynamique, annonces auto, synthèse de dossier client,
génération de contrat + chatbot FAQ.

Backend : GitHub Models (API compatible OpenAI), gratuit dans la limite du palier
GitHub. On l'authentifie avec un token GitHub disposant de la permission "Models".

Prérequis :
    pip install -r requirements.txt
    export GITHUB_MODELS_TOKEN="github_pat_..."   # token fine-grained, scope Models
    # (à défaut, GITHUB_TOKEN est aussi accepté)

⚠️ Palier gratuit = rate-limité (quelques req/min, plafond journalier) : OK pour
démo, pas pour du trafic réel.
"""

from __future__ import annotations

import csv
import os
from openai import OpenAI

# Endpoint GitHub Models (compatible OpenAI).
_ENDPOINT = "https://models.inference.ai.azure.com"

# Modèles dispo sur GitHub Models (gratuit). gpt-4o-mini suffit partout ;
# passe MODEL_JUGEMENT à "gpt-4o" pour la synthèse de dossier si ton quota le permet.
MODEL_RAPIDE = "gpt-4o-mini"
MODEL_JUGEMENT = "gpt-4o-mini"

_client = None


def _get_client() -> OpenAI:
    """Client paresseux : instancié seulement quand on appelle l'IA."""
    global _client
    if _client is None:
        token = os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("Définis GITHUB_MODELS_TOKEN (token GitHub, permission Models).")
        _client = OpenAI(base_url=_ENDPOINT, api_key=token)
    return _client


def _ask(system: str, user: str, model: str = MODEL_RAPIDE, max_tokens: int = 1024) -> str:
    resp = _get_client().chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return (resp.choices[0].message.content or "").strip()


# ============================================================ a) TARIFICATION
_SYS_TARIF = (
    "Tu es l'outil de tarification dynamique d'une agence de location de voitures. "
    "À partir des caractéristiques du véhicule, des dates, du taux d'occupation de "
    "la flotte et de la saison, tu proposes un PRIX/JOUR en euros et une courte "
    "justification (1-2 phrases). Règles : prix >= tarif de base ; majoration si "
    "forte demande / haute saison / faible disponibilité ; remise possible si longue "
    "durée. Réponds STRICTEMENT au format : 'PRIX: <nombre> EUR | RAISON: <texte>'. "
    "Le prix proposé reste une SUGGESTION validée ensuite par un humain."
)

def tarification_dynamique(vehicule: dict, date_debut: str, date_fin: str,
                           taux_occupation: float, saison: str) -> str:
    u = (f"Véhicule : {vehicule.get('marque')} {vehicule.get('modele')} "
         f"({vehicule.get('categorie')}, {vehicule.get('carburant')}), "
         f"tarif_base_jour={vehicule.get('tarif_base_jour_eur')} EUR.\n"
         f"Période : {date_debut} -> {date_fin}.\n"
         f"Taux d'occupation flotte : {taux_occupation:.0%}. Saison : {saison}.")
    return _ask(_SYS_TARIF, u)


# ============================================================ b) ANNONCES AUTO
_SYS_ANNONCE = (
    "Tu es rédacteur d'annonces pour une agence de location de voitures. À partir "
    "des caractéristiques d'un véhicule, tu produis un TITRE accrocheur (<= 70 "
    "caractères) et une DESCRIPTION commerciale honnête de 3-4 phrases mettant en "
    "avant les points forts réels. Pas d'invention de caractéristiques. Format : "
    "'TITRE: <...>\\nDESCRIPTION: <...>'."
)

def annonce_auto(vehicule: dict) -> str:
    u = "\n".join(f"{k}: {v}" for k, v in vehicule.items())
    return _ask(_SYS_ANNONCE, u)


# ============================================================ c) SYNTHÈSE DOSSIER
_SYS_DOSSIER = (
    "Tu aides une agence de location à PRÉ-ANALYSER un dossier client. Tu produis "
    "une SYNTHÈSE neutre, un SCORE indicatif de 0 à 100 (fiabilité du dossier) et "
    "les POINTS D'ATTENTION factuels (ex. permis récent, âge, données manquantes). "
    "IMPORTANT : tu ne prononces PAS de refus, tu n'utilises AUCUN critère "
    "discriminatoire (origine, sexe, etc.) ; tu fournis une aide à la décision, la "
    "décision finale et sa motivation restent HUMAINES. Format : "
    "'SCORE: <0-100>\\nSYNTHÈSE: <...>\\nATTENTION: <puces>'."
)

def synthese_dossier(client: dict, historique: str = "Aucun antécédent connu.") -> str:
    u = ("Profil client :\n" + "\n".join(f"{k}: {v}" for k, v in client.items())
         + f"\nHistorique de location : {historique}")
    return _ask(_SYS_DOSSIER, u, model=MODEL_JUGEMENT)


# ============================================================ d) CONTRAT + CHATBOT
_SYS_CONTRAT = (
    "Tu rédiges un CONTRAT DE LOCATION DE VÉHICULE pré-rempli en français à partir "
    "des données fournies (locataire, véhicule, dates, prix, caution, franchise, "
    "conditions). Style clair et juridique, avec les clauses usuelles (durée, prix, "
    "caution, assurance, état des lieux, restitution, responsabilités). Laisse des "
    "[CHAMPS À COMPLÉTER] pour ce qui manque. Ce contrat est un MODÈLE à faire "
    "valider par un juriste avant usage réel."
)

def generer_contrat(reservation: dict, vehicule: dict, client: dict,
                    caution_eur: float, franchise_eur: float, conditions: str) -> str:
    u = (f"LOCATAIRE : {client.get('prenom')} {client.get('nom')}, "
         f"permis {client.get('permis_numero')} (obtenu {client.get('permis_obtention')}).\n"
         f"VÉHICULE : {vehicule.get('marque')} {vehicule.get('modele')} "
         f"{vehicule.get('annee')}, imm. {vehicule.get('immatriculation')}.\n"
         f"PÉRIODE : {reservation.get('date_debut')} -> {reservation.get('date_fin')} "
         f"({reservation.get('jours')} jours) à {reservation.get('prix_jour_eur')} EUR/j, "
         f"total {reservation.get('prix_total_eur')} EUR.\n"
         f"CAUTION : {caution_eur} EUR. FRANCHISE : {franchise_eur} EUR.\n"
         f"CONDITIONS : {conditions}")
    return _ask(_SYS_CONTRAT, u, max_tokens=2048)


_SYS_CHATBOT = (
    "Tu es l'assistant FAQ d'une agence de location de voitures. Tu réponds aux "
    "clients de façon brève, polie et factuelle, à partir du CONTEXTE fourni "
    "(conditions, tarifs, politique). Si l'info n'est pas dans le contexte, tu le "
    "dis et tu renvoies vers un conseiller humain. Pas d'engagement contractuel."
)

def chatbot_faq(question: str, contexte: str = "") -> str:
    u = f"CONTEXTE :\n{contexte}\n\nQUESTION DU CLIENT : {question}"
    return _ask(_SYS_CHATBOT, u)


# ============================================================ Utilitaires données
def load_csv(path: str) -> list[dict]:
    """Charge un export CSV d'un des Google Sheets en liste de dicts."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
