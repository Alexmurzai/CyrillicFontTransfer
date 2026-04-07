import os
import hashlib
import shutil
from pathlib import Path
from tqdm import tqdm

def get_file_hash(file_path):
    """Calculates MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def add_new_fonts(source_dir, target_dir):
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        print(f"[X] Error: Source directory {source_dir} not found.")
        return

    if not target_path.exists():
        target_path.mkdir(parents=True)

    print(f"[*] Scanning existing fonts in {target_path}...")
    existing_hashes = set()
    # Recursive search in all fonts_db folder
    project_root = target_path.parent
    fonts_db_path = project_root / "fonts_db"
    
    for f in fonts_db_path.glob("**/*"):
        if f.suffix.lower() in ['.ttf', '.otf']:
            existing_hashes.add(get_file_hash(f))
            
    print(f"[*] Found {len(existing_hashes)} unique existing fonts.")

    print(f"[*] Finding new fonts in {source_path}...")
    new_files = list(source_path.glob("**/*.ttf")) + list(source_path.glob("**/*.otf"))
    print(f"[*] Found {len(new_files)} candidate fonts in source.")

    added_count = 0
    duplicate_count = 0
    
    for f in tqdm(new_files, desc="Processing fonts"):
        f_hash = get_file_hash(f)
        if f_hash in existing_hashes:
            duplicate_count += 1
            continue
            
        # Unique font, copy it
        target_file = target_path / f.name
        # Handle filename collisions (different hashes, same name)
        if target_file.exists():
            target_file = target_path / f"{f.stem}_{f_hash[:8]}{f.suffix}"
            
        shutil.copy2(f, target_file)
        existing_hashes.add(f_hash)
        added_count += 1

    print("\n" + "="*50)
    print(f"[+] Task Complete!")
    print(f"[*] New unique fonts added: {added_count}")
    print(f"[*] Duplicates skipped: {duplicate_count}")
    print("="*50)

if __name__ == "__main__":
    SOURCE = r"D:\Install\CreativeMarket - Set of multilingual fonts with Cyrillic vol.8"
    TARGET = r"D:\applications\CyrillicFontTransfer\fonts_db\CreativeMarket_vol8"
    add_new_fonts(SOURCE, TARGET)
