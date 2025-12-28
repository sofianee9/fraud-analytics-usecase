# - Use Case Study

Application d'analyse forensique documentaire pour la détection de fraudes.

## Objectif

Analyser des documents suspects (PDF, images) et identifier les falsifications à travers :
- Analyse des métadonnées (Producer, Creator, dates)
- Détection de logiciels de retouche (Photoshop, GIMP, Quartz...)
- Extraction EXIF des images
- Comparaison avec documents de référence

## Méthodologie

| Étape | Contrôle | Outil |
|-------|----------|-------|
| 1 | Métadonnées PDF | PyMuPDF |
| 2 | Métadonnées images (EXIF) | Pillow |
| 3 | Texte superposé | pdftotext |
| 4 | Vérification entreprises | Pappers, Societe.com |
| 5 | Analyse visuelle | Comparaison référence |
| 6 | Analyse temporelle | Cohérence des dates |

## Red Flags détectés

- Logiciels interdits : Photoshop, GIMP, Canva, Quartz, ImageMagick
- EXIF supprimées
- Dates incohérentes (PDF créé après/avant le document)
- Texte superposé (valeurs cachées sous le texte visible)
- Entreprises liquidées/radiées

## Résultats

- **11 documents analysés**
- **11 frauduleux** (100%)
- **Catégories :** Facturation, Banque/Assurance, Identité, Fiscalité

## Stack technique

- **Frontend :** Streamlit
- **Analyse PDF :** PyMuPDF (fitz)
- **Analyse images :** Pillow (PIL)
- **Persistance :** JSON + Base64

## Lancer l'application
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure
```
├── app.py                  # Application Streamlit
├── dossiers_fraude.json    # Base de données des dossiers
├── requirements.txt        # Dépendances Python
└── README.md

```
