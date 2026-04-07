import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

class FontBackbone(nn.Module):
    """
    Экстрактор признаков для одного символа на базе EfficientNet-B0.
    Использует предобученные веса ImageNet для детекции базовых черт.
    """
    def __init__(self, embedding_dim=512):
        super().__init__()
        # Загружаем предобученные веса (IMAGENET1K_V1)
        self.model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        
        # Меняем входной слой на 1 канал
        # Сохраняем веса одного из каналов для инициализации ч/б входа
        old_conv = self.model.features[0][0]
        new_conv = nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1, bias=False)
        with torch.no_grad():
            new_conv.weight[:] = old_conv.weight.sum(dim=1, keepdim=True)
        self.model.features[0][0] = new_conv
        
        # Удаляем финальный классификатор
        self.feature_dim = self.model.classifier[1].in_features
        self.model.classifier = nn.Identity()
        
        # Проекционный слой в латентное пространство стиля
        self.projection = nn.Sequential(
            nn.Linear(self.feature_dim, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
            nn.ReLU()
        )

    def forward(self, x):
        # x shape: [B, 1, 64, 64]
        features = self.model(x)
        return self.projection(features)

class AttentionAggregator(nn.Module):
    """Механизм внимания для объединения эмбеддингов нескольких символов."""
    def __init__(self, embedding_dim=512):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(embedding_dim, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )

    def forward(self, x):
        weights = self.attention(x) # [B, N, 1]
        weights = torch.softmax(weights, dim=1)
        font_vector = torch.sum(x * weights, dim=1) # [B, EmbeddingDim]
        return font_vector, weights

class HFRNet(nn.Module):
    """Финальная сеть с L2-нормализацией на выходе."""
    def __init__(self, signature_dim=256):
        super().__init__()
        self.backbone = FontBackbone(embedding_dim=512)
        self.aggregator = AttentionAggregator(embedding_dim=512)
        
        self.fc = nn.Sequential(
            nn.Linear(512, signature_dim),
            nn.LayerNorm(signature_dim)
        )

    def forward(self, x):
        b, n, c, h, w = x.shape
        x_flat = x.view(b * n, c, h, w)
        char_features = self.backbone(x_flat)
        char_features = char_features.view(b, n, -1)
        
        font_sig, weights = self.aggregator(char_features)
        out = self.fc(font_sig)
        
        # КРИТИЧЕСКИ ВАЖНО: L2-нормализация для Triplet Loss и поиска
        out = F.normalize(out, p=2, dim=1)
        
        return out, weights
