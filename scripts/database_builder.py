import os
import json
import torch
import faiss
import numpy as np
from tqdm import tqdm
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Локальные импорты
from ml_core.model import HFRNet
from ml_core.dataset import FontDataset

def build_vector_db(model_path="models/hfr_model_best.pth", index_path="data/fonts_index.json", device="cuda"):
    """
    Создает базу векторов (signatures) для всех кириллических шрифтов.
    """
    # 1. Загрузка модели
    print(f"Loading model from {model_path}...")
    model = HFRNet(signature_dim=256).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # 2. Подготовка датасета (только для кириллицы)
    with open(index_path, "r", encoding="utf-8") as f:
        full_index = json.load(f)
    
    # Мы индексируем только те шрифты, которые содержат кириллицу (both + cyrillic)
    cyr_fonts = full_index["both"] + full_index["cyrillic"]
    print(f"Total Cyrillic fonts for indexing: {len(cyr_fonts)}")

    dataset = FontDataset(index_path=index_path)
    
    # 3. Индексация
    signature_dim = 256
    faiss_index = faiss.IndexFlatL2(signature_dim)
    metadata = []
    
    all_signatures = []

    print("Generating Font Signatures...")
    with torch.no_grad():
        for i, font_info in enumerate(tqdm(cyr_fonts)):
            # Для каждого шрифта рендерим набор символов
            # Используем те же символы, что и при обучении (латинские для распознавания стиля)
            # Это ключевой момент: мы распознаем СТИЛЬ через латиницу, даже для кириллических шрифтов
            font_path = font_info["path"]
            
            # Рендерим 8 символов (H, O, a, g, n, s, e, p)
            chars = "HOagnsep"
            tensors = []
            for ch in chars:
                img = dataset.render_char(font_path, ch)
                tensors.append(dataset.transform(img))
            
            batch = torch.stack(tensors).unsqueeze(0).to(device) # [1, 8, 1, 64, 64]
            
            # Предсказание
            sig, _ = model(batch)
            # L2-Нормализация: делаем все векторы в базе единичной длины
            sig = torch.nn.functional.normalize(sig, p=2, dim=1)
            sig_np = sig.cpu().numpy().astype('float32')

            
            all_signatures.append(sig_np)
            metadata.append({
                "id": i,
                "name": font_info["name"],
                "path": font_info["path"]
            })

    # 4. Сохранение в FAISS
    all_signatures = np.vstack(all_signatures)
    faiss_index.add(all_signatures)
    
    os.makedirs("data", exist_ok=True)
    faiss.write_index(faiss_index, "data/font_signatures.faiss")
    
    with open("data/font_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    print(f"\nVector DB built successfully!")
    print(f"FAISS index saved to: data/font_signatures.faiss")
    print(f"Metadata saved to: data/font_metadata.json")

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    build_vector_db(device=device)
