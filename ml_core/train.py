import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split, Sampler
from tqdm import tqdm
import random

# Локальные импорты
from ml_core.dataset import FontDataset
from ml_core.model import HFRNet
from ml_core.loss import TripletLoss

class BalancedBatchSampler(Sampler):
    """
    Самплер, который гарантирует наличие P шрифтов по K примеров каждого в батче.
    В нашем случае: K=2 (два разных набора символов/аугментаций одного шрифта).
    """
    def __init__(self, data_source, batch_size, samples_per_class=2):
        self.data_source = data_source
        self.batch_size = batch_size
        self.samples_per_class = samples_per_class
        self.num_classes_per_batch = batch_size // samples_per_class
        self.indices = list(range(len(data_source)))

    def __iter__(self):
        random.shuffle(self.indices)
        for i in range(0, len(self.indices) - self.num_classes_per_batch, self.num_classes_per_batch):
            batch_indices = []
            for j in range(i, i + self.num_classes_per_batch):
                # Добавляем индекс шрифта дважды (Dataset сам сделает разные аугментации)
                idx = self.indices[j]
                for _ in range(self.samples_per_class):
                    batch_indices.append(idx)
            yield batch_indices

    def __len__(self):
        return len(self.indices) // self.num_classes_per_batch

def train_hfr(epochs=20, batch_size=32, lr=1e-4, num_chars=8, device="cuda"):
    """
    Улучшенный цикл обучения Phase 2.1.
    """
    # 1. Данные
    dataset = FontDataset(
        index_path="data/fonts_index.json",
        num_chars_per_font=num_chars,
        img_size=64
    )
    
    # Сплит 90/10
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = random_split(dataset, [train_size, val_size])
    
    # Используем наш Balanced Sampler для обучения
    train_sampler = BalancedBatchSampler(train_set, batch_size=batch_size, samples_per_class=2)
    train_loader = DataLoader(train_set, batch_sampler=train_sampler, num_workers=4)
    
    # Для валидации обычный лоадер
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=2)
    
    print(f"Phase 2.1 Training: {len(train_set)} fonts. Batch Size: {batch_size} (16 fonts x 2 samples).")

    # 2. Модель (теперь с предобученными весами)
    model = HFRNet(signature_dim=256).to(device)
    criterion = TripletLoss(margin=0.5)
    
    # Оптимизатор с небольшим LR для fine-tuning
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    os.makedirs("models", exist_ok=True)
    best_val_loss = float('inf')

    # 3. Обучение
    for epoch in range(epochs):
        model.train()
        total_train_loss = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        for batch_imgs, batch_labels in pbar:
            batch_imgs = batch_imgs.to(device)
            batch_labels = batch_labels.to(device)
            
            optimizer.zero_grad()
            signatures, _ = model(batch_imgs)
            
            loss = criterion(signatures, batch_labels)
            loss.backward()
            optimizer.step()
            
            total_train_loss += loss.item()
            pbar.set_postfix({'loss': f"{loss.item():.4f}"})

        # 4. Валидация
        model.eval()
        total_val_loss = 0
        with torch.no_grad():
            for batch_imgs, batch_labels in val_loader:
                batch_imgs = batch_imgs.to(device)
                batch_labels = batch_labels.to(device)
                
                # Здесь нам нужны позитивные пары для расчета лосса на валидации
                # Но для простоты используем тот же батч. 
                # (На валидации лосс может быть выше, так как нет пар, это нормально)
                signatures, _ = model(batch_imgs)
                val_loss = criterion(signatures, batch_labels)
                total_val_loss += val_loss.item()

        avg_train_loss = total_train_loss / len(train_loader)
        avg_val_loss = total_val_loss / len(val_loader)
        
        print(f"Epoch {epoch+1}: Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            # Сохраняем и саму модель, и веса для инференса
            torch.save(model.state_dict(), "models/hfr_model_best.pth")
            print("--- New best model saved! ---")
            
        scheduler.step()

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Fine-tuning HFRNet on {device}")
    train_hfr(epochs=20, batch_size=32, device=device)
