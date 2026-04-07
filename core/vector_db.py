"""
Векторная база данных шрифтов на основе ChromaDB.
"""

import os
from typing import Optional, Any
import chromadb
from pathlib import Path

class FontVectorDB:
    """
    Класс для сохранения и косинусного поиска стилевых эмбеддингов шрифтов.
    """

    def __init__(self, persist_dir: str = "fonts_db/chroma", collection_name: str = "cyrillic_fonts"):
        # Создаем директорию, если не существует
        os.makedirs(persist_dir, exist_ok=True)
        
        # Подключение к локальной БД
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # get_or_create работает по принципу "получить, если есть, иначе создать"
        # Используем cosine сходство по умолчанию (для CLIP эмбеддингов)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_font(self, font_name: str, file_path: str, embedding: list[float]) -> None:
        """Помещает эмбеддинг и путь .ttf файла в БД. Обновляет, если такой шрифт уже есть."""
        self.collection.upsert(
            ids=[font_name],
            embeddings=[embedding],
            metadatas=[{"file_path": str(Path(file_path).absolute())}]
        )

    def is_font_exists(self, font_name: str) -> bool:
        """Проверяет, есть ли уже такой шрифт в базе."""
        results = self.collection.get(ids=[font_name])
        return len(results['ids']) > 0

    def count(self) -> int:
        """Возвращает количество проиндексированных шрифтов."""
        return self.collection.count()

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """
        Ищет top_k наиболее похожих шрифтов по косинусному расстоянию.
        Выдаёт список словарей [{'id': ..., 'file_path': ..., 'distance': ...}, ...]
        """
        if self.count() == 0:
            return []
            
        # Реальная k не может быть больше количества записей
        k = min(top_k, self.count())

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["metadatas", "distances"]
        )

        output = []
        if not results['ids']:
            return output

        # Парсинг ответа ChromaDB (отдаются списки списков из-за возможного batch-запроса)
        for i in range(len(results['ids'][0])):
            record = {
                "id": results['ids'][0][i],
                "file_path": results['metadatas'][0][i].get("file_path", ""),
                
                # ChromaDB cosine distance: 0.0 - точное совпадение, 1.0 - ортогональны, 2.0 - противоположны.
                # Поэтому similarity (сходство) = 1.0 - distance.
                "similarity": max(0.0, 1.0 - results['distances'][0][i])
            }
            output.append(record)

        return output
