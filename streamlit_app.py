"""
app.py — Interface Streamlit de l'agence de location de voitures.

Lancer en local :  streamlit run app.py   (ouvre http://localhost:8501)

Données : si GOOGLE_APPLICATION_CREDENTIALS est configuré -> lit les vrais Google
Sheets via sheets.py ; sinon -> MODE DÉMO sur des données d'exemple intégrées.
IA : les boutons IA s'activent si ANTHROPIC_API_KEY est défini.
Secrets : via variables d'environnement ou st.secrets — JAMAIS dans le dépôt.
"""

import os
import streamlit as st

# --- Pont st.secrets -> variables d'environnement (anthropic & gspread les lisent) ---
try:
    _secrets = dict(st.secrets)
except Exception:
    _secrets = {}
for _k in ("ANTHROPIC_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"):
    if _k in _secrets and not os.environ.get(_k):
        os.environ[_k] = str(_secrets[_k])

st.set_page_config(page_title="Agence Location Auto", page_icon="🚗", layout="wide")

# ---------------------------------------------------------------- Données démo
SAMPLE = {
    "vehicules": [
        {"id": "V001", "marque": "Renault", "modele": "Clio V", "annee": 2023,
         "immatriculation": "AB-123-CD", "categorie": "Citadine", "carburant": "Essence",
         "km": 28450, "statut": "disponible", "tarif_base_jour_eur": 39},
        {"id": "V002", "marque": "Peugeot", "modele": "3008", "annee": 2022,
         "immatriculation": "EF-456-GH", "categorie": "SUV", "carburant": "Diesel",
         "km": 51200, "statut": "loué", "tarif_base_jour_eur": 72},
        {"id": "V003", "marque": "Tesla", "modele": "Model 3", "annee": 2024,
         "immatriculation": "IJ-789-KL", "categorie": "Berline", "carburant": "Électrique",
         "km": 12300, "statut": "disponible", "tarif_base_jour_eur": 95},
        {"id": "V004", "marque": "Citroën", "modele": "Berlingo", "annee": 2021,
         "immatriculation": "MN-012-OP", "categorie": "Utilitaire", "carburant": "Diesel",
         "km": 88700, "statut": "maintenance", "tarif_base_jour_eur": 55},
        {"id": "V005", "marque": "Volkswagen", "modele": "Golf 8", "annee": 2023,
         "immatriculation": "QR-345-ST", "categorie": "Compacte", "carburant": "Essence",
         "km": 34100, "statut": "disponible", "tarif_base_jour_eur": 49},
    ],
    "clients": [
        {"id": "C001", "nom": "Martin", "prenom": "Sophie", "email": "sophie.martin@email.fr",
         "telephone": "0611223344", "permis_numero": "123456789012",
         "permis_obtention": "2015-06-01", "date_naissance": "1990-03-22", "notes": "Cliente régulière"},
        {"id": "C002", "nom": "Dubois", "prenom": "Karim", "email": "karim.dubois@email.fr",
         "telephone": "0622334455", "permis_numero": "234567890123",
         "permis_obtention": "2022-09-15", "date_naissance": "2003-11-08", "notes": "Jeune permis"},
        {"id": "C003", "nom": "Nguyen", "prenom": "Léa", "email": "lea.nguyen@email.fr",
         "telephone": "0633445566", "permis_numero": "345678901234",
         "permis_obtention": "2010-01-20", "date_naissance": "1985-07-30", "notes": "RAS"},
    ],
    "reservations": [
        {"id": "R001", "vehicule_id": "V002", "client_id": "C001", "date_debut": "2026-05-20",
         "date_fin": "2026-05-27", "jours": 7, "prix_jour_eur": 72, "prix_total_eur": 504, "statut": "en_cours"},
        {"id": "R002", "vehicule_id": "V003", "client_id": "C003", "date_debut": "2026-06-01",
         "date_fin": "2026-06-05", "jours": 4, "prix_jour_eur": 95, "prix_total_eur": 380, "statut": "confirmée"},
        {"id": "R003", "vehicule_id": "V001", "client_id": "C002", "date_debut": "2026-05-30",
         "date_fin": "2026-06-02", "jours": 3, "prix_jour_eur": 39, "prix_total_eur": 117, "statut": "en_attente"},
    ],
    "contrats": [
        {"id": "CT001", "reservation_id": "R001", "date_signature": "2026-05-20",
         "caution_eur": 1000, "franchise_eur": 800, "conditions": "Kilométrage illimité ; carburant restitué plein"},
        {"id": "CT002", "reservation_id": "R002", "date_signature": "2026-05-24",
         "caution_eur": 1500, "franchise_eur": 1000, "conditions": "200 km/jour inclus ; recharge à la charge du client"},
    ],
}


@st.cache_data(ttl=300)
def load(nom):
    """(données, mode). 'live' si Sheets, 'démo' sinon."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            import sheets
            return sheets.load_sheet(nom), "live"
        except Exception as e:
            return SAMPLE[nom], f"démo (Sheets indisponible : {e})"
    return SAMPLE[nom], "démo"


def occupation(vehicules):
    if not vehicules:
        return 0.0
    loues = sum(1 for v in vehicules if str(v.get("statut", "")).strip().lower() == "loué")
    return loues / len(vehicules)


def ai_ready():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def call_ai(fn_name, *args, **kwargs):
    """Importe agence_ia à la demande (le client n'est créé que si clé présente)."""
    if not ai_ready():
        st.warning("Définis ANTHROPIC_API_KEY (variable d'env ou st.secrets) pour activer l'IA.")
        return None
    try:
        import agence_ia
        return getattr(agence_ia, fn_name)(*args, **kwargs)
    except Exception as e:
        st.error(f"Erreur IA : {e}")
        return None


# ---------------------------------------------------------------- Mise en page
st.title("🚗 Agence Location Auto")
vehicules, mode = load("vehicules")
st.caption(f"Source de données : **{mode}** · IA : {'✅ active' if ai_ready() else '⚠️ clé manquante'}")

page = st.sidebar.radio(
    "Navigation",
    ["Tableau de bord", "Véhicules & annonces", "Tarification", "Clients & dossiers",
     "Contrats", "Chatbot"],
)

# ---- Tableau de bord ----
if page == "Tableau de bord":
    reservations, _ = load("reservations")
    c1, c2, c3 = st.columns(3)
    c1.metric("Véhicules", len(vehicules))
    c2.metric("Occupation flotte", f"{occupation(vehicules):.0%}")
    c3.metric("Réservations actives",
              sum(1 for r in reservations if r.get("statut") in ("en_cours", "confirmée")))
    st.subheader("Flotte")
    st.dataframe(vehicules, use_container_width=True)
    st.subheader("Réservations")
    st.dataframe(reservations, use_container_width=True)

# ---- Véhicules & annonces ----
elif page == "Véhicules & annonces":
    st.dataframe(vehicules, use_container_width=True)
    label = lambda v: f"{v['id']} — {v['marque']} {v['modele']}"
    veh = next(v for v in vehicules if label(v) ==
               st.selectbox("Véhicule", [label(v) for v in vehicules]))
    if st.button("✍️ Générer l'annonce"):
        with st.spinner("Rédaction…"):
            out = call_ai("annonce_auto", veh)
        if out:
            st.text_area("Annonce générée", out, height=200)

# ---- Tarification ----
elif page == "Tarification":
    dispo = [v for v in vehicules if str(v.get("statut")).lower() == "disponible"]
    if not dispo:
        st.info("Aucun véhicule disponible.")
    else:
        label = lambda v: f"{v['id']} — {v['marque']} {v['modele']} ({v['tarif_base_jour_eur']} €/j)"
        veh = next(v for v in dispo if label(v) ==
                   st.selectbox("Véhicule disponible", [label(v) for v in dispo]))
        col1, col2 = st.columns(2)
        d1 = col1.date_input("Début")
        d2 = col2.date_input("Fin")
        saison = st.selectbox("Saison", ["hiver", "printemps", "été", "automne"], index=2)
        if st.button("💶 Suggérer un prix"):
            with st.spinner("Calcul…"):
                out = call_ai("tarification_dynamique", veh, str(d1), str(d2),
                              occupation(vehicules), saison)
            if out:
                st.success(out)
                st.caption("Suggestion — à valider par un humain.")

# ---- Clients & dossiers ----
elif page == "Clients & dossiers":
    clients, _ = load("clients")
    st.dataframe(clients, use_container_width=True)
    label = lambda c: f"{c['id']} — {c['prenom']} {c['nom']}"
    cli = next(c for c in clients if label(c) ==
               st.selectbox("Client", [label(c) for c in clients]))
    hist = st.text_input("Historique de location", "Aucun antécédent connu.")
    if st.button("🔎 Synthèse du dossier"):
        with st.spinner("Analyse…"):
            out = call_ai("synthese_dossier", cli, hist)
        if out:
            st.text_area("Synthèse (aide à la décision)", out, height=220)
            st.caption("Aide à la décision — décision finale humaine, sans critère discriminatoire.")

# ---- Contrats ----
elif page == "Contrats":
    reservations, _ = load("reservations")
    clients, _ = load("clients")
    by_id = lambda items, i, k="id": next((x for x in items if x[k] == i), {})
    res = next(r for r in reservations if r["id"] ==
               st.selectbox("Réservation", [r["id"] for r in reservations]))
    veh = by_id(vehicules, res["vehicule_id"])
    cli = by_id(clients, res["client_id"])
    st.write(f"**{cli.get('prenom','?')} {cli.get('nom','?')}** — "
             f"{veh.get('marque','?')} {veh.get('modele','?')} — "
             f"{res['date_debut']} → {res['date_fin']}")
    caution = st.number_input("Caution (€)", value=1000.0, step=100.0)
    franchise = st.number_input("Franchise (€)", value=800.0, step=100.0)
    conditions = st.text_input("Conditions", "Kilométrage illimité ; carburant restitué plein")
    if st.button("📄 Générer le contrat"):
        with st.spinner("Rédaction du contrat…"):
            out = call_ai("generer_contrat", res, veh, cli, caution, franchise, conditions)
        if out:
            st.text_area("Contrat (modèle — à faire valider par un juriste)", out, height=400)
            st.download_button("Télécharger (.txt)", out,
                               file_name=f"contrat_{res['id']}.txt")

# ---- Chatbot ----
elif page == "Chatbot":
    st.subheader("Assistant FAQ")
    contexte = st.text_area("Contexte (conditions, tarifs, politique)",
                            "Restitution uniquement à l'agence de départ. "
                            "Caution demandée à la prise du véhicule. "
                            "Annulation gratuite jusqu'à 48 h avant le départ.", height=100)
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for role, msg in st.session_state.chat:
        st.chat_message(role).write(msg)
    if q := st.chat_input("Votre question"):
        st.session_state.chat.append(("user", q))
        st.chat_message("user").write(q)
        rep = call_ai("chatbot_faq", q, contexte) or "(IA indisponible)"
        st.session_state.chat.append(("assistant", rep))
        st.chat_message("assistant").write(rep)
