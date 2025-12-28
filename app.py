import streamlit as st
import fitz  # PyMuPDF
import re
from PIL import Image
import io
import datetime
import json
import base64
import os


# 1. CONFIGURATION & DESIGN

st.set_page_config(layout="wide", page_title="Use Case Study")
DB_FILE = "dossiers_fraude.json"

st.markdown("""
    <style>
    /* 1. FOND GENERAL TRES SOMBRE */
    .stApp {
        background-color: #0E1117;
        color: #E6E6E6;
    }
    
    /* 2. TITRES */
    h1 {
        border-bottom: 2px solid #D32F2F; 
        color: #FFFFFF; 
        padding-bottom: 15px; 
        text-transform: uppercase;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
        letter-spacing: 1px;
    }
    h3, h4 {
        color: #FFFFFF;
        font-weight: 600;
        margin-top: 20px;
    }
    
    /* 3. CONTENEURS (EXPANDERS) STYLE GITHUB DARK */
    .stExpander {
        background-color: #0D1117;
        border: 1px solid #30363D;
        border-radius: 6px;
        margin-bottom: 20px;
    }
    
    /* 4. INPUTS & CHAMPS METADONNEES (STYLE "Screen 2") */
    div[data-baseweb="input"] {
        background-color: #21262D; /* Gris foncé */
        border: 1px solid #30363D;
        border-radius: 4px;
        color: #C9D1D9;
    }
    div[data-baseweb="input"] > div {
        background-color: transparent;
        color: #C9D1D9;
    }
    /* Désactiver l'effet focus blanc */
    div[data-baseweb="base-input"]:focus-within {
        border-color: #58A6FF;
    }
    
    /* 5. SELECTBOX & TEXTAREA */
    div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
        background-color: #21262D;
        border: 1px solid #30363D;
        color: #C9D1D9;
    }

    /* 6. BOUTONS */
    div.stButton > button:first-child {
        background-color: #238636; /* Vert GitHub pour Action */
        color: white;
        border: 1px solid #2ea043;
        font-weight: bold;
        text-transform: uppercase;
        border-radius: 4px;
    }
    div.stButton > button:first-child:hover {
        background-color: #2ea043;
        border-color: #2ea043;
    }
    /* Bouton Supprimer spécifique (rouge sombre) */
    div[data-testid="stVerticalBlock"] > div > div > div > div > div.stButton > button {
        background-color: #21262D;
        border: 1px solid #30363D;
        color: #C9D1D9;
    }

    /* 7. STYLE PERSONNALISÉ POUR LES BADGES TECHNIQUE/VISUEL */
    .tech-badge {
        background-color: #0f2e1b; /* Vert très sombre */
        color: #2ea043;            /* Vert clair */
        border: 1px solid #1e4529;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
        margin-bottom: 10px;
        display: inline-block;
        width: 100%;
    }
    .visu-badge {
        background-color: #0d2339; /* Bleu très sombre */
        color: #2f81f7;            /* Bleu clair */
        border: 1px solid #183856;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
        margin-bottom: 10px;
        display: inline-block;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# 2. PERSISTANCE & IMAGES

def image_to_base64(img_obj):
    if img_obj is None: return None
    try:
        buf = io.BytesIO()
        img_obj.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except: return None

def base64_to_image(b64_str):
    if not b64_str: return None
    try:
        img_data = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(img_data))
    except: return None

def save_db():
    serializable_cases = []
    if 'cases' not in st.session_state: return
    for case in st.session_state['cases']:
        c = case.copy()
        c['img_suspect_clean'] = image_to_base64(case['img_suspect_clean'])
        c['img_annotated'] = image_to_base64(case['img_annotated'])
        c['img_ref'] = image_to_base64(case['img_ref'])
        serializable_cases.append(c)
    try:
        with open(DB_FILE, "w", encoding='utf-8', errors='ignore') as f:
            json.dump(serializable_cases, f, ensure_ascii=False, indent=4)
    except: pass

def load_db():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
        restored_cases = []
        for c in data:
            c['img_suspect_clean'] = base64_to_image(c.get('img_suspect_clean'))
            c['img_annotated'] = base64_to_image(c.get('img_annotated'))
            c['img_ref'] = base64_to_image(c.get('img_ref'))
            restored_cases.append(c)
        return restored_cases
    except: return []

if 'cases' not in st.session_state:
    st.session_state['cases'] = load_db()
if 'reset_counter' not in st.session_state:
    st.session_state['reset_counter'] = 0

# 3. MOTEUR ANALYSE

def format_pdf_date(date_str):
    if not date_str: return "Non spécifié"
    try:
        date_str = str(date_str)
        # Format EXIF: "YYYY:MM:DD HH:MM:SS"
        if re.match(r'^\d{4}:\d{2}:\d{2}', date_str):
            parts = date_str.split(' ')
            date_part = parts[0].replace(':', '/')
            time_part = parts[1] if len(parts) > 1 else ''
            # Reformater en DD/MM/YYYY
            ymd = date_part.split('/')
            if len(ymd) == 3:
                return f"{ymd[2]}/{ymd[1]}/{ymd[0]} à {time_part}" if time_part else f"{ymd[2]}/{ymd[1]}/{ymd[0]}"
        # Format PDF: "D:YYYYMMDDHHmmss"
        clean = date_str.replace("D:", "").replace("'", "").split('+')[0].split('Z')[0]
        if len(clean) >= 14: return f"{clean[6:8]}/{clean[4:6]}/{clean[:4]} à {clean[8:10]}:{clean[10:12]}"
        elif len(clean) >= 8: return f"{clean[6:8]}/{clean[4:6]}/{clean[:4]}"
        return clean
    except: return date_str

def detect_bad_software(producer, creator):
    forbidden_softs = ['photoshop', 'gimp', 'canva', 'illustrator', 'paint', 'quartz', 'indesign', 'word', 'powerpoint', 'libreoffice', 'ilovepdf', 'camscanner', 'imagemagick']
    prod_str = str(producer).lower()
    creat_str = str(creator).lower()
    return list(set([s for s in forbidden_softs if s in prod_str or s in creat_str]))

def clean_metadata_string(value):
    """Nettoie une chaîne de métadonnées pour éviter les erreurs de surrogates UTF-8"""
    if not value:
        return value
    try:
        return value.encode('utf-8', errors='surrogateescape').decode('utf-8', errors='replace')
    except:
        return str(value)

def extract_exif_data(img_bytes):
    """Extrait les données EXIF d'une image"""
    from PIL.ExifTags import TAGS
    try:
        img = Image.open(io.BytesIO(img_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return {}
        
        exif_dict = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            # Nettoyer les valeurs avec caractères nuls
            if isinstance(value, str):
                value = value.replace('\x00', '').strip()
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='ignore').replace('\x00', '').strip()
                except:
                    value = str(value)
            exif_dict[tag] = value
        return exif_dict
    except Exception as e:
        return {}

def extract_pdf_intelligence(file_buffer):
    file_bytes = file_buffer.read()
    
    # GESTION DES IMAGES (PNG, JPG, WEBP)
    if file_buffer.type != "application/pdf":
        img_preview = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        
        # Extraire les données EXIF
        exif = extract_exif_data(file_bytes)
        
        # Construire les métadonnées depuis EXIF
        make = exif.get('Make', '')
        model = exif.get('Model', '')
        software = exif.get('Software', '')
        datetime_orig = exif.get('DateTimeOriginal', exif.get('DateTime', ''))
        
        # Producer = Appareil photo
        if make and model:
            producer = f"{make} {model}".strip()
        elif make:
            producer = make
        elif model:
            producer = model
        else:
            producer = "Inconnu (EXIF absentes)"
        
        # Creator = Logiciel
        creator = software if software else "N/A"
        
        # Date de création
        creation_date = datetime_orig if datetime_orig else "Non spécifié"
        
        meta = {
            "producer": producer,
            "creator": creator,
            "creationDate": creation_date,
            "modDate": exif.get('DateTime', ''),
            "exif_raw": exif  # Garder les données brutes
        }
        
        # Détecter si EXIF supprimées (suspect)
        exif_status = "IMAGE (Pixelisé)"
        if not exif:
            exif_status = "IMAGE - ⚠️ EXIF SUPPRIMÉES"
        
        extra_meta = {
            "filesize": f"{len(file_bytes)/1024:.2f} KB",
            "type": exif_status,
            "encryption": "NON"
        }
        return meta, extra_meta, img_preview

    # GESTION DES PDF (MULTI-PAGES)
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    raw_meta = doc.metadata
    
    meta = {}
    for key, value in raw_meta.items():
        meta[key] = clean_metadata_string(value)
    
    full_text = "".join([page.get_text() for page in doc])
    is_native = len(full_text) > 50
    extra_meta = {
        "filesize": f"{len(file_bytes)/1024:.2f} KB",
        "type": "NATIF (Vectoriel)" if is_native else "SCAN (Pixelisé)",
        "encryption": "OUI" if doc.is_encrypted else "NON"
    }
    
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    
    total_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)
    combined_img = Image.new('RGB', (total_width, total_height))
    y_offset = 0
    for img in images:
        combined_img.paste(img, (0, y_offset))
        y_offset += img.height
        
    return meta, extra_meta, combined_img

def render_reference_doc(file_buffer):
    file_buffer.seek(0)
    if file_buffer.type == "application/pdf":
        doc = fitz.open(stream=file_buffer.read(), filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
        total_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)
        combined_img = Image.new('RGB', (total_width, total_height))
        y_offset = 0
        for img in images:
            combined_img.paste(img, (0, y_offset))
            y_offset += img.height
        return combined_img
    return Image.open(file_buffer).convert("RGB")

def combine_images_horizontal(images):
    """Combine plusieurs images horizontalement"""
    if not images:
        return None
    if len(images) == 1:
        return images[0]
    
    # Redimensionner toutes les images à la même hauteur
    max_height = max(img.height for img in images)
    resized = []
    for img in images:
        ratio = max_height / img.height
        new_width = int(img.width * ratio)
        resized.append(img.resize((new_width, max_height), Image.Resampling.LANCZOS))
    
    total_width = sum(img.width for img in resized)
    combined = Image.new('RGB', (total_width, max_height), (30, 30, 30))
    
    x_offset = 0
    for img in resized:
        combined.paste(img, (x_offset, 0))
        x_offset += img.width
    
    return combined

def convert_img_to_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

def archive_case_callback(case_data):
    st.session_state['cases'].append(case_data)
    save_db()
    st.session_state['reset_counter'] += 1
    st.success(f"Dossier archivé : {case_data['filename']}")

def delete_case(index):
    del st.session_state['cases'][index]
    save_db()
    st.rerun()

def extract_doc_number(case):
    """Extrait le numéro du document pour le tri (doc1 -> 1, doc2 -> 2, etc.)"""
    filename = case.get('filename', '')
    match = re.search(r'doc(\d+)', filename.lower())
    if match:
        return int(match.group(1))
    return 999  # Les docs sans numéro vont à la fin

# 4. INTERFACE UTILISATEUR

# EN-TÊTE
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("FINOVOX - Use Case Study")
with col_h2:
    st.write("")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding='utf-8') as f:
            st.download_button("SAUVEGARDER BASE JSON", f, "dossiers_fraude.json", "application/json")

st.markdown("---")

# SECTION 1 : WORKSPACE (Création)

with st.expander("NOUVELLE ANALYSE DE DOCUMENT", expanded=True):
    
    # 1. IMPORT MULTI-DOCUMENTS (jusqu'à 3)
    st.markdown("**DOCUMENTS SUSPECTS (jusqu'à 3 documents liés)**")
    c_up1, c_up2, c_up3 = st.columns(3)
    
    with c_up1:
        st.caption("📄 Document 1 (Principal)")
        uploaded_file1 = st.file_uploader("", type=["pdf", "png", "jpg", "jpeg"], key=f"suspect1_{st.session_state['reset_counter']}")
    with c_up2:
        st.caption("📄 Document 2 (Lié)")
        uploaded_file2 = st.file_uploader("", type=["pdf", "png", "jpg", "jpeg"], key=f"suspect2_{st.session_state['reset_counter']}")
    with c_up3:
        st.caption("📄 Document 3 (Lié)")
        uploaded_file3 = st.file_uploader("", type=["pdf", "png", "jpg", "jpeg"], key=f"suspect3_{st.session_state['reset_counter']}")
    
    st.markdown("---")
    
    # Document de référence
    st.markdown("**DOCUMENT ÉTALON (OPTIONNEL)**")
    reference_file = st.file_uploader("", type=["pdf", "png", "jpg", "jpeg"], key=f"ref_{st.session_state['reset_counter']}")

    # Collecter tous les fichiers uploadés
    uploaded_files = [f for f in [uploaded_file1, uploaded_file2, uploaded_file3] if f is not None]

    if uploaded_files:
        try:
            # Extraire les données de tous les documents
            all_images = []
            all_meta = []
            all_extra = []
            all_alerts = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                meta, extra, bg_image = extract_pdf_intelligence(uploaded_file)
                all_images.append(bg_image)
                all_meta.append(meta)
                all_extra.append(extra)
                
                prod = meta.get('producer', 'N/A')
                creat = meta.get('creator', 'N/A')
                alerts = detect_bad_software(prod, creat)
                all_alerts.extend(alerts)
                
                # Reset le buffer pour d'éventuelles réutilisations
                uploaded_file.seek(0)
            
            ref_image = render_reference_doc(reference_file) if reference_file else None
            
            # Image combinée pour archivage
            combined_suspect_image = combine_images_horizontal(all_images)
            
            st.markdown("---")

            # 2. VISUALISATION MULTI-DOCUMENTS
            st.markdown("### 1. INSPECTION VISUELLE")
            
            # Afficher chaque document suspect
            num_docs = len(all_images)
            if num_docs == 1:
                cols = st.columns([2, 1])
            elif num_docs == 2:
                cols = st.columns([1, 1, 1])
            else:
                cols = st.columns([1, 1, 1, 1])
            
            for idx, img in enumerate(all_images):
                with cols[idx]:
                    st.info(f"DOCUMENT {idx+1}: {uploaded_files[idx].name}")
                    st.image(img, use_container_width=True)
                    st.download_button(
                        f"📥 Télécharger Doc {idx+1}", 
                        convert_img_to_bytes(img), 
                        f"preuve_doc{idx+1}.png", 
                        "image/png",
                        key=f"dl_doc{idx}_{st.session_state['reset_counter']}"
                    )
            
            # Afficher la référence dans la dernière colonne
            with cols[-1] if num_docs < 3 else st.columns(1)[0]:
                if num_docs < 3:
                    st.success("RÉFÉRENCE / ÉTALON")
                    if ref_image: 
                        st.image(ref_image, use_container_width=True)
                    else: 
                        st.warning("NON FOURNI")

            if num_docs == 3 and ref_image:
                st.success("RÉFÉRENCE / ÉTALON")
                st.image(ref_image, use_container_width=True)

            st.markdown("---")

            # 3. DONNÉES TECHNIQUES (pour chaque document)
            st.markdown("### 2. AUDIT MÉTADONNÉES")
            
            for idx, (meta, extra) in enumerate(zip(all_meta, all_extra)):
                st.markdown(f"**📄 Document {idx+1}: {uploaded_files[idx].name}**")
                
                prod = meta.get('producer', 'N/A')
                creat = meta.get('creator', 'N/A')
                d_crea = format_pdf_date(meta.get('creationDate', ''))
                d_mod = format_pdf_date(meta.get('modDate', ''))
                doc_alerts = detect_bad_software(prod, creat)

                k1, k2, k3 = st.columns(3)
                with k1:
                    st.text_input(f"LOGICIEL (PRODUCER)", value=prod, disabled=True, key=f"prod_{idx}_{st.session_state['reset_counter']}", help="Logiciel ayant généré le PDF. ALERTE si Photoshop, GIMP, Canva, Word, Quartz, ImageMagick...")
                    st.text_input(f"CRÉATEUR (CREATOR)", value=creat, disabled=True, key=f"creat_{idx}_{st.session_state['reset_counter']}", help="Application ou auteur à l'origine du document. Peut révéler une modification.")
                    if doc_alerts: 
                        st.error(f"🚨 ALERTE : LOGICIEL INTERDIT ({', '.join(doc_alerts)})")
                with k2:
                    st.text_input(f"CRÉÉ LE", value=d_crea, disabled=True, key=f"dcrea_{idx}_{st.session_state['reset_counter']}", help="Date de création du fichier PDF. À comparer avec la date affichée sur le document.")
                    st.text_input(f"MODIFIÉ LE", value=d_mod, disabled=True, key=f"dmod_{idx}_{st.session_state['reset_counter']}", help="Date de dernière modification. Si différente de la création = retouche suspecte.")
                with k3:
                    st.text_input(f"NATURE", value=extra['type'], disabled=True, key=f"type_{idx}_{st.session_state['reset_counter']}", help="NATIF = texte vectoriel (copier/coller possible). SCAN = image pixelisée. EXIF SUPPRIMÉES = manipulation probable.")
                    st.text_input(f"POIDS", value=extra['filesize'], disabled=True, key=f"size_{idx}_{st.session_state['reset_counter']}", help="Taille du fichier. Un poids anormalement élevé peut indiquer des calques/images cachées.")
                
                if idx < len(all_meta) - 1:
                    st.markdown("---")

            st.markdown("---")

            # 4. CLÔTURE
            st.markdown("### 3. CLÔTURE DU DOSSIER")
            cw1, cw2 = st.columns([1, 2])
            
            with cw1:
                st.markdown("**A. PREUVE VISUELLE (ANNOTÉE)**")
                annotated_file = st.file_uploader("Charger l'image avec cercles rouges", type=["png", "jpg", "jpeg"], key=f"ano_{st.session_state['reset_counter']}")
                annotated_image_obj = Image.open(annotated_file) if annotated_file else None
                if annotated_image_obj: 
                    st.image(annotated_image_obj, use_container_width=True)

            with cw2:
                with st.form("closing_form"):
                    st.markdown("**B. RAPPORT D'INVESTIGATION**")
                    cat = st.selectbox("CATÉGORIE", ["Fiscalité", "Facturation", "Banque/Assurance", "Identité"])
                    reason = st.text_input("MOBILE / CONTEXTE", help="Pourquoi le fraudeur a-t-il modifié ce document ? Quel est son intérêt ?")
                    verdict = st.radio("VERDICT", ["[VALIDE] AUTHENTIQUE", "[REJETE] FRAUDULEUX", "[SUSPECT] A VÉRIFIER"], index=1)
                    m_tech = st.text_area("OBSERVATIONS TECHNIQUES (FORENSIQUE)", help="Détails des incohérences métadonnées, dates, logiciels...")
                    m_visu = st.text_area("OBSERVATIONS VISUELLES (GRAPHIQUE)", help="Détails des incohérences de police, alignement, montage...")

                    if st.form_submit_button("VALIDER ET ARCHIVER"):
                        if not annotated_image_obj:
                            st.error("ACTION REQUISE : CHARGER LA PREUVE VISUELLE.")
                        else:
                            # Collecter toutes les métadonnées
                            combined_meta = {
                                "nb_documents": len(uploaded_files),
                                "documents": []
                            }
                            for idx, (meta, extra, uf) in enumerate(zip(all_meta, all_extra, uploaded_files)):
                                combined_meta["documents"].append({
                                    "filename": uf.name,
                                    "producer": meta.get('producer', 'N/A'),
                                    "creator": meta.get('creator', 'N/A'),
                                    "d_crea": format_pdf_date(meta.get('creationDate', '')),
                                    "d_mod": format_pdf_date(meta.get('modDate', '')),
                                    "type": extra['type'],
                                    "filesize": extra['filesize']
                                })
                            
                            # Noms des fichiers combinés
                            filenames = " + ".join([f.name for f in uploaded_files])
                            
                            case_data = {
                                "filename": filenames,
                                "category": cat,
                                "verdict": verdict,
                                "reason": reason,
                                "method_tech": m_tech,
                                "method_visu": m_visu,
                                "img_suspect_clean": combined_suspect_image,
                                "img_annotated": annotated_image_obj, 
                                "img_ref": ref_image,
                                "full_meta": combined_meta
                            }
                            archive_case_callback(case_data)
                            st.rerun()
        except Exception as e:
            st.error(f"ERREUR ANALYSE: {e}")
            import traceback
            st.code(traceback.format_exc())

# SECTION 2 : ARCHIVES

st.write("")
st.markdown("### DOSSIERS TRAITÉS")

if not st.session_state['cases']:
    st.info("AUCUN DOSSIER ARCHIVÉ.")

# Trier par numéro de document (doc1, doc2, ... doc11)
sorted_cases = sorted(st.session_state['cases'], key=extract_doc_number)

for i, case in enumerate(sorted_cases):
    
    title = f"{case['verdict']} | {case.get('category', 'Dossier')} | {case['filename']}"
    
    with st.expander(title):
        
        # 1. ZONE IMAGES : 3 COLONNES
        st.markdown("#### ÉLÉMENTS DE PREUVE")
        col_img1, col_img2, col_img3 = st.columns(3)
        
        with col_img1:
            st.caption("ORIGINAL(S)")
            if case['img_suspect_clean']:
                st.image(case['img_suspect_clean'], use_container_width=True)
        
        with col_img2:
            st.caption("PREUVE ANNOTÉE")
            if case['img_annotated']: 
                st.image(case['img_annotated'], use_container_width=True)
            else: 
                st.warning("Manquant")
            
        with col_img3:
            st.caption("ÉTALON / RÉFÉRENCE")
            if case['img_ref']: 
                st.image(case['img_ref'], use_container_width=True)
            else: 
                st.info("Pas de document de référence")

        st.markdown("---")

        # 2. ZONE RAPPORT
        st.markdown("#### RAPPORT D'ANALYSE")
        st.markdown(f"**Mobile :** {case.get('reason', 'N/A')}")
        st.markdown(f"**Verdict :** {case['verdict']}")
        st.write("")
        
        c_rap1, c_rap2 = st.columns(2)
        with c_rap1:
            st.markdown('<div class="tech-badge">Technique</div>', unsafe_allow_html=True)
            st.write(case['method_tech'])
        
        with c_rap2:
            st.markdown('<div class="visu-badge">Visuel</div>', unsafe_allow_html=True)
            st.write(case['method_visu'])

        st.markdown("---")

        # 3. ZONE MÉTADONNÉES BRUTES
        st.markdown("#### DONNÉES TECHNIQUES BRUTES (ARCHIVE)")
        
        fm = case.get('full_meta', {})
        
        # format multi-documents
        if 'documents' in fm:
            for doc_idx, doc_meta in enumerate(fm['documents']):
                st.markdown(f"**📄 Document {doc_idx+1}: {doc_meta.get('filename', 'N/A')}**")
                k1, k2, k3 = st.columns(3)
                with k1:
                    st.text_input(f"Producer", value=doc_meta.get('producer', 'N/A'), disabled=True, key=f"arch_prod_{i}_{doc_idx}", help="Logiciel ayant généré le PDF")
                    st.text_input(f"Creator", value=doc_meta.get('creator', 'N/A'), disabled=True, key=f"arch_creat_{i}_{doc_idx}", help="Application ou auteur d'origine")
                with k2:
                    st.text_input(f"Créé le", value=doc_meta.get('d_crea', 'N/A'), disabled=True, key=f"arch_crea_{i}_{doc_idx}", help="Date de création du fichier")
                    st.text_input(f"Modifié le", value=doc_meta.get('d_mod', 'N/A'), disabled=True, key=f"arch_mod_{i}_{doc_idx}", help="Date de dernière modification")
                with k3:
                    st.text_input(f"Taille", value=doc_meta.get('filesize', 'N/A'), disabled=True, key=f"arch_size_{i}_{doc_idx}", help="Poids du fichier")
                    st.text_input(f"Nature", value=doc_meta.get('type', 'N/A'), disabled=True, key=f"arch_type_{i}_{doc_idx}", help="Type: NATIF/SCAN/IMAGE")
        else:
            # Ancien format (rétrocompatibilité)
            p = fm.get('producer') or 'N/A'
            c = fm.get('creator') or 'N/A'
            dc = fm.get('d_crea') or 'N/A'
            dm = fm.get('d_mod') or 'N/A'
            sz = fm.get('filesize') or 'N/A'
            tp = fm.get('type') or 'N/A'

            k1, k2, k3 = st.columns(3)
            with k1:
                st.text_input(f"Producer", value=p, disabled=True, key=f"arch_prod_{i}", help="Logiciel ayant généré le PDF")
                st.text_input(f"Creator", value=c, disabled=True, key=f"arch_creat_{i}", help="Application ou auteur d'origine")
            with k2:
                st.text_input(f"Créé le", value=dc, disabled=True, key=f"arch_crea_{i}", help="Date de création du fichier")
                st.text_input(f"Modifié le", value=dm, disabled=True, key=f"arch_mod_{i}", help="Date de dernière modification")
            with k3:
                st.text_input(f"Taille", value=sz, disabled=True, key=f"arch_size_{i}", help="Poids du fichier")
                st.text_input(f"Nature", value=tp, disabled=True, key=f"arch_type_{i}", help="Type: NATIF/SCAN/IMAGE")
            
        st.write("")
        # Trouver l'index original pour la suppression
        original_index = st.session_state['cases'].index(case)
        if st.button("Supprimer", key=f"del_{i}"):
            delete_case(original_index)