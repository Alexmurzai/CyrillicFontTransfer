import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "hfr_stats.db"))

def get_connection():
    """Возвращает соединение с SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных и создание таблиц, если они не существуют."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        # Таблица посещений
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip TEXT,
                user_agent TEXT
            )
        """)
        # Таблица распознаваний
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recognitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                top_match TEXT,
                ip TEXT
            )
        """)
        # Таблица скачиваний
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                font_id INTEGER,
                font_name TEXT,
                ip TEXT
            )
        """)
        conn.commit()
    print(f"[OK] HFR Stats database initialized at: {DB_PATH}")

def log_visit(ip: str, user_agent: str) -> bool:
    """
    Записывает посещение в базу данных, если от этого IP не было визитов за последние 30 минут.
    Возвращает True, если визит был записан, иначе False.
    """
    try:
        with get_connection() as conn:
            # Проверяем последнее посещение с этого IP за последние 30 минут
            cursor = conn.cursor()
            time_limit = (datetime.utcnow() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "SELECT id FROM visits WHERE ip = ? AND timestamp > ? ORDER BY timestamp DESC LIMIT 1",
                (ip, time_limit)
            )
            recent_visit = cursor.fetchone()
            
            if recent_visit is None:
                conn.execute(
                    "INSERT INTO visits (ip, user_agent) VALUES (?, ?)",
                    (ip, user_agent)
                )
                conn.commit()
                return True
    except Exception as e:
        print(f"[ERR] Failed to log visit: {e}")
    return False

def log_recognition(category: str, top_match: str, ip: str):
    """Записывает событие подбора шрифта."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO recognitions (category, top_match, ip) VALUES (?, ?, ?)",
                (category, top_match, ip)
            )
            conn.commit()
    except Exception as e:
        print(f"[ERR] Failed to log recognition: {e}")

def log_download(font_id: int, font_name: str, ip: str):
    """Записывает событие скачивания шрифта."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO downloads (font_id, font_name, ip) VALUES (?, ?, ?)",
                (font_id, font_name, ip)
            )
            conn.commit()
    except Exception as e:
        print(f"[ERR] Failed to log download: {e}")

def get_stats_summary() -> dict:
    """Агрегирует всю статистику для дашборда и API."""
    stats = {
        "totals": {"visits": 0, "recognitions": 0, "downloads": 0},
        "top_matches": [],
        "top_downloads": [],
        "categories": {},
        "activity_daily": []
    }
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Всего событий
            cursor.execute("SELECT COUNT(*) FROM visits")
            stats["totals"]["visits"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM recognitions")
            stats["totals"]["recognitions"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM downloads")
            stats["totals"]["downloads"] = cursor.fetchone()[0]
            
            # 2. Популярные совпадения
            cursor.execute("""
                SELECT top_match, COUNT(*) as count 
                FROM recognitions 
                WHERE top_match IS NOT NULL AND top_match != ''
                GROUP BY top_match 
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats["top_matches"] = [dict(row) for row in cursor.fetchall()]
            
            # 3. Популярные скачивания
            cursor.execute("""
                SELECT font_name, COUNT(*) as count 
                FROM downloads 
                GROUP BY font_name 
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats["top_downloads"] = [dict(row) for row in cursor.fetchall()]
            
            # 4. Распределение по категориям
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM recognitions 
                GROUP BY category
            """)
            stats["categories"] = {row["category"]: row["count"] for row in cursor.fetchall()}
            
            # 5. Активность по дням за последние 14 дней
            cursor.execute("""
                WITH RECURSIVE dates(date) AS (
                    SELECT date('now', '-13 days')
                    UNION ALL
                    SELECT date(date, '+1 day') FROM dates WHERE date < date('now')
                )
                SELECT 
                    dates.date,
                    COALESCE(v.cnt, 0) as visits,
                    COALESCE(r.cnt, 0) as recognitions,
                    COALESCE(d.cnt, 0) as downloads
                FROM dates
                LEFT JOIN (
                    SELECT date(timestamp) as dt, COUNT(*) as cnt 
                    FROM visits GROUP BY date(timestamp)
                ) v ON dates.date = v.dt
                LEFT JOIN (
                    SELECT date(timestamp) as dt, COUNT(*) as cnt 
                    FROM recognitions GROUP BY date(timestamp)
                ) r ON dates.date = r.dt
                LEFT JOIN (
                    SELECT date(timestamp) as dt, COUNT(*) as cnt 
                    FROM downloads GROUP BY date(timestamp)
                ) d ON dates.date = d.dt
                ORDER BY dates.date ASC
            """)
            stats["activity_daily"] = [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        print(f"[ERR] Failed to fetch stats summary: {e}")
    return stats

def render_stats_html(stats: dict) -> str:
    """Генерирует премиум HTML/CSS дашборд на основе собранной статистики."""
    # Вычисляем максимальное значение для масштабирования графиков
    max_val = max(
        [max(d["visits"], d["recognitions"], d["downloads"]) for d in stats["activity_daily"]] + [1]
    )
    
    # Генерация колонок диаграммы
    chart_cols_html = ""
    for d in stats["activity_daily"]:
        # Преобразуем YYYY-MM-DD в более читаемый вид DD.MM
        try:
            date_obj = datetime.strptime(d["date"], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m")
        except:
            formatted_date = d["date"]
            
        v_h = max(3, int((d["visits"] / max_val) * 100))
        r_h = max(3, int((d["recognitions"] / max_val) * 100))
        d_h = max(3, int((d["downloads"] / max_val) * 100))
        
        chart_cols_html += f"""
        <div class="chart-col">
            <div class="bars-container">
                <div class="bar bar-visits" style="height: {v_h}%;" title="Посещения: {d['visits']}"></div>
                <div class="bar bar-matches" style="height: {r_h}%;" title="Подборы: {d['recognitions']}"></div>
                <div class="bar bar-downloads" style="height: {d_h}%;" title="Скачивания: {d['downloads']}"></div>
            </div>
            <div class="col-label">{formatted_date}</div>
        </div>
        """

    # Генерация строк популярных подборов
    matches_rows = ""
    if stats["top_matches"]:
        for i, item in enumerate(stats["top_matches"]):
            matches_rows += f"""
            <tr>
                <td><span class="rank-badge">#{i+1}</span></td>
                <td class="font-name">{item['top_match']}</td>
                <td class="font-count">{item['count']} подборов</td>
            </tr>
            """
    else:
        matches_rows = "<tr><td colspan='3' class='empty-table'>Статистика подборов пуста</td></tr>"

    # Генерация строк популярных скачиваний
    downloads_rows = ""
    if stats["top_downloads"]:
        for i, item in enumerate(stats["top_downloads"]):
            downloads_rows += f"""
            <tr>
                <td><span class="rank-badge rank-badge--alt">#{i+1}</span></td>
                <td class="font-name">{item['font_name']}</td>
                <td class="font-count">{item['count']} скачиваний</td>
            </tr>
            """
    else:
        downloads_rows = "<tr><td colspan='3' class='empty-table'>Статистика скачиваний пуста</td></tr>"

    # Распределение по категориям
    cat_items = ""
    for cat, count in stats["categories"].items():
        cat_items += f"""
        <div class="category-chip">
            <span class="category-name">{cat.upper()}</span>
            <span class="category-val">{count}</span>
        </div>
        """
    if not cat_items:
        cat_items = "<div class='empty-table' style='width: 100%; text-align: center;'>Нет данных</div>"

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HFR — Панель статистики</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #11111b;
            --card-bg: #1e1e2e;
            --border-color: #313244;
            --text-color: #cdd6f4;
            --text-muted: #a6adc8;
            --accent-purple: #cba6f7;
            --accent-green: #a6e3a1;
            --accent-pink: #f38ba8;
            --accent-blue: #89b4fa;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', 'Segoe UI', sans-serif;
        }}
        
        body {{
            background: var(--bg-color);
            color: var(--text-color);
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }}
        
        .dashboard {{
            width: 100%;
            max-width: 1200px;
            display: flex;
            flex-direction: column;
            gap: 30px;
        }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            color: var(--text-muted);
            margin-top: 5px;
            font-size: 0.95rem;
        }}
        
        .btn-back {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 10px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }}
        
        .btn-back:hover {{
            background: var(--border-color);
            border-color: var(--accent-purple);
        }}
        
        /* Карточки тоталов */
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
        }}
        
        .card-visits::before {{ background: var(--accent-green); }}
        .card-recognitions::before {{ background: var(--accent-purple); }}
        .card-downloads::before {{ background: var(--accent-pink); }}
        
        .card-title {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .card-value {{
            font-size: 3rem;
            font-weight: 700;
            margin-top: 10px;
            line-height: 1;
        }}
        
        .card-visits .card-value {{ color: var(--accent-green); }}
        .card-recognitions .card-value {{ color: var(--accent-purple); }}
        .card-downloads .card-value {{ color: var(--accent-pink); }}
        
        /* График */
        .chart-card {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .chart-legend {{
            display: flex;
            gap: 20px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        
        .legend-visits {{ background: var(--accent-green); }}
        .legend-matches {{ background: var(--accent-purple); }}
        .legend-downloads {{ background: var(--accent-pink); }}
        
        .chart-container {{
            height: 250px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-top: 20px;
            border-bottom: 2px solid var(--border-color);
            gap: 15px;
        }}
        
        .chart-col {{
            flex: 1;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            gap: 8px;
        }}
        
        .bars-container {{
            width: 100%;
            height: calc(100% - 25px);
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 4px;
        }}
        
        .bar {{
            width: 8px;
            border-radius: 4px 4px 0 0;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .bar:hover {{
            filter: brightness(1.2);
            box-shadow: 0 0 10px rgba(255,255,255,0.1);
        }}
        
        .bar-visits {{ background: var(--accent-green); }}
        .bar-matches {{ background: var(--accent-purple); }}
        .bar-downloads {{ background: var(--accent-pink); }}
        
        .col-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 600;
        }}
        
        /* Сетка таблиц */
        .tables-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
        }}
        
        .table-title {{
            font-size: 1.15rem;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
            margin-bottom: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        tr {{
            border-bottom: 1px solid rgba(49, 50, 68, 0.5);
            transition: background 0.3s ease;
        }}
        
        tr:hover {{
            background: rgba(255,255,255,0.02);
        }}
        
        td {{
            padding: 12px 8px;
            font-size: 0.95rem;
        }}
        
        .rank-badge {{
            display: inline-block;
            width: 28px;
            height: 28px;
            line-height: 28px;
            text-align: center;
            background: rgba(203, 166, 247, 0.1);
            color: var(--accent-purple);
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
        }}
        
        .rank-badge--alt {{
            background: rgba(243, 139, 168, 0.1);
            color: var(--accent-pink);
        }}
        
        .font-name {{
            font-weight: 600;
        }}
        
        .font-count {{
            text-align: right;
            color: var(--text-muted);
            font-weight: 600;
        }}
        
        .empty-table {{
            color: var(--text-muted);
            text-align: center;
            padding: 30px;
            font-style: italic;
        }}
        
        /* Категории */
        .categories-card {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .category-chips {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }}
        
        .category-chip {{
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border-color);
            padding: 10px 18px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .category-name {{
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 1px;
            color: var(--accent-blue);
        }}
        
        .category-val {{
            font-size: 1.1rem;
            font-weight: 700;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <header>
            <div>
                <h1>HFR — Аналитика и Статистика</h1>
                <div class="subtitle">Локальные данные использования подбора и скачиваний</div>
            </div>
            <a href="/" class="btn-back">← Назад к сервису</a>
        </header>
        
        <div class="summary-cards">
            <div class="card card-visits">
                <div class="card-title">Уникальные визиты (30м лимит)</div>
                <div class="card-value">{stats['totals']['visits']}</div>
            </div>
            <div class="card card-recognitions">
                <div class="card-title">Запущенные поиски</div>
                <div class="card-value">{stats['totals']['recognitions']}</div>
            </div>
            <div class="card card-downloads">
                <div class="card-title">Загрузки шрифтов</div>
                <div class="card-value">{stats['totals']['downloads']}</div>
            </div>
        </div>
        
        <div class="card chart-card">
            <div class="table-title" style="border: none; margin: 0; padding: 0;">
                <span>Активность за последние 14 дней</span>
            </div>
            <div class="chart-legend">
                <div class="legend-item"><div class="legend-dot legend-visits"></div><span>Визиты</span></div>
                <div class="legend-item"><div class="legend-dot legend-matches"></div><span>Подборы</span></div>
                <div class="legend-item"><div class="legend-dot legend-downloads"></div><span>Скачивания</span></div>
            </div>
            <div class="chart-container">
                {chart_cols_html}
            </div>
        </div>
        
        <div class="card categories-card">
            <div class="table-title" style="border: none; margin: 0; padding: 0;">
                <span>Распределение поисков по стилям</span>
            </div>
            <div class="category-chips">
                {cat_items}
            </div>
        </div>
        
        <div class="tables-grid">
            <div class="card">
                <div class="table-title">ТОП-10 Популярных совпадений</div>
                <table>
                    <tbody>
                        {matches_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="card">
                <div class="table-title">ТОП-10 Скачиваемых шрифтов</div>
                <table>
                    <tbody>
                        {downloads_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html

