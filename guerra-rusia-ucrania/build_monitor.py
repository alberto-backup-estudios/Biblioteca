import os
import sys
import json
import time
import html
import re
import hashlib
from datetime import datetime, timezone
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import feedparser
import requests

# Forzar salida en UTF-8 en consola de Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "feeds_config.json")
CACHE_FILE = os.path.join(BASE_DIR, "data", "articles.json")
TRANSLATIONS_FILE = os.path.join(BASE_DIR, "translations_cache.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "index.html")

WAR_KEYWORDS = {
    "ru": [
        r"украин", r"киев", r"всу", r"сво\b", r"фронт", r"донбасс", r"покровск",
        r"курск", r"белгород", r"дрон", r"бпла", r"ракет", r"путин", r"зеленск",
        r"минобороны", r"нато", r"санкци", r"войн", r"военн", r"переговор",
        r"оружи", r"пво", r"байден", r"трамп", r"снаряд", r"обстрел", r"артиллери"
    ],
    "uk": [
        r"росі", r"рф\b", r"москв", r"фронт", r"донбас", r"покровськ", r"курськ",
        r"бєлгород", r"дрон", r"бпла", r"ракет", r"путін", r"зеленськ", r"генштаб",
        r"зсу", r"нато", r"санкці", r"війн", r"переговор", r"збро", r"ппо", r"окупант",
        r"снаряд", r"обстріл", r"бавовна", r"десант"
    ],
    "en": [
        r"ukrain", r"kyiv", r"russia", r"moscow", r"putin", r"zelensky", r"frontline",
        r"donbas", r"pokrovsk", r"kursk", r"drone", r"missile", r"nato", r"sanction",
        r"war\b", r"troops", r"defense", r"strike", r"ceasefire", r"kremlin", r"pentagon",
        r"weapons", r"air defense", r"kharkiv", r"zaporizhzhia", r"artillery"
    ]
}

CATEGORY_PATTERNS = {
    "frente": [
        r"frontline", r"frente", r"combate", r"advance", r"offensive", r"avance",
        r"pokrovsk", r"покровск", r"kursk", r"курск", r"donetsk", r"donbas",
        r"наступлен", r"штурм", r"бои\b", r"атак", r"наступ", r"бої\b", r"оборон",
        r"capture", r"toma\b", r"libera", r"territorio", r"kharkiv", r"chuguev"
    ],
    "diplomacia": [
        r"peace", r"paz\b", r"negotiat", r"negociaci", r"ceasefire", r"alto el fuego",
        r"talks", r"conversaci", r"summit", r"cumbre", r"diplomaci", r"treaty", r"tratado",
        r"переговор", r"мирн", r"соглашени", r"договор", r"перемовини", r"тиша"
    ],
    "armamento": [
        r"weapon", r"armas", r"armamento", r"missile", r"misil", r"patriot", r"f-16",
        r"himars", r"artillery", r"artillería", r"ammo", r"ammunition", r"munición",
        r"military aid", r"ayuda militar", r"tanque", r"tank", r"снаряд", r"зброя",
        r"поставка", r"оружие", r"пакет помощ"
    ],
    "drones": [
        r"drone", r"дрон", r"uav", r"бпла", r"shahed", r"шахед", r"geran", r"герань",
        r"fpv", r"air defense", r"defensa aérea", r"пво", r"ппо", r"intercept",
        r"derrib", r"сбит", r"intercepción"
    ],
    "economia": [
        r"sanction", r"sanción", r"sanciones", r"oil", r"petróleo", r"gas\b", r"refinery",
        r"refinería", r"economy", r"economía", r"ruble", r"rublo", r"export",
        r"санкци", r"нефт", r"газ\b", r"нпз", r"рубл", r"экономік", r"санкці"
    ],
    "civil": [
        r"civil", r"blackout", r"apagón", r"power grid", r"energía", r"shelter",
        r"refugio", r"evacua", r"hospital", r"energy infrastructure", r"víctima",
        r"casualt", r"мирные жители", r"инфраструктур", r"цивільн", r"знеструмлен"
    ]
}

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleantext = re.sub(r"<[^>]+>", " ", raw_html)
    cleantext = html.unescape(cleantext)
    return re.sub(r"\s+", " ", cleantext).strip()

def parse_date(entry):
    for attr in ["published_parsed", "updated_parsed", "created_parsed"]:
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()

def is_war_relevant(text, lang):
    text_lower = text.lower()
    patterns = WAR_KEYWORDS.get(lang, []) + WAR_KEYWORDS.get("en", [])
    for pat in patterns:
        if re.search(pat, text_lower):
            return True
    return False

def identify_categories(text):
    text_lower = text.lower()
    cats = []
    for cat_id, patterns in CATEGORY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                cats.append(cat_id)
                break
    return cats if cats else ["general"]

def translate_to_es(text, max_len=600):
    if not text or not text.strip():
        return ""
    text_clean = text.strip()[:max_len]
    
    # Intento 1: API clients5 (robusta y veloz)
    try:
        url = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=es&q=" + urllib.parse.quote(text_clean)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                if isinstance(data[0], list):
                    return "".join([part[0] for part in data if isinstance(part, list)])
                elif isinstance(data[0], str):
                    return data[0]
    except Exception:
        pass

    # Intento 2: MyMemory API como alternativa
    try:
        url = "https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(text_clean[:400]) + "&langpair=autodetect|es"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            t_res = data.get("responseData", {}).get("translatedText")
            if t_res and "MYMEMORY WARNING" not in t_res:
                return t_res
    except Exception:
        pass

    return text_clean

def generate_quick_summary(text_es, max_chars=180):
    """Genera un resumen ejecutivo de lectura rápida de 1 o 2 oraciones."""
    if not text_es:
        return ""
    # Dividir en oraciones
    sentences = re.split(r"(?<=[.!?])\s+", text_es.strip())
    first_sentence = sentences[0] if sentences else text_es
    if len(first_sentence) <= max_chars:
        if len(sentences) > 1 and len(first_sentence) + len(sentences[1]) < max_chars:
            return f"{first_sentence} {sentences[1]}"
        return first_sentence
    return first_sentence[:max_chars].rstrip() + "..."

def fetch_feed_articles(feed_config, war_filter_enabled=True):
    articles = []
    feed_url = feed_config["url"]
    feed_id = feed_config["id"]
    feed_name = feed_config["name"]
    perspective = feed_config["perspective"]
    language = feed_config["language"]
    bias_note = feed_config.get("bias_note", "")
    requires_filter = feed_config.get("requires_war_filter", False) and war_filter_enabled

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(feed_url, headers=headers, timeout=10)
        parsed = feedparser.parse(resp.content)

        for entry in getattr(parsed, "entries", [])[:25]:
            title = clean_html(getattr(entry, "title", "Sin título"))
            raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            summary = clean_html(raw_summary)
            if len(summary) > 400:
                summary = summary[:397] + "..."
            link = getattr(entry, "link", "#")
            pub_date = parse_date(entry)

            combined_text = f"{title} {summary}"

            # Filtrar si la fuente es generalista
            if requires_filter and not is_war_relevant(combined_text, language):
                continue

            art_id = hashlib.md5(f"{feed_id}_{title}".encode("utf-8")).hexdigest()[:12]
            categories = identify_categories(combined_text)

            articles.append({
                "id": art_id,
                "title_original": title,
                "summary_original": summary,
                "link": link,
                "source_id": feed_id,
                "source_name": feed_name,
                "perspective": perspective,
                "language": language,
                "bias_note": bias_note,
                "published": pub_date,
                "categories": categories
            })
    except Exception as e:
        print(f"[WARN] Error consultando {feed_name}: {e}")

    return articles

def generate_html(articles, perspectives, last_updated):
    """Compila el dashboard interactivo de inteligencia con estética OSINT."""
    articles_json_str = json.dumps(articles, ensure_ascii=False)
    perspectives_json_str = json.dumps(perspectives, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Monitor de la Guerra Rusia-Ucrania | Inteligencia & Fuentes Traducidas</title>
  <meta name="description" content="Dashboard en tiempo real con noticias traducidas al español de fuentes ucranianas, rusas estatales e independientes, y análisis militar internacional.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-main: #0b0f19;
      --bg-card: #131a29;
      --bg-card-hover: #192236;
      --border-color: #202c45;
      --border-accent: #2e3e60;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      
      --accent-blue: #38bdf8;
      --accent-yellow: #facc15;
      --accent-red: #f87171;
      --accent-green: #34d399;
      --accent-purple: #c084fc;
      --accent-orange: #fb923c;
      
      --ukraine-color: #38bdf8;
      --ukraine-bg: rgba(56, 189, 248, 0.12);
      --ru-ind-color: #34d399;
      --ru-ind-bg: rgba(52, 211, 153, 0.12);
      --ru-off-color: #f87171;
      --ru-off-bg: rgba(248, 113, 113, 0.12);
      --intl-color: #facc15;
      --intl-bg: rgba(250, 204, 21, 0.12);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    header {{
      background: linear-gradient(180deg, #111827 0%, #0b0f19 100%);
      border-bottom: 1px solid var(--border-color);
      padding: 1.5rem 1rem;
      position: sticky;
      top: 0;
      z-index: 100;
      backdrop-filter: blur(12px);
    }}

    .header-container {{
      max-width: 1300px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}

    .top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .brand-icon {{
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #1e293b, #0f172a);
      border: 1px solid var(--border-accent);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }}

    .brand-title {{
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #fff;
    }}

    .brand-title span {{
      color: var(--accent-blue);
    }}

    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-muted);
      background: rgba(255,255,255,0.05);
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      border: 1px solid var(--border-color);
    }}

    .status-dot {{
      width: 8px;
      height: 8px;
      background: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-green);
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.5; transform: scale(0.85); }}
    }}

    /* Panel de Resumen Ejecutivo Superior */
    .executive-brief {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
      border: 1px solid var(--border-accent);
      border-radius: 12px;
      padding: 1.25rem;
      margin: 1.5rem auto 0;
      max-width: 1300px;
      width: calc(100% - 2rem);
    }}

    .executive-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.75rem;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      padding-bottom: 0.5rem;
    }}

    .executive-title {{
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
      color: var(--accent-yellow);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .brief-columns {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
    }}

    .brief-col {{
      background: rgba(0, 0, 0, 0.25);
      border-radius: 8px;
      padding: 0.85rem;
      border-left: 3px solid transparent;
    }}

    .brief-col.ukraine {{ border-left-color: var(--ukraine-color); }}
    .brief-col.russia-ind {{ border-left-color: var(--ru-ind-color); }}
    .brief-col.russia-off {{ border-left-color: var(--ru-off-color); }}
    .brief-col.intl {{ border-left-color: var(--intl-color); }}

    .brief-col-title {{
      font-size: 0.8rem;
      font-weight: 700;
      margin-bottom: 0.4rem;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}

    .brief-col-text {{
      font-size: 0.825rem;
      color: var(--text-muted);
      line-height: 1.4;
    }}

    /* Controles de Filtrado y Búsqueda */
    .controls-container {{
      max-width: 1300px;
      margin: 1.5rem auto 0;
      padding: 0 1rem;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}

    .search-row {{
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }}

    .search-box {{
      flex: 1;
      min-width: 260px;
      position: relative;
    }}

    .search-box input {{
      width: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: #fff;
      padding: 0.75rem 1rem 0.75rem 2.5rem;
      border-radius: 8px;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s;
    }}

    .search-box input:focus {{
      border-color: var(--accent-blue);
    }}

    .search-box svg {{
      position: absolute;
      left: 0.85rem;
      top: 50%;
      transform: translateY(-50%);
      width: 18px;
      height: 18px;
      color: var(--text-dim);
    }}

    .perspective-pills {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}

    .pill-btn {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 0.5rem 0.85rem;
      border-radius: 8px;
      font-size: 0.825rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s ease;
    }}

    .pill-btn:hover {{
      background: var(--bg-card-hover);
      color: #fff;
    }}

    .pill-btn.active {{
      background: #1e293b;
      color: #fff;
      border-color: var(--accent-blue);
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
    }}

    .category-chips {{
      display: flex;
      gap: 0.4rem;
      flex-wrap: wrap;
      margin-top: 0.25rem;
    }}

    .chip-btn {{
      background: transparent;
      border: 1px solid rgba(255,255,255,0.08);
      color: var(--text-dim);
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      cursor: pointer;
      transition: all 0.15s;
    }}

    .chip-btn:hover, .chip-btn.active {{
      background: rgba(255,255,255,0.1);
      color: var(--text-main);
      border-color: var(--border-accent);
    }}

    /* Grid de Noticias */
    main {{
      max-width: 1300px;
      margin: 1.5rem auto 3rem;
      padding: 0 1rem;
      width: 100%;
      flex: 1;
    }}

    .stats-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      font-size: 0.825rem;
      color: var(--text-dim);
    }}

    .news-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 1.25rem;
    }}

    .card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
      position: relative;
    }}

    .card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-accent);
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }}

    .card-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
    }}

    .badge-perspective {{
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.725rem;
    }}

    .badge-ukraine {{ background: var(--ukraine-bg); color: var(--ukraine-color); border: 1px solid rgba(56, 189, 248, 0.3); }}
    .badge-ru-ind {{ background: var(--ru-ind-bg); color: var(--ru-ind-color); border: 1px solid rgba(52, 211, 153, 0.3); }}
    .badge-ru-off {{ background: var(--ru-off-bg); color: var(--ru-off-color); border: 1px solid rgba(248, 113, 113, 0.3); }}
    .badge-intl {{ background: var(--intl-bg); color: var(--intl-color); border: 1px solid rgba(250, 204, 21, 0.3); }}

    .source-name {{
      color: var(--text-dim);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.725rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 140px;
    }}

    .card-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: #fff;
      line-height: 1.4;
    }}

    /* Caja de Resumen Ejecutivo Rápido */
    .quick-read-box {{
      background: rgba(255, 255, 255, 0.03);
      border-left: 3px solid var(--accent-blue);
      border-radius: 0 6px 6px 0;
      padding: 0.65rem 0.75rem;
    }}

    .quick-read-label {{
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent-blue);
      font-weight: 700;
      margin-bottom: 0.25rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }}

    .quick-read-text {{
      font-size: 0.85rem;
      color: var(--text-main);
      line-height: 1.45;
    }}

    /* Resumen completo traducido */
    .card-summary {{
      font-size: 0.825rem;
      color: var(--text-muted);
      line-height: 1.5;
    }}

    /* Acordeón de texto original */
    .original-section {{
      margin-top: auto;
      padding-top: 0.5rem;
      border-top: 1px solid rgba(255,255,255,0.05);
    }}

    .toggle-original-btn {{
      background: none;
      border: none;
      color: var(--text-dim);
      font-size: 0.75rem;
      cursor: pointer;
      padding: 0.25rem 0;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: color 0.15s;
    }}

    .toggle-original-btn:hover {{
      color: var(--text-muted);
    }}

    .original-box {{
      display: none;
      margin-top: 0.5rem;
      padding: 0.65rem;
      background: rgba(0,0,0,0.3);
      border-radius: 6px;
      font-size: 0.75rem;
      color: #94a3b8;
      font-family: 'JetBrains Mono', monospace;
      line-height: 1.4;
      border: 1px dashed var(--border-color);
    }}

    .original-box.open {{
      display: block;
    }}

    .card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 0.5rem;
      font-size: 0.75rem;
      color: var(--text-dim);
    }}

    .source-link {{
      color: var(--accent-blue);
      text-decoration: none;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      transition: opacity 0.2s;
    }}

    .source-link:hover {{
      text-decoration: underline;
      opacity: 0.85;
    }}

    .empty-state {{
      grid-column: 1 / -1;
      text-align: center;
      padding: 4rem 1rem;
      color: var(--text-dim);
    }}

    footer {{
      border-top: 1px solid var(--border-color);
      padding: 2rem 1rem;
      text-align: center;
      font-size: 0.8rem;
      color: var(--text-dim);
      background: #080c14;
    }}

    @media (max-width: 768px) {{
      .news-grid {{
        grid-template-columns: 1fr;
      }}
      .brand-title {{
        font-size: 1.1rem;
      }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-container">
      <div class="top-bar">
        <div class="brand">
          <div class="brand-icon">⚔️</div>
          <div>
            <div class="brand-title">Monitor <span>Rusia-Ucrania</span></div>
            <div style="font-size: 0.75rem; color: var(--text-dim);">Inteligencia Abierta & Análisis Multifuente Traducido</div>
          </div>
        </div>
        <div class="status-badge">
          <div class="status-dot"></div>
          <span>Actualizado: <span id="last-updated-text">{last_updated}</span></span>
        </div>
      </div>
    </div>
  </header>

  <!-- Resumen Ejecutivo Superior -->
  <section class="executive-brief">
    <div class="executive-header">
      <div class="executive-title">
        <span>⚡</span> Resumen Rápido de Inteligencia (Últimas Horas)
      </div>
      <div style="font-size: 0.75rem; color: var(--text-dim);">Lectura rápida: 60 seg</div>
    </div>
    <div class="brief-columns" id="executive-brief-container">
      <!-- Se llena dinámicamente con JS -->
    </div>
  </section>

  <!-- Filtros y Búsqueda -->
  <div class="controls-container">
    <div class="search-row">
      <div class="search-box">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        <input type="text" id="searchInput" placeholder="Buscar por tema, ciudad (ej. Pokrovsk, Kursk), armamento o actor..." autocomplete="off">
      </div>
      <div class="perspective-pills" id="perspectiveButtons">
        <button class="pill-btn active" data-perspective="all">🌍 Todas las Perspectivas</button>
        <button class="pill-btn" data-perspective="ukraine">🇺🇦 Ucrania</button>
        <button class="pill-btn" data-perspective="russia_independent">🕊️ Rusia Independiente</button>
        <button class="pill-btn" data-perspective="russia_official">🇷🇺 Rusia Oficial</button>
        <button class="pill-btn" data-perspective="international">🌐 Internacional & OSINT</button>
      </div>
    </div>

    <div class="category-chips" id="categoryChips">
      <button class="chip-btn active" data-category="all">Todos los temas</button>
      <button class="chip-btn" data-category="frente">💥 Frente y Combates</button>
      <button class="chip-btn" data-category="drones">🛰️ Drones y Misiles</button>
      <button class="chip-btn" data-category="armamento">🛡️ Armas y Ayuda</button>
      <button class="chip-btn" data-category="diplomacia">🤝 Diplomacia</button>
      <button class="chip-btn" data-category="economia">📉 Sanciones y Energía</button>
      <button class="chip-btn" data-category="civil">🏙️ Impacto Civil</button>
    </div>
  </div>

  <main>
    <div class="stats-bar">
      <div>Mostrando <strong id="articlesCount">0</strong> noticias verificadas y traducidas</div>
      <div id="filterStatus">Filtro: Todos</div>
    </div>

    <div class="news-grid" id="newsGrid">
      <!-- Tarjetas renderizadas con JS -->
    </div>
  </main>

  <footer>
    <p>Monitor de la Guerra Rusia-Ucrania — Compilador automatizado con traducción al español.</p>
    <p style="margin-top: 0.35rem; color: #475569;">Fuentes monitorizadas: The Kyiv Independent, Ukrainska Pravda, Ukrinform, Meduza, The Moscow Times, Novaya Gazeta, TASS, RIA Novosti, ISW y BBC.</p>
  </footer>

  <script id="articles-data" type="application/json">
{articles_json_str}
  </script>
  <script id="perspectives-data" type="application/json">
{perspectives_json_str}
  </script>

  <script>
    const articles = JSON.parse(document.getElementById('articles-data').textContent);
    const perspectives = JSON.parse(document.getElementById('perspectives-data').textContent);

    let activePerspective = 'all';
    let activeCategory = 'all';
    let searchTerm = '';

    function formatTimeAgo(isoString) {{
      try {{
        const diffSec = Math.floor((new Date() - new Date(isoString)) / 1000);
        if (diffSec < 60) return 'Hace un momento';
        const mins = Math.floor(diffSec / 60);
        if (mins < 60) return `Hace ${{mins}}m`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `Hace ${{hours}}h`;
        const days = Math.floor(hours / 24);
        return `Hace ${{days}}d`;
      }} catch (e) {{
        return '';
      }}
    }}

    function renderExecutiveBrief() {{
      const container = document.getElementById('executive-brief-container');
      const sampleByPersp = {{
        'ukraine': {{ label: '🇺🇦 Posición / Terreno Ucrania', art: null, class: 'ukraine' }},
        'russia_independent': {{ label: '🕊️ Análisis Ruso No Censurado', art: null, class: 'russia-ind' }},
        'russia_official': {{ label: '🇷🇺 Comunicado Oficial Kremlin', art: null, class: 'russia-off' }},
        'international': {{ label: '🌐 Evaluación Estratégica ISW / Global', art: null, class: 'intl' }}
      }};

      articles.forEach(a => {{
        if (sampleByPersp[a.perspective] && !sampleByPersp[a.perspective].art) {{
          sampleByPersp[a.perspective].art = a;
        }}
      }});

      let html = '';
      Object.keys(sampleByPersp).forEach(k => {{
        const item = sampleByPersp[k];
        if (item.art) {{
          const text = item.art.quick_summary || item.art.summary_es || item.art.title_es;
          html += `
            <div class="brief-col ${{item.class}}">
              <div class="brief-col-title">${{item.label}}</div>
              <div class="brief-col-text"><strong>${{item.art.title_es}}</strong>: ${{text}}</div>
            </div>
          `;
        }}
      }});
      container.innerHTML = html;
    }}

    function renderArticles() {{
      const grid = document.getElementById('newsGrid');
      const filtered = articles.filter(a => {{
        const matchPersp = (activePerspective === 'all' || a.perspective === activePerspective);
        const matchCat = (activeCategory === 'all' || (a.categories && a.categories.includes(activeCategory)));
        const q = searchTerm.toLowerCase().trim();
        const matchSearch = !q || 
          (a.title_es && a.title_es.toLowerCase().includes(q)) ||
          (a.summary_es && a.summary_es.toLowerCase().includes(q)) ||
          (a.title_original && a.title_original.toLowerCase().includes(q)) ||
          (a.source_name && a.source_name.toLowerCase().includes(q));
        return matchPersp && matchCat && matchSearch;
      }});

      document.getElementById('articlesCount').textContent = filtered.length;

      if (filtered.length === 0) {{
        grid.innerHTML = `
          <div class="empty-state">
            <p style="font-size: 1.25rem; font-weight: 600;">No se encontraron noticias con estos criterios.</p>
            <p style="margin-top: 0.5rem;">Prueba con otra palabra clave o restablece los filtros de perspectiva.</p>
          </div>
        `;
        return;
      }}

      grid.innerHTML = filtered.map(a => {{
        const pInfo = perspectives[a.perspective] || {{ name: a.perspective, icon: '📰', badge_class: 'badge-intl' }};
        const timeAgo = formatTimeAgo(a.published);
        const quickSummary = a.quick_summary || a.summary_es || 'Sin resumen disponible.';

        return `
          <article class="card">
            <div class="card-meta">
              <span class="badge-perspective ${{pInfo.badge_class}}">${{pInfo.icon}} ${{pInfo.short_name || pInfo.name}}</span>
              <span class="source-name" title="${{a.bias_note || a.source_name}}">${{a.source_name}}</span>
            </div>

            <h2 class="card-title">${{a.title_es}}</h2>

            <div class="quick-read-box">
              <div class="quick-read-label">⚡ Lectura Rápida (30 seg)</div>
              <div class="quick-read-text">${{quickSummary}}</div>
            </div>

            ${{a.summary_es && a.summary_es !== quickSummary ? `<p class="card-summary">${{a.summary_es}}</p>` : ''}}

            <div class="original-section">
              <button class="toggle-original-btn" onclick="toggleOriginal('${{a.id}}')">
                <span>🔄</span> Ver texto original (${{a.language.toUpperCase()}})
              </button>
              <div class="original-box" id="orig-${{a.id}}">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">${{a.title_original}}</div>
                <div>${{a.summary_original || ''}}</div>
                <div style="margin-top: 0.35rem; color: #64748b; font-size: 0.7rem;">Nota editorial: ${{a.bias_note}}</div>
              </div>
            </div>

            <div class="card-footer">
              <span>${{timeAgo}}</span>
              <a href="${{a.link}}" target="_blank" rel="noopener noreferrer" class="source-link">
                Leer fuente <span>↗</span>
              </a>
            </div>
          </article>
        `;
      }}).join('');
    }}

    function toggleOriginal(id) {{
      const el = document.getElementById('orig-' + id);
      if (el) {{
        el.classList.toggle('open');
      }}
    }}

    // Event listeners
    document.querySelectorAll('#perspectiveButtons .pill-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('#perspectiveButtons .pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activePerspective = btn.getAttribute('data-perspective');
        renderArticles();
      }});
    }});

    document.querySelectorAll('#categoryChips .chip-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('#categoryChips .chip-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeCategory = btn.getAttribute('data-category');
        renderArticles();
      }});
    }});

    document.getElementById('searchInput').addEventListener('input', (e) => {{
      searchTerm = e.target.value;
      renderArticles();
    }});

    // Inicialización
    renderExecutiveBrief();
    renderArticles();
  </script>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Sitio HTML generado exitosamente en: {OUTPUT_HTML}")

def main():
    print("=" * 60)
    print(" Monitor de Guerra Rusia-Ucrania — Compilador & Traductor ")
    print("=" * 60)

    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] Archivo de configuración no encontrado: {CONFIG_FILE}")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    feeds = config.get("feeds", [])
    perspectives = config.get("perspectives", {})
    settings = config.get("settings", {})
    max_new_translations = settings.get("max_new_translations_per_run", 35)
    request_delay = settings.get("request_delay_seconds", 0.25)
    war_filter = settings.get("filter_general_feeds_by_war_keywords", True)

    print(f"[*] Consultando {len(feeds)} fuentes estratégicas de información...")
    all_articles = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_feed_articles, f, war_filter) for f in feeds]
        for fut in futures:
            try:
                res = fut.result()
                all_articles.extend(res)
            except Exception as e:
                print(f"[WARN] Error en hilo de feed: {e}")

    print(f"[*] Total de artículos recopilados: {len(all_articles)}")

    # Deduplicación por título normalizado
    seen_titles = set()
    deduped = []
    for a in all_articles:
        norm = re.sub(r"[^a-zA-Z0-9\u0400-\u04FF]", "", a["title_original"].lower())[:40]
        if norm and norm not in seen_titles:
            seen_titles.add(norm)
            deduped.append(a)

    # Ordenar por fecha de publicación descendente
    deduped.sort(key=lambda x: x["published"], reverse=True)
    print(f"[*] Artículos únicos tras deduplicar: {len(deduped)}")

    # Cargar caché de traducciones
    translations = {}
    if os.path.exists(TRANSLATIONS_FILE):
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                translations = json.load(f)
            print(f"[*] Caché cargada: {len(translations)} traducciones existentes.")
        except Exception as e:
            print(f"[WARN] No se pudo leer caché previa: {e}")

    # Identificar noticias pendientes de traducción agrupadas por perspectiva
    by_perspective = {}
    for a in deduped:
        art_id = a["id"]
        if a["language"] == "es":
            a["title_es"] = a["title_original"]
            a["summary_es"] = a["summary_original"]
            a["quick_summary"] = generate_quick_summary(a["summary_original"] or a["title_original"])
            a["is_translated"] = True
        elif art_id in translations:
            cached = translations[art_id]
            a["title_es"] = cached.get("title_es", a["title_original"])
            a["summary_es"] = cached.get("summary_es", a["summary_original"])
            a["quick_summary"] = cached.get("quick_summary", generate_quick_summary(a["summary_es"]))
            a["is_translated"] = True
        else:
            a["is_translated"] = False
            p = a["perspective"]
            if p not in by_perspective:
                by_perspective[p] = []
            by_perspective[p].append(a)

    # Distribuir el cupo equitativamente entre perspectivas para máxima diversidad
    queue = []
    persp_keys = list(by_perspective.keys())
    round_idx = 0
    while len(queue) < max_new_translations and any(by_perspective.values()):
        added_in_round = False
        for p in persp_keys:
            if by_perspective[p] and len(queue) < max_new_translations:
                queue.append(by_perspective[p].pop(0))
                added_in_round = True
        if not added_in_round:
            break

    if queue:
        print(f"[*] Traduciendo {len(queue)} artículos nuevos balanceados por perspectiva (límite: {max_new_translations})...")
        for i, a in enumerate(queue, 1):
            t_title = translate_to_es(a["title_original"], max_len=300)
            t_summary = translate_to_es(a["summary_original"], max_len=600)
            q_sum = generate_quick_summary(t_summary or t_title)

            a["title_es"] = t_title
            a["summary_es"] = t_summary
            a["quick_summary"] = q_sum
            a["is_translated"] = True

            translations[a["id"]] = {
                "title_es": t_title,
                "summary_es": t_summary,
                "quick_summary": q_sum
            }
            time.sleep(request_delay)

            if i % 10 == 0 or i == len(queue):
                print(f"    -> {i}/{len(queue)} traducidos...")

        try:
            with open(TRANSLATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            print(f"[OK] Caché de traducciones actualizada con {len(translations)} entradas.")
        except Exception as e:
            print(f"[WARN] Error guardando caché: {e}")
    else:
        print("[*] No hay artículos nuevos pendientes de traducción en el cupo actual.")

    # Para los restantes que excedieron el cupo de esta pasada
    for a in deduped:
        if not getattr(a, "is_translated", False):
            a["title_es"] = a["title_original"]
            a["summary_es"] = a["summary_original"]
            a["quick_summary"] = generate_quick_summary(a["summary_original"] or a["title_original"])
            a["is_translated"] = False

    # Guardar base de datos en JSON
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"[OK] Base de datos guardada en: {CACHE_FILE}")

    # Generar sitio web estático
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    generate_html(deduped, perspectives, now_str)
    print("=" * 60)
    print(" ¡Proceso completado con éxito! ")
    print("=" * 60)

if __name__ == "__main__":
    main()
