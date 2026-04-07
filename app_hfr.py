import gradio as gr
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
from backend.inference_engine import InferenceEngine


# Инициализируем инференс
engine = InferenceEngine()

def pil_to_base64(img):
    """Конвертирует PIL изображение в base64 строку для HTML."""
    if img is None: return ""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_results_html(matches, start_idx, end_idx, preview_text, letter_spacing=0, word_spacing=20):
    """Генерирует HTML для среза найденных шрифтов."""
    html = ""
    for i in range(start_idx, min(end_idx, len(matches))):
        m = matches[i]
        # Расчет процента сходства
        score_pct = max(0, min(100, 100 * (1 - m['score'] / 1.5))) 
        
        preview_img = engine.get_font_preview(m['path'], text=preview_text, letter_spacing=letter_spacing, word_spacing=word_spacing)
        preview_base64 = pil_to_base64(preview_img)
        
        # Получаем абсолютный путь для скачивания
        abs_path = os.path.abspath(m['path']).replace('\\', '/')
        
        html += f"""
        <div style='background: #1e1e2e; padding: 20px; border-radius: 16px; border: 1px solid #45475a; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 20px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                <span style='font-size: 1.1em; font-weight: bold; color: #cba6f7;'>#{i+1} {m['font_name']}</span>
                <div style='background: #313244; padding: 4px 12px; border-radius: 20px;'>
                    <span style='color: #a6e3a1; font-weight: bold;'>{score_pct:.1f}% сходство</span>
                </div>
            </div>
            
            <div style='background: white; border-radius: 8px; padding: 10px; margin: 10px 0; overflow: hidden; text-align: center;'>
                <img src='data:image/png;base64,{preview_base64}' style='max-width: 100%; height: auto; display: inline-block;' />
            </div>
            
            <div style='display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #313244; padding-top: 10px; margin-top: 10px;'>
                <div style='font-size: 0.85em; color: #9399b2; overflow: hidden; text-overflow: ellipsis;'>
                    {m['path']}
                </div>
                <a href='/file={abs_path}' download style='display: inline-block; background: #cba6f7; color: #11111b; padding: 6px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.9em; flex-shrink: 0; margin-left: 10px;'>Скачать шрифт</a>
            </div>
        </div>
        """
    return html


def process_image(img_path, preview_text, letter_spacing, word_spacing):
    """Первичный поиск (ТОП-50)."""
    if img_path is None:
        return None, "Пожалуйста, загрузите изображение или сделайте снимок.", [], 0
    
    if not preview_text:
        preview_text = "HFR Recognition"
    
    char_images, matches = engine.recognize_font(img_path, top_k=50)
    
    if char_images is None:
        return None, "Символы не найдены. Попробуйте другой ракурс.", [], 0
    
    html = get_results_html(matches, 0, 5, preview_text, letter_spacing, word_spacing)
    return char_images, html, matches, 5

def show_more(matches, current_count, preview_text, letter_spacing, word_spacing):
    """Подгрузка следующих 5 результатов без пересчета модели."""
    if not matches:
        return "", 0, gr.update(visible=False)
    
    new_count = current_count + 5
    html = get_results_html(matches, 0, new_count, preview_text, letter_spacing, word_spacing)
    
    btn_visible = new_count < len(matches)
    return html, new_count, gr.update(visible=btn_visible)

def update_previews(matches, current_count, preview_text, letter_spacing, word_spacing):
    """Обновляет превью 'на лету' при изменении ползунков."""
    if not matches:
        return gr.update()
    html = get_results_html(matches, 0, current_count, preview_text, letter_spacing, word_spacing)
    return html


# Кастомный CSS для закрепленного макета и скрытия подписей
css = """
div[data-testid="block-label"] {
    opacity: 0;
    transition: opacity 0.4s ease-in-out;
    pointer-events: none;
}
div:hover > div[data-testid="block-label"] {
    opacity: 1;
}
#show_more_btn {
    background: #45475a !important;
    border: 1px solid #585b70 !important;
    margin-top: 10px;
}
#main_container {
    align-items: flex-start !important;
}
#left_col {
    position: sticky;
    top: 20px;
    height: 95vh;
    overflow-y: auto;
    padding-right: 10px;
}
#right_col {
    height: 95vh;
    overflow-y: auto;
    padding-right: 10px;
}
/* Скроллбары */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-thumb {
    background: #585b70; 
    border-radius: 10px;
}
"""

with gr.Blocks(theme=gr.themes.Soft(primary_hue="purple", secondary_hue="indigo"), css=css, title="HFR - Cyrillic Font Finder") as demo:
    # Состояния для пагинации
    matches_state = gr.State([])
    count_state = gr.State(0)

    gr.Markdown("""
    # Hierarchical Font Recognition (HFR)
    ### Найдите кириллический аналог по латинскому стилю. Теперь с кастомным превью!
    """)
    
    with gr.Row(elem_id="main_container"):
        with gr.Column(scale=1, elem_id="left_col"):
            gr.Markdown("#### Загрузите скриншот латиницы (темный текст на светлом)")
            input_img = gr.Image(type="filepath", sources=["upload", "webcam", "clipboard"], show_label=False)
            
            preview_input = gr.Textbox(label="Текст для демонстрации результата", placeholder="Например: Привет, мир!", value="АБВГДЕabc")
            btn = gr.Button("Найти аналоги", variant="primary", size="lg")
            
            gr.Markdown("#### Сегментация (проверка захвата)")
            gallery = gr.Gallery(show_label=False, columns=8, rows=1, height="auto", object_fit="contain")
            
            with gr.Row():
                letter_spacing_slider = gr.Slider(minimum=-20, maximum=50, value=0, step=1, label="Расстояние между букв")
                word_spacing_slider = gr.Slider(minimum=0, maximum=100, value=20, step=1, label="Расстояние между слов")
            
        with gr.Column(scale=1, elem_id="right_col"):
            gr.Markdown("#### Найденные кириллические соответствия")

            results_box = gr.HTML("<div style='color: #7f849c; text-align: center; padding: 50px;'>Загрузите изображение и нажмите кнопку 'Найти', чтобы увидеть результаты.</div>")
            show_more_btn = gr.Button("Показать еще 5 вариантов", visible=False, elem_id="show_more_btn")
            
    # Логика работы
    btn.click(
        fn=process_image, 
        inputs=[input_img, preview_input, letter_spacing_slider, word_spacing_slider], 
        outputs=[gallery, results_box, matches_state, count_state]
    ).then(
        fn=lambda: gr.update(visible=True), 
        outputs=[show_more_btn]
    )

    show_more_btn.click(
        fn=show_more,
        inputs=[matches_state, count_state, preview_input, letter_spacing_slider, word_spacing_slider],
        outputs=[results_box, count_state, show_more_btn]
    )
    
    # Динамическое обновление при движении слайдеров
    letter_spacing_slider.change(
        fn=update_previews,
        inputs=[matches_state, count_state, preview_input, letter_spacing_slider, word_spacing_slider],
        outputs=[results_box]
    )
    word_spacing_slider.change(
        fn=update_previews,
        inputs=[matches_state, count_state, preview_input, letter_spacing_slider, word_spacing_slider],
        outputs=[results_box]
    )
    preview_input.change(
        fn=update_previews,
        inputs=[matches_state, count_state, preview_input, letter_spacing_slider, word_spacing_slider],
        outputs=[results_box]
    )


if __name__ == "__main__":
    import os
    # Получаем абсолютный путь к папке проекта
    project_dir = os.path.abspath(".")
    
    # Разрешаем Gradio отдавать на скачивание файлы ТОЛЬКО из папки нашего проекта
    # Добавлен параметр share=True для публичной ссылки через сервера Gradio
    demo.launch(server_port=7860, show_error=True, share=True, allowed_paths=[project_dir])
