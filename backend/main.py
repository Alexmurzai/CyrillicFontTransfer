"""
HFR — Hierarchical Font Recognition API
FastAPI backend для premium веб-интерфейса.
"""
import os
import sys
import shutil
import base64
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

# Добавляем корень проекта в path для импортов ml_core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.inference_engine import InferenceEngine
from backend.font_classifier import classify_font, classify_all_fonts
from backend.api_models import FontMatch, RecognitionResponse, HealthResponse


app = FastAPI(
    title="HFR — Hierarchical Font Recognition API",
    version="2.1.0",
    description="API для поиска кириллических аналогов латинских шрифтов"
)

# CORS — разрешаем фронтенд (Vite dev + production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "*",  # Для Cloudflare Tunnel
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Папка для временных загрузок
UPLOAD_DIR = Path("temp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Глобальные объекты
engine: InferenceEngine | None = None
font_categories: dict[int, str] = {}


@app.get("/")
def read_root():
    """Корневой роут для проверки доступности."""
    return {
        "message": "HFR API is running",
        "docs": "/docs",
        "health": "/api/health"
    }


def pil_to_base64(img) -> str:
    """Конвертирует PIL Image в data:image/png;base64,... строку."""
    if img is None:
        return ""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    b64 = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


@app.on_event("startup")
def load_engine():
    """Загрузка ML-модели и FAISS при старте."""
    global engine, font_categories
    try:
        engine = InferenceEngine(
            model_path="models/hfr_model_best.pth",
            index_path="data/font_signatures.faiss",
            meta_path="data/font_metadata.json"
        )
        # Классифицируем все шрифты при старте
        font_categories = classify_all_fonts(engine.metadata)
        
        # Статистика категорий
        from collections import Counter
        stats = Counter(font_categories.values())
        print(f"[OK] Font categories classified: {dict(stats)}")
        print(f"[OK] HFR Engine loaded. {len(engine.metadata)} fonts indexed on {engine.device}")
    except Exception as e:
        print(f"[ERR] Error loading HFR Engine: {e}")
        import traceback
        traceback.print_exc()


# ──────────────────────────────────────────────
# Эндпоинты
# ──────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Статус здоровья сервиса."""
    return HealthResponse(
        status="ok" if engine else "error",
        engine_loaded=engine is not None,
        fonts_count=len(engine.metadata) if engine else 0,
        device=engine.device if engine else "none"
    )


@app.post("/api/recognize")
async def recognize_font(
    file: UploadFile = File(...),
    top_k: int = Query(default=50, ge=1, le=200),
    preview_text: str = Query(default="АБВГДЕabc"),
    letter_spacing: int = Query(default=0, ge=-20, le=50),
    word_spacing: int = Query(default=20, ge=0, le=100),
    category: str = Query(default="all", description="Фильтр: all|serif|sans|script|display|mono"),
):
    """
    Основной эндпоинт: загрузка изображения → распознавание шрифта.
    
    Возвращает сегментированные символы и ТОП-N совпадений с превью.
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="HFR Engine не загружен")

    # Сохраняем файл временно
    file_path = UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Запускаем распознавание (топ-K × 2 для запаса под фильтрацию)
        search_k = top_k * 3 if category != "all" else top_k
        char_pil_images, matches = engine.recognize_font(str(file_path), top_k=min(search_k, len(engine.metadata)))

        if char_pil_images is None:
            raise HTTPException(status_code=422, detail="Символы не найдены на изображении. Попробуйте другое.")

        # Конвертируем сегментированные символы в base64
        char_images_b64 = [pil_to_base64(img) for img in char_pil_images]

        # Формируем результаты с превью и фильтрацией
        result_matches = []
        for m in matches:
            # Определяем категорию
            font_cat = font_categories.get(m.get("id", -1), classify_font(m["font_name"]))

            # Фильтрация по категории
            if category != "all" and font_cat != category:
                continue

            # Рендерим превью
            preview_img = engine.get_font_preview(
                m["path"],
                text=preview_text,
                letter_spacing=letter_spacing,
                word_spacing=word_spacing,
            )

            # Расчёт процента сходства
            score_pct = max(0, min(100, 100 * (1 - m["score"] / 1.5)))

            result_matches.append(FontMatch(
                id=m.get("id", 0),
                font_name=m["font_name"],
                score=m["score"],
                similarity_pct=round(score_pct, 1),
                preview_base64=pil_to_base64(preview_img),
                font_path=m["path"],
                font_category=font_cat,
            ))

            # Ограничиваем выдачу
            if len(result_matches) >= top_k:
                break

        return {
            "char_images": char_images_b64,
            "matches": [m.model_dump() for m in result_matches],
            "total": len(result_matches),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")
    finally:
        if file_path.exists():
            os.remove(file_path)


@app.get("/api/preview")
def get_preview(
    font_path: str = Query(..., description="Путь к .ttf файлу"),
    text: str = Query(default="АБВГДЕabc"),
    size: int = Query(default=64, ge=16, le=200),
    letter_spacing: int = Query(default=0, ge=-20, le=50),
    word_spacing: int = Query(default=20, ge=0, le=100),
):
    """
    Рендерит превью текста указанным шрифтом.
    Возвращает PNG-изображение.
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="HFR Engine не загружен")

    if not os.path.exists(font_path):
        raise HTTPException(status_code=404, detail=f"Шрифт не найден: {font_path}")

    img = engine.get_font_preview(
        font_path, text=text, size=size,
        letter_spacing=letter_spacing, word_spacing=word_spacing
    )

    # Возвращаем как PNG
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return Response(
        content=buffered.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@app.get("/api/font/download/{font_id}")
def download_font(font_id: int):
    """Скачивание .ttf файла по ID из метаданных."""
    if engine is None:
        raise HTTPException(status_code=503, detail="HFR Engine не загружен")

    if font_id < 0 or font_id >= len(engine.metadata):
        raise HTTPException(status_code=404, detail=f"Шрифт с ID {font_id} не найден")

    meta = engine.metadata[font_id]
    font_path = meta["path"]

    if not os.path.exists(font_path):
        raise HTTPException(status_code=404, detail=f"Файл шрифта не найден: {font_path}")

    return FileResponse(
        path=font_path,
        filename=meta["name"],
        media_type="application/x-font-ttf",
        headers={"Content-Disposition": f'attachment; filename="{meta["name"]}"'}
    )


@app.get("/api/categories")
def get_categories():
    """Возвращает статистику по категориям шрифтов."""
    if engine is None:
        raise HTTPException(status_code=503, detail="HFR Engine не загружен")

    from collections import Counter
    stats = Counter(font_categories.values())
    return {
        "categories": dict(stats),
        "total": len(font_categories)
    }


@app.get("/api/update-previews")
def update_previews(
    font_paths: str = Query(..., description="Пути к шрифтам через запятую"),
    text: str = Query(default="АБВГДЕabc"),
    letter_spacing: int = Query(default=0, ge=-20, le=50),
    word_spacing: int = Query(default=20, ge=0, le=100),
):
    """
    Batch-обновление превью для уже найденных шрифтов.
    Используется при изменении текста/spacing без перезапуска поиска.
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="HFR Engine не загружен")

    paths = [p.strip() for p in font_paths.split(",") if p.strip()]
    previews = {}

    for path in paths:
        if os.path.exists(path):
            img = engine.get_font_preview(
                path, text=text,
                letter_spacing=letter_spacing,
                word_spacing=word_spacing
            )
            previews[path] = pil_to_base64(img)
        else:
            previews[path] = ""

    return {"previews": previews}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
