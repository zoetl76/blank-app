"""
sheets.py — accès aux 4 Google Sheets de l'agence via gspread (compte de service).

Le JSON du compte de service reste en LOCAL (hors repo) ; on le pointe via la
variable d'environnement GOOGLE_APPLICATION_CREDENTIALS.

    from sheets import load_sheet, taux_occupation
    vehicules = load_sheet("vehicules")          # list[dict]
    occ = taux_occupation()                       # float 0..1
"""

from __future__ import annotations

import os
import gspread
from google.oauth2.service_account import Credentials

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# IDs des Sheets du dossier "Agence Location Auto"
SHEET_IDS = {
    "vehicules":    "1qkOGw1o4z8loeZJHO8G-H0fo1zauSIqAYszwNKbXosY",
    "clients":      "1YHQXjmT_MoxmTqfjbwTy8RdGemIuTaLwbyNKaAjjOAg",
    "reservations": "1aZXZptv-8Wru3NwqOes8ExPGs0TML8h8x9y2EnrMkDI",
    "contrats":     "12055_F02XgLIrrIgggWQQ-KPKoort7CYemtORj6rtt8",
}


def _client() -> gspread.Client:
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not path:
        raise SystemExit("Définis GOOGLE_APPLICATION_CREDENTIALS (JSON du compte de service).")
    creds = Credentials.from_service_account_file(path, scopes=_SCOPES)
    return gspread.authorize(creds)


def load_sheet(nom: str) -> list[dict]:
    """Renvoie le contenu d'une feuille en list[dict] (même format que load_csv)."""
    if nom not in SHEET_IDS:
        raise KeyError(f"Feuille inconnue : {nom}. Choix : {list(SHEET_IDS)}")
    ws = _client().open_by_key(SHEET_IDS[nom]).sheet1
    return ws.get_all_records()


def taux_occupation() -> float:
    """Part de la flotte actuellement louée (pour la tarification dynamique)."""
    v = load_sheet("vehicules")
    if not v:
        return 0.0
    loues = sum(1 for x in v if str(x.get("statut", "")).strip().lower() == "loué")
    return loues / len(v)
