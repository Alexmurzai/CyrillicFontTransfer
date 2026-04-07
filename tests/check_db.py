import os
from core.vector_db import FontVectorDB

db = FontVectorDB(persist_dir='fonts_db/chroma')
res = db.collection.get()
ids = res['ids']
print(f"Total fonts in DB: {len(ids)}")
has_perpetua = any("Perpetua" in font_id for font_id in ids)
print(f"Contains Perpetua? {has_perpetua}")

if has_perpetua:
    print("Found entries:")
    for font_id in ids:
        if "Perpetua" in font_id:
            print("  -", font_id)
else:
    print("Sample fonts in DB:", ids[:5])
