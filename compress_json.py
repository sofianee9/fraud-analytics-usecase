import json
import base64
import io
from PIL import Image

def compress_image_b64(b64_string, max_size=800, quality=50):
    if not b64_string:
        return b64_string
    try:
        img_data = base64.b64decode(b64_string)
        img = Image.open(io.BytesIO(img_data))
        
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
        
        return base64.b64encode(buffer.getvalue()).decode()
    except:
        return b64_string

with open("dossiers_fraude.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for i, dossier in enumerate(data):
    print(f"Compression dossier {i+1}/{len(data)}...")
    if dossier.get("img_suspect_clean"):
        dossier["img_suspect_clean"] = compress_image_b64(dossier["img_suspect_clean"])
    if dossier.get("img_annotated"):
        dossier["img_annotated"] = compress_image_b64(dossier["img_annotated"])
    if dossier.get("img_ref"):
        dossier["img_ref"] = compress_image_b64(dossier["img_ref"])

with open("dossiers_fraude.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print("✅ JSON compressé !")