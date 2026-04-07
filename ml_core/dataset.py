import os
import json
import random
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from pathlib import Path

class FontDataset(Dataset):
    """
    Датасет для Hierarchical Font Recognition.
    Рендерит символы шрифта 'на лету' с аугментациями.
    """
    def __init__(self, index_path, char_set="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", 
                 img_size=64, num_chars_per_font=8, transform=None):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        
        # Для обучения используем шрифты с латиницей (latin + both)
        self.fonts = index["latin"] + index["both"]
        self.char_set = list(char_set)
        self.img_size = img_size
        self.num_chars_per_font = num_chars_per_font
        self.transform = transform or transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])

    def __len__(self):
        return len(self.fonts)

    def render_char(self, font_path, char):
        """Рендерит один символ пропорционально вписанным в квадрат."""
        try:
            # 1. Загружаем шрифт большим размером для точности замеров
            test_size = 100
            fnt = ImageFont.truetype(font_path, test_size)
            
            # 2. Замеряем пропорции через textbbox
            dummy = Image.new("L", (1, 1))
            draw_dummy = ImageDraw.Draw(dummy)
            left, top, right, bottom = draw_dummy.textbbox((0, 0), char, font=fnt)
            w, h = right - left, bottom - top
            
            # 3. Рассчитываем итоговый размер шрифта, чтобы вписать в img_size с маржой 30%
            # (оставляем место для аугментаций)
            target_char_size = self.img_size * 0.7
            scale = target_char_size / max(w, h)
            actual_size = int(test_size * scale)
            
            fnt = ImageFont.truetype(font_path, actual_size)
            
            # 4. Рендерим на финальный холст 64x64
            img = Image.new("L", (self.img_size, self.img_size), 255)
            draw = ImageDraw.Draw(img)
            
            # Повторный замер для центрирования
            left, top, right, bottom = draw.textbbox((0, 0), char, font=fnt)
            w, h = right - left, bottom - top
            
            # Центрируем с небольшим случайным смещением ( jitter )
            offset_x = (self.img_size - w) // 2 - left + random.randint(-2, 2)
            offset_y = (self.img_size - h) // 2 - top + random.randint(-2, 2)
            
            draw.text((offset_x, offset_y), char, font=fnt, fill=0)
            return img
        except Exception as e:
            return Image.new("L", (self.img_size, self.img_size), 255)


    def apply_aug(self, img):
        """Специфические типографические аугментации."""
        # 1. Случайный наклон (Slant)
        if random.random() > 0.5:
            m = random.uniform(-0.3, 0.3)
            img = img.transform(img.size, Image.AFFINE, (1, m, 0, 0, 1, 0))
        
        # 2. Небольшое размытие (Blur)
        if random.random() > 0.7:
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.1, 0.8)))
            
        return img

    def __getitem__(self, idx):
        font_info = self.fonts[idx]
        font_path = font_info["path"]
        
        # Выбираем случайный набор символов для этого шрифта
        chars = random.sample(self.char_set, self.num_chars_per_font)
        
        char_tensors = []
        for char in chars:
            img = self.render_char(font_path, char)
            img = self.apply_aug(img)
            tensor = self.transform(img)
            char_tensors.append(tensor)
            
        # Возвращаем стек тензоров [N, 1, H, W] и индекс шрифта
        return torch.stack(char_tensors), idx

def save_sample_batch(dataset, output_dir="temp/samples"):
    """Сохраняет примеры из датасета для визуальной проверки."""
    os.makedirs(output_dir, exist_ok=True)
    imgs_tensor, font_idx = dataset[random.randint(0, len(dataset)-1)]
    
    # Склеиваем символы одного шрифта в одну линию
    combined = Image.new("L", (dataset.img_size * dataset.num_chars_per_font, dataset.img_size))
    for i in range(dataset.num_chars_per_font):
        # Inverse transform to PIL
        img_arr = (imgs_tensor[i][0].numpy() * 0.5 + 0.5) * 255
        img = Image.fromarray(img_arr.astype(np.uint8))
        combined.paste(img, (i * dataset.img_size, 0))
        
    combined.save(os.path.join(output_dir, f"font_{font_idx}.png"))
    print(f"Sample saved to {output_dir}")

if __name__ == "__main__":
    # Тестовый запуск
    ds = FontDataset("data/fonts_index.json")
    print(f"Dataset initialized with {len(ds)} fonts.")
    save_sample_batch(ds)
    
    # Проверка DataLoader
    loader = DataLoader(ds, batch_size=4, shuffle=True)
    batch_imgs, batch_labels = next(iter(loader))
    print(f"Batch shape: {batch_imgs.shape}") # Expect [Batch, NumChars, 1, 64, 64]
