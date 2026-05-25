# Agence Location Auto

Application de gestion d'une agence de location de voitures, avec 4 fonctionnalités IA (Claude) : tarification dynamique, génération d'annonces, synthèse de dossiers clients, génération de contrats + chatbot FAQ.

## Lancer en local
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py   # http://localhost:8501
```
L'app tourne en **mode démo** (données d'exemple intégrées) sans aucune config. Pour activer l'IA et les vraies données, voir ci-dessous.

## Secrets (jamais committés)
Copier `streamlit_secrets_TEMPLATE.toml` en `.streamlit/secrets.toml` et renseigner :
- `ANTHROPIC_API_KEY` — clé API Claude (active les fonctions IA)
- `GOOGLE_APPLICATION_CREDENTIALS` ou table `[gcp_service_account]` — compte de service Google (lecture des Google Sheets de données)

## Déploiement Streamlit Community Cloud
1. Pousser ce repo sur GitHub (sans secrets).
2. https://share.streamlit.io → New app → ce repo, `streamlit_app.py`.
3. Settings → Secrets → coller le contenu rempli du template.

## Fichiers
- `streamlit_app.py` — interface Streamlit (toutes les pages)
- `agence_ia.py` — les 4 fonctions IA (SDK Anthropic, prompt caching)
- `sheets.py` — accès aux Google Sheets via gspread
- `requirements.txt` — dépendances

Les données opérationnelles vivent dans des Google Sheets (hors repo). Les secrets restent hors du repo.
