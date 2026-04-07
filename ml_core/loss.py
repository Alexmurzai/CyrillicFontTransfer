import torch
import torch.nn as nn
import torch.nn.functional as F

class TripletLoss(nn.Module):
    """
    Triplet Loss для обучения качественных вложений (embeddings).
    Использует Semi-Hard Mining внутри батча.
    L = max(d(a, p) - d(a, n) + margin, 0)
    """
    def __init__(self, margin=0.5):
        super(TripletLoss, self).__init__()
        self.margin = margin

    def forward(self, embeddings, labels):
        # embeddings: [BatchSize, EmbeddingDim]
        # labels: [BatchSize] - индексы шрифтов
        
        # 1. Вычисляем матрицу попарных расстояний (L2)
        # (a-b)^2 = a^2 - 2ab + b^2
        dist_matrix = torch.cdist(embeddings, embeddings, p=2)
        
        # 2. Маска для позитивных пар (одинаковые лейблы)
        labels = labels.unsqueeze(1)
        mask_pos = (labels == labels.t()).float()
        # Исключаем диагональ (расстояние до самого себя всегда 0)
        mask_pos = mask_pos - torch.eye(mask_pos.size(0), device=mask_pos.device)
        
        # 3. Маска для негативных пар (разные лейблы)
        mask_neg = (labels != labels.t()).float()
        
        # 4. Вычисляем усредненное расстояние до позитивных пар
        # Для простоты берем максимальное расстояние до позитива (hard positive)
        pos_dist = (dist_matrix * mask_pos).max(dim=1)[0]
        
        # 5. Вычисляем минимальное расстояние до негативных пар (hard negative)
        # Чтобы нули в маске не "тянули" минимум на себя, добавим константу
        neg_dist = (dist_matrix + (1 - mask_neg) * 1e6).min(dim=1)[0]
        
        # 6. Итоговый лосс
        loss = F.relu(pos_dist - neg_dist + self.margin)
        
        return loss.mean()

def cosine_similarity_loss(embeddings, labels, margin=0.5):
    """Альтернативный лосс на основе косинусного сходства."""
    # Нормализуем эмбеддинги
    embeds = F.normalize(embeddings, p=2, dim=1)
    sim_matrix = torch.matmul(embeds, embeds.t())
    
    labels = labels.unsqueeze(1)
    mask_pos = (labels == labels.t()).float()
    mask_neg = (labels != labels.t()).float()
    
    # Мы хотим, чтобы сходство позитивных пар было близко к 1, негативных < margin
    pos_sim = (sim_matrix * mask_pos).sum() / (mask_pos.sum() + 1e-6)
    neg_sim = (sim_matrix * mask_neg).sum() / (mask_neg.sum() + 1e-6)
    
    loss = (1.0 - pos_sim) + F.relu(neg_sim - margin)
    return loss
