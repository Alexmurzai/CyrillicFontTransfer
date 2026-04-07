import os
import json
from fontTools.ttLib import TTFont
from tqdm import tqdm
from pathlib import Path

def check_font_support(font_path):
    """
    Проверяет поддержку набора символов шрифтом.
    Возвращает словарь с флагами для латиницы и кириллицы.
    """
    try:
        font = TTFont(font_path, fontNumber=0) # fontNumber=0 для TTC/OTF коллекций
        cmap = font.getBestCmap()
        if not cmap:
            return None
        
        # Латиница (A-Z, a-z)
        latin_range = range(0x0041, 0x007B) # A-Z, [,\,],^,_,`, a-z
        latin_count = sum(1 for code in latin_range if code in cmap)
        has_latin = latin_count > 40 # Ожидаем большинство символов A-Z/a-z

        # Кириллица (А-Я, а-я)
        cyrillic_range = range(0x0410, 0x0450)
        cyrillic_count = sum(1 for code in cyrillic_range if code in cmap)
        has_cyrillic = cyrillic_count > 60

        return {
            "name": font_path.name,
            "path": str(font_path.absolute()),
            "latin": bool(has_latin),
            "cyrillic": bool(has_cyrillic),
            "count": {"lat": latin_count, "cyr": cyrillic_count}
        }
    except Exception as e:
        print(f"Error processing {font_path}: {e}")
        return None

def build_index(font_dirs, output_json):
    index = {"latin": [], "cyrillic": [], "both": []}
    
    all_files = []
    for d in font_dirs:
        path = Path(d)
        if path.exists():
            all_files.extend(list(path.glob("**/*.ttf")) + list(path.glob("**/*.otf")))

    print(f"Found {len(all_files)} font files. Scanning...")
    
    for f in tqdm(all_files):
        res = check_font_support(f)
        if res:
            if res["latin"] and res["cyrillic"]:
                index["both"].append(res)
            elif res["latin"]:
                index["latin"].append(res)
            elif res["cyrillic"]:
                index["cyrillic"].append(res)

    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(index, jf, indent=4, ensure_ascii=False)
    
    print(f"\nIndexing complete!")
    print(f"Latin fonts: {len(index['latin'])}")
    print(f"Cyrillic fonts: {len(index['cyrillic'])}")
    print(f"Supporting both: {len(index['both'])}")

if __name__ == "__main__":
    FONT_ROOTS = [
        r"D:\applications\CyrillicFontTransfer\All fonts from Office 365 [v4.37 from 2023-10-10]",
        r"D:\applications\CyrillicFontTransfer\Fonts CYR",
        r"D:\applications\CyrillicFontTransfer\fonts_db\CreativeMarket_vol8"
    ]
    OUTPUT = "data/fonts_index.json"
    
    # Создаем папку data если нет
    os.makedirs("data", exist_ok=True)
    
    build_index(FONT_ROOTS, OUTPUT)
