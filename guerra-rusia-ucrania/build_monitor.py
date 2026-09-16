# -*- coding: utf-8 -*-
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
from bs4 import BeautifulSoup

# Forzar salida en UTF-8 en consola de Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "feeds_config.json")
HISTORICO_FILE = os.path.join(BASE_DIR, "historico_noticias.json")
ARTICULOS_DIR = os.path.join(BASE_DIR, "articulos_texto")
OUTPUT_HTML = os.path.join(BASE_DIR, "index.html")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,uk-UA,uk;q=0.9,en-US,en;q=0.8,es;q=0.7"
}

# =====================================================================
# REGLAS DE RELEVANCIA BÉLICA Y FILTRO DE RUIDO
# =====================================================================

PENALTY_PATTERNS = [
    # Ruido, entretenimiento, farándula, cantantes, festivales, actores
    r"(фестивал|певиц|певец|гагарин|киркоров|басков|шаман|shaman|актер|актрис|концерт|театр|кино|шоу-биз|знаменитост|celebrity|singer|cantante|concert|concierto|festival|eurovision|gagarina|gagarin|мурал|памятник|шоу|музык|песн)",
    # Deportes, torneos, juegos
    r"(шахмат|fide|chess|футбол|football|футбольн|хоккей|баскетбол|спорт|sport|олимпиад|чемпионат|турнир|матч)",
    # Sucesos locales no bélicos, delitos comunes, accidentes de tráfico
    r"(дтп|пьян|водитель|пешеход|сбил|авари|криминал|полиция задержала|убийство на почве|бытовой конфликт|грабеж|кража|карманник|зоопарк|погод|weather|климат|туризм|гороскоп|цирк|детсад)",
    # Asuntos sociales/internos ajenos al conflicto
    r"(алимент|родительск|детск|ребенок|детей|школ|подростк|соцсет|social media|whiskey|виски|алкогол|тарифы на виски)"
]

MANDATORY_WAR_PATTERNS = [
    # Militar y combate (ruso y ucraniano)
    r"(войн|военн|вооружен|всу|зсу|сво|арми|минобороны|генштаб|фронт|наступлен|штурм|бои|бой|атак|обстрел|снаряд|ракета|дрон|бпла|шахед|герань|пво|ппо|бомбардиров|авиабомб|искандер|кинжал|himars|patriot|atacms|storm shadow|f-16|танк|окоп|потери|погиб|ранен|плен|mobiliz|мобилизац|десант|пехот|командир|бригад|диверс|взрыв)",
    # Inglés / Español militar
    r"(war|military|armed forces|frontline|offensive|assault|combat|battle|strike|shelling|missile|drone|uav|air defense|casualties|killed|wounded|pow|troops|army|soldier|general|guerra|militar|frente|ofensiva|asalto|combate|batalla|ataque|bombardeo|misil|dron|defensa aérea|bajas|muertos|heridos|tropas|ejército)",
    # Diplomacia y sanciones DIRECTAMENTE vinculadas a la guerra / Ucrania / Rusia
    r"(санкци|sanction|sancion|мирные переговор|peace talks|conversaciones de paz|план побед|victory plan|помощь украине|military aid|ayuda militar|поставки оружия|weapons to ukraine|armas a ucrania)"
]

HIGH_RELEVANCE_PATTERNS = [
    # Ubicaciones clave del frente y zonas de combate
    (r"(pokrovsk|покровск|kursk|курск|toretsk|торецк|часов яр|chasiv yar|купянск|kupyansk|kharkiv|харьков|vuhledar|угледар|zaporizhzhia|запорожье|crimea|крым|черное море|black sea|сумы|sumy|белгород|belgorod|брянск|bryansk|донецк|donetsk|луганск|luhansk|херсон|kherson|одесс|odesa)", 12),
    # Operaciones militares clave, avances y ataques
    (r"(наступлен|offensive|штурм|assault|avance|advance|прорыв|frontline|линия фронта|captura|toma|liberaci|минобороны|генштаб|генерал|general)", 10),
    # Armamento pesado, misiles, drones e impactos estratégicos
    (r"(misil|missile|dron|drone|atacms|storm shadow|f-16|patriot|himars|кинжал|kinzhal|искандер|iskander|шахед|shahed|бпла|refiner|нпз|defensa aérea|air defense|пво|ппо|авиабомб)", 8),
    # Alta diplomacia bélica y geopolítica
    (r"(zelensky|зеленск|putin|путин|otan|nato|alto el fuego|ceasefire|negociaci|мирный план|victory plan|peace plan)", 6)
]

CATEGORY_PATTERNS = {
    "frente": [
        r"frontline", r"frente", r"combate", r"advance", r"offensive", r"avance",
        r"pokrovsk", r"покровск", r"kursk", r"курск", r"donetsk", r"donbas",
        r"наступлен", r"штурм", r"бои", r"атак", r"наступ", r"оборон",
        r"capture", r"toma", r"libera", r"territorio", r"kharkiv", r"sumy", r"сумы"
    ],
    "drones": [
        r"drone", r"дрон", r"uav", r"бпла", r"shahed", r"шахед", r"geran", r"герань",
        r"fpv", r"air defense", r"defensa aérea", r"пво", r"ппо", r"intercept",
        r"derrib", r"сбит", r"intercepción", r"enjambre", r"bengalas"
    ],
    "armamento": [
        r"weapon", r"armas", r"armamento", r"missile", r"misil", r"patriot", r"f-16",
        r"himars", r"artillery", r"artillería", r"ammo", r"ammunition", r"munición",
        r"military aid", r"ayuda militar", r"tanque", r"tank", r"снаряд", r"зброя",
        r"поставка", r"оружие", r"пакет помощ"
    ],
    "diplomacia": [
        r"peace", r"paz", r"negotiat", r"negociaci", r"ceasefire", r"alto el fuego",
        r"talks", r"conversaci", r"summit", r"cumbre", r"diplomaci", r"treaty", r"tratado",
        r"переговор", r"мирн", r"соглашени", r"договор", r"перемовини", r"тиша"
    ],
    "economia": [
        r"sanction", r"sanción", r"sanciones", r"oil", r"petróleo", r"gas", r"refinery",
        r"refinería", r"economy", r"economía", r"ruble", r"rublo", r"export",
        r"санкци", r"нефт", r"газ", r"нпз", r"рубл", r"экономік", r"санкці"
    ]
}

def calculate_relevance(title, body):
    combined = f"{title} {body}".lower()

    # 1. Filtro de Ruido (Penalización severa)
    for pat in PENALTY_PATTERNS:
        if re.search(pat, combined):
            return -50

    # 2. Requisito OBLIGATORIO de sustancia bélica directa
    has_war_context = False
    for pat in MANDATORY_WAR_PATTERNS:
        if re.search(pat, combined):
            has_war_context = True
            break

    if not has_war_context:
        return -20

    # 3. Puntuación de impacto estratégico
    score = 5
    for pat, weight in HIGH_RELEVANCE_PATTERNS:
        if re.search(pat, combined):
            score += weight

    return score

def identify_category(text):
    text_lower = text.lower()
    for cat_id, patterns in CATEGORY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return cat_id
    return "frente"

def extract_full_article_body(entry):
    """Extrae los párrafos reales y sustanciales de la noticia (raspado web directo)."""
    title = getattr(entry, "title", "").strip()
    url = getattr(entry, "link", "")

    if url and not "news.google.com" in url:
        try:
            r = requests.get(url, headers=HEADERS, timeout=7)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for s in soup(["script", "style", "nav", "header", "footer", "aside", "form", "figure", "figcaption"]):
                    s.decompose()

                paras = []

                # Caso RIA Novosti: sus párrafos están en <div class="article__text">
                if "ria.ru" in url:
                    ria_paras = [p.get_text().strip() for p in soup.find_all("div", class_="article__text") if len(p.get_text().strip()) > 35]
                    if len(ria_paras) >= 2:
                        return "\n\n".join(ria_paras[:6])

                # Caso Kommersant: párrafos en <p class="doc__text">
                if "kommersant.ru" in url:
                    kom_paras = [p.get_text().strip() for p in soup.find_all("p", class_="doc__text") if len(p.get_text().strip()) > 35]
                    if len(kom_paras) >= 2:
                        return "\n\n".join(kom_paras[:6])

                # Caso Ukrainska Pravda
                if "pravda.com.ua" in url:
                    container = soup.find("div", class_=lambda c: c and "post_text" in str(c).lower()) or soup.find("article")
                    if container:
                        up_paras = [p.get_text().strip() for p in container.find_all("p") if len(p.get_text().strip()) > 35]
                        if len(up_paras) >= 2:
                            return "\n\n".join(up_paras[:6])

                # Caso Interfax-Ucrania
                if "interfax.com.ua" in url:
                    container = soup.find("div", class_="article-content") or soup.find("article")
                    if container:
                        inf_paras = [p.get_text().strip() for p in container.find_all("p") if len(p.get_text().strip()) > 35]
                        if len(inf_paras) >= 2:
                            return "\n\n".join(inf_paras[:6])

                # Caso Deutsche Welle (DW)
                if "dw.com" in url:
                    container = soup.find("div", class_=lambda c: c and "rich-text" in str(c).lower()) or soup.find("article") or soup.find("main")
                    if container:
                        dw_paras = [p.get_text().strip() for p in container.find_all("p") if len(p.get_text().strip()) > 35]
                        if len(dw_paras) >= 2:
                            return "\n\n".join(dw_paras[:6])

                # Extracción general para Meduza, The Moscow Times, BBC, etc.
                container = (
                    soup.find("article") or
                    soup.find("main") or
                    soup.find("div", class_=lambda c: c and any(k in str(c).lower() for k in ["article-body", "story-body", "post-body", "generalmaterial"]))
                )
                if container:
                    for p in container.find_all("p"):
                        t = p.get_text().strip()
                        if len(t) > 40 and not any(k in t.lower() for k in ["cookie", "telegram", "подпис", "читайте", "subscribe", "privacy policy", "all rights reserved"]):
                            if t not in paras:
                                paras.append(t)
                    if len(paras) >= 2:
                        return "\n\n".join(paras[:6])
        except Exception:
            pass

    # 2. Respaldo RSS (únicamente si contiene texto sustancial multilínea)
    content_val = ""
    if getattr(entry, "content", None):
        try:
            content_val = entry.content[0].value
        except Exception:
            pass

    raw = content_val or getattr(entry, "summary", "") or getattr(entry, "description", "")
    if raw:
        soup = BeautifulSoup(raw, "html.parser")
        paras = [p.get_text().strip() for p in soup.find_all(["p", "div"]) if len(p.get_text().strip()) > 35]
        if len(paras) >= 2:
            return "\n\n".join(paras[:6])
        clean = soup.get_text().strip()
        if len(clean) >= 250 and clean != title:
            # Dividir por oraciones si es un párrafo largo
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if len(s.strip()) > 30]
            if len(sentences) >= 2:
                mid = len(sentences) // 2
                return " ".join(sentences[:mid]) + "\n\n" + " ".join(sentences[mid:])
            return clean

    return ""

def translate_single_chunk(text, max_len=600):
    if not text or not text.strip():
        return ""
    text_clean = text.strip()[:max_len]
    try:
        url = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=es&q=" + urllib.parse.quote(text_clean)
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                if isinstance(data[0], list):
                    return "".join([part[0] for part in data if isinstance(part, list)])
                elif isinstance(data[0], str):
                    return data[0]
    except Exception:
        pass

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

def translate_full_story(text, max_paragraphs=6):
    """Traduce la noticia completa párrafo por párrafo al español."""
    if not text or not text.strip():
        return ""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    translated_paras = []
    for p in paragraphs[:max_paragraphs]:
        t = translate_single_chunk(p, max_len=650)
        if t and len(t) > 15:
            translated_paras.append(t)
    return "\n\n".join(translated_paras)

def fetch_feed(feed_config):
    candidates = []
    feed_url = feed_config["url"]
    feed_id = feed_config["id"]
    feed_name = feed_config["name"]
    perspective = feed_config["perspective"]
    language = feed_config["language"]
    bias_note = feed_config.get("bias_note", "")

    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=10)
        parsed = feedparser.parse(resp.content)

        for entry in getattr(parsed, "entries", [])[:30]:
            title = getattr(entry, "title", "Sin título").strip()
            title = re.sub(r"<[^>]+>", "", title).strip()
            body = extract_full_article_body(entry)

            # CONTROL DE CALIDAD ESTRICTO:
            # Descartar artículos sin cuerpo sustancial, con menos de 200 caracteres,
            # sin múltiples párrafos o donde el cuerpo es copia del título.
            if not body or len(body.strip()) < 200 or body.strip() == title:
                continue

            score = calculate_relevance(title, body)
            if score <= 0:
                continue

            link = getattr(entry, "link", "#")

            # Parsear fecha
            pub_date = None
            for attr in ["published_parsed", "updated_parsed", "created_parsed"]:
                parsed_d = getattr(entry, attr, None)
                if parsed_d:
                    try:
                        pub_date = datetime(*parsed_d[:6], tzinfo=timezone.utc).isoformat()
                        break
                    except Exception:
                        pass
            if not pub_date:
                pub_date = datetime.now(timezone.utc).isoformat()

            art_id = hashlib.md5(f"{feed_id}_{title}".encode("utf-8")).hexdigest()[:12]
            category = identify_category(f"{title} {body}")

            candidates.append({
                "id": art_id,
                "title_original": title,
                "text_original": body,
                "link": link,
                "source_id": feed_id,
                "source_name": feed_name,
                "perspective": perspective,
                "language": language,
                "bias_note": bias_note,
                "published": pub_date,
                "category": category,
                "relevance_score": score
            })
    except Exception as e:
        print(f"[WARN] Error en fuente {feed_name}: {e}")

    return candidates

def select_daily_top_articles(candidates, max_per_perspective=8):
    by_persp = {}
    for a in candidates:
        p = a["perspective"]
        if p not in by_persp:
            by_persp[p] = []
        by_persp[p].append(a)

    selected = []
    selected_ids = set()

    for p, items in by_persp.items():
        items.sort(key=lambda x: (x["relevance_score"], x["published"]), reverse=True)
        count = 0
        for a in items:
            if a["id"] not in selected_ids:
                selected.append(a)
                selected_ids.add(a["id"])
                count += 1
                if count >= max_per_perspective:
                    break

    selected.sort(key=lambda x: x["published"], reverse=True)
    return selected

def save_article_text_file(article, date_folder):
    """Guarda cada noticia como un archivo markdown individual en articulos_texto/."""
    os.makedirs(date_folder, exist_ok=True)
    clean_title = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+", "-", article.get("title_es", "noticia")[:50]).strip("-").lower()
    filename = f"{article['id']}_{clean_title}.md"
    filepath = os.path.join(date_folder, filename)

    content = f"""# {article.get('title_es', article['title_original'])}

- **Fecha de publicación:** {article.get('published', '')}
- **Fuente:** {article.get('source_name', '')}
- **Perspectiva:** {article.get('perspective', '')}
- **Idioma original:** {article.get('language', '').upper()}
- **Enlace a la fuente original:** {article.get('link', '#')}
- **Contexto editorial:** {article.get('bias_note', '')}
- **Puntuación de relevancia bélica:** {article.get('relevance_score', 0)}

---

## Noticia Completa Traducida al Español:

{article.get('text_es', '')}

---

## Texto Original ({article.get('language', '').upper()}):

### {article.get('title_original', '')}

{article.get('text_original', '')}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def update_historico_and_translate(selected_articles):
    historico = []
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
                historico = json.load(f)
        except Exception:
            historico = []

    historico_map = {a["id"]: a for a in historico}
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_folder = os.path.join(ARTICULOS_DIR, today_str)

    to_translate = []
    for a in selected_articles:
        if a["id"] in historico_map:
            saved = historico_map[a["id"]]
            a["title_es"] = saved.get("title_es") or a["title_original"]
            a["text_es"] = saved.get("text_es") or a["text_original"]
            a["date_added"] = saved.get("date_added", today_str)
        else:
            a["date_added"] = today_str
            if a["language"] == "es":
                a["title_es"] = a["title_original"]
                a["text_es"] = a["text_original"]
            else:
                to_translate.append(a)

    if to_translate:
        print(f"[*] Traduciendo {len(to_translate)} artículos sustanciales al español (título y párrafos completos)...")
        for i, a in enumerate(to_translate, 1):
            t_title = translate_single_chunk(a["title_original"], max_len=300)
            t_text = translate_full_story(a["text_original"], max_paragraphs=6)

            a["title_es"] = t_title if t_title else a["title_original"]
            a["text_es"] = t_text if t_text else a["text_original"]

            time.sleep(0.25)
            if i % 5 == 0 or i == len(to_translate):
                print(f"    -> {i}/{len(to_translate)} traducidos con éxito...")

    # Guardar archivos de texto y actualizar base de datos histórica
    new_count = 0
    for a in selected_articles:
        save_article_text_file(a, today_folder)
        if a["id"] not in historico_map:
            historico.append(a)
            historico_map[a["id"]] = a
            new_count += 1
        else:
            historico_map[a["id"]].update(a)

    historico.sort(key=lambda x: (x.get("date_added", ""), x.get("published", "")), reverse=True)

    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

    print(f"[OK] Hemeroteca actualizada: {len(historico)} artículos archivados permanentemente (+{new_count} nuevos).")
    return selected_articles, historico

def generate_html_site(daily_articles, historic_articles, perspectives, last_updated):
    """Genera la aplicación web con la estética limpia y probada de AI Sentinel."""
    daily_json_str = json.dumps(daily_articles, ensure_ascii=False)
    historic_json_str = json.dumps(historic_articles, ensure_ascii=False)
    perspectives_json_str = json.dumps(perspectives, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <meta name="theme-color" content="#020617">
  <title>Monitor de Guerra Rusia-Ucrania | Artículos Traducidos & Análisis</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }}
    dialog[open] {{ animation: fadeIn 0.15s ease-out; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: scale(0.97); }} to {{ opacity: 1; transform: scale(1); }} }}
    .no-scrollbar::-webkit-scrollbar {{ display: none; }}
    .no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen pb-16 antialiased">

  <!-- CABECERA PRINCIPAL -->
  <header class="sticky top-0 z-30 backdrop-blur-md bg-slate-950/90 border-b border-slate-800 px-4 lg:px-8 py-3.5">
    <div class="max-w-6xl mx-auto flex items-center justify-between gap-3">
      
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-xl font-bold">
          ⚔️
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="font-extrabold text-base sm:text-lg tracking-tight text-white">Monitor <span class="text-sky-400">Rusia-Ucrania</span></h1>
            <span class="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">En Vivo</span>
          </div>
          <p class="text-[11px] text-slate-400 hidden sm:block">Noticias de alta relevancia traducidas al español de fuentes ucranianas, rusas e internacionales</p>
        </div>
      </div>

      <!-- Pestañas Hoy vs Hemeroteca -->
      <div class="flex items-center gap-1.5 bg-slate-900 p-1 rounded-2xl border border-slate-800 text-xs">
        <button id="tabTodayBtn" class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-bold transition bg-sky-600 text-white shadow-md shadow-sky-600/20">
          <i data-lucide="zap" class="w-3.5 h-3.5"></i>
          <span>Edición de Hoy</span>
        </button>
        <button id="tabArchiveBtn" class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-semibold transition text-slate-400 hover:text-slate-200">
          <i data-lucide="archive" class="w-3.5 h-3.5"></i>
          <span>Hemeroteca</span>
        </button>
      </div>

    </div>
  </header>

  <!-- CONTROLES Y FILTROS -->
  <div class="max-w-6xl mx-auto px-4 lg:px-8 pt-5 pb-3 space-y-3">
    
    <!-- Barra de búsqueda y favoritos -->
    <div class="flex items-center gap-2">
      <div class="relative flex-1">
        <i data-lucide="search" class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"></i>
        <input type="text" id="searchInput" placeholder="Buscar por ciudad (Pokrovsk, Kursk, Toretsk), misiles, drones, sanciones..." 
               class="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition">
      </div>
      <button id="savedFilterBtn" class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-xs font-semibold hover:border-slate-700 transition">
        <i data-lucide="star" class="w-3.5 h-3.5"></i>
        <span class="hidden sm:inline">Guardados</span>
        <span id="savedCount" class="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-300">0</span>
      </button>
    </div>

    <!-- Filtros por Perspectiva -->
    <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1 text-xs">
      <span class="text-slate-500 text-[11px] font-bold uppercase tracking-wider shrink-0 mr-1">Perspectiva:</span>
      <button class="persp-pill active px-3 py-1.5 rounded-xl font-semibold bg-sky-600/20 text-sky-300 border border-sky-500/30 shrink-0" data-persp="all">🌍 Todas</button>
      <button class="persp-pill px-3 py-1.5 rounded-xl font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-persp="ukraine">🇺🇦 Ucrania</button>
      <button class="persp-pill px-3 py-1.5 rounded-xl font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-persp="russia_independent">🕊️ Rusia Independiente</button>
      <button class="persp-pill px-3 py-1.5 rounded-xl font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-persp="russia_official">🇷🇺 Rusia Oficial</button>
      <button class="persp-pill px-3 py-1.5 rounded-xl font-semibold bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-persp="international">🌐 Análisis BBC / DW</button>
    </div>

    <!-- Categorías temáticas -->
    <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar text-xs">
      <span class="text-slate-500 text-[11px] font-bold uppercase tracking-wider shrink-0 mr-1">Tema:</span>
      <button class="cat-pill active px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-800 text-slate-200 border border-slate-700 shrink-0" data-cat="all">Todos</button>
      <button class="cat-pill px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-cat="frente">💥 Frente y Combates</button>
      <button class="cat-pill px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-cat="drones">🛰️ Drones y Misiles</button>
      <button class="cat-pill px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-cat="armamento">🛡️ Armamento y Ayuda</button>
      <button class="cat-pill px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-cat="diplomacia">🤝 Diplomacia y Paz</button>
      <button class="cat-pill px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 shrink-0" data-cat="economia">📉 Sanciones y Energía</button>
    </div>

    <!-- Barra de estado -->
    <div class="flex items-center justify-between text-xs text-slate-500 pt-1">
      <div class="flex items-center gap-1.5">
        <span id="tabModeIndicator" class="font-bold text-slate-400">Edición de Hoy:</span>
        <span id="resultsCount" class="text-slate-400">0 noticias</span>
      </div>
      <div class="text-[11px] text-slate-500">
        Actualizado: <span>{last_updated}</span>
      </div>
    </div>

  </div>

  <!-- CONTENEDOR DE TARJETAS -->
  <main class="max-w-6xl mx-auto px-4 lg:px-8 mt-2">
    <div id="cardsGrid" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Tarjetas renderizadas con JS -->
    </div>
  </main>

  <!-- MODAL DE LECTURA COMPLETA -->
  <dialog id="modal" class="bg-slate-900 text-slate-100 p-0 rounded-2xl border border-slate-800 max-w-2xl w-[92vw] shadow-2xl backdrop:bg-black/75 backdrop:backdrop-blur-sm">
    <div class="p-5 sm:p-6 space-y-4 max-h-[85vh] overflow-y-auto">
      
      <!-- Cabecera del modal -->
      <div class="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <div id="mBadges" class="flex flex-wrap items-center gap-1.5 text-xs mb-1.5"></div>
          <h2 id="mTitle" class="text-base sm:text-lg font-bold text-white leading-snug"></h2>
        </div>
        <button onclick="document.getElementById('modal').close()" class="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white font-bold text-base">&times;</button>
      </div>

      <!-- Nota de sesgo editorial -->
      <div id="mBiasBox" class="bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-xs text-amber-300/90 flex items-start gap-2">
        <i data-lucide="shield-alert" class="w-4 h-4 text-amber-400 shrink-0 mt-0.5"></i>
        <div id="mBiasText"></div>
      </div>

      <!-- Noticia completa en español -->
      <div class="space-y-3 text-xs sm:text-sm leading-relaxed text-slate-200" id="mFullStory">
        <!-- Párrafos traducidos -->
      </div>

      <!-- Texto original plegable -->
      <details class="mt-4 pt-3 border-t border-slate-800/80 text-xs text-slate-400">
        <summary class="cursor-pointer font-semibold text-slate-400 hover:text-slate-200 flex items-center gap-1.5">
          <i data-lucide="languages" class="w-3.5 h-3.5 text-sky-400"></i>
          <span>Contrastar con el texto original sin traducir</span>
        </summary>
        <div id="mOriginalStory" class="mt-3 p-3.5 bg-slate-950 rounded-xl border border-slate-800/60 font-mono text-[11px] leading-relaxed text-slate-400 space-y-2"></div>
      </details>

      <!-- Pie de modal -->
      <div class="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
        <div class="flex items-center gap-2">
          <button id="mBookmarkBtn" class="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center gap-1.5 font-semibold">
            <i data-lucide="star" class="w-3.5 h-3.5"></i>
            <span id="mBookmarkLabel">Guardar</span>
          </button>
        </div>
        <a id="mLink" href="#" target="_blank" rel="noopener noreferrer" class="px-3.5 py-1.5 rounded-xl bg-slate-800 text-slate-400 hover:text-slate-200 flex items-center gap-1.5">
          <span>Visitar fuente original</span>
          <i data-lucide="external-link" class="w-3 h-3"></i>
        </a>
      </div>

    </div>
  </dialog>

  <!-- SCRIPTS Y DATOS -->
  <script id="daily-data" type="application/json">{daily_json_str}</script>
  <script id="historic-data" type="application/json">{historic_json_str}</script>
  <script id="perspectives-data" type="application/json">{perspectives_json_str}</script>

  <script>
    const DAILY_ARTICLES = JSON.parse(document.getElementById('daily-data').textContent);
    const HISTORIC_ARTICLES = JSON.parse(document.getElementById('historic-data').textContent);
    const PERSPECTIVES = JSON.parse(document.getElementById('perspectives-data').textContent);

    let activeTab = 'today'; // 'today' | 'archive'
    let currentPersp = 'all';
    let currentCat = 'all';
    let searchQuery = '';
    let onlySaved = false;
    let savedIds = new Set(JSON.parse(localStorage.getItem('war_monitor_saved') || '[]'));

    function getDataset() {{
      return activeTab === 'today' ? DAILY_ARTICLES : HISTORIC_ARTICLES;
    }}

    function render() {{
      document.getElementById('savedCount').textContent = savedIds.size;
      const data = getDataset();

      let filtered = data.filter(a => {{
        if (onlySaved && !savedIds.has(a.id)) return false;
        if (currentPersp !== 'all' && a.perspective !== currentPersp) return false;
        if (currentCat !== 'all' && a.category !== currentCat) return false;

        if (searchQuery.trim()) {{
          const q = searchQuery.toLowerCase();
          const full = `${{a.title_es || ''}} ${{a.text_es || ''}} ${{a.source_name || ''}}`.toLowerCase();
          if (!full.includes(q)) return false;
        }}
        return true;
      }});

      const modeLabel = activeTab === 'today' ? 'Edición de Hoy' : 'Hemeroteca Histórica';
      document.getElementById('tabModeIndicator').textContent = `${{modeLabel}}:`;
      document.getElementById('resultsCount').textContent = `${{filtered.length}} ${{filtered.length === 1 ? 'noticia' : 'noticias'}}`;

      const grid = document.getElementById('cardsGrid');
      if (filtered.length === 0) {{
        grid.innerHTML = '<div class="col-span-2 p-12 text-center text-slate-500 text-sm">No se encontraron noticias con los criterios seleccionados.</div>';
        return;
      }}

      grid.innerHTML = filtered.map(a => {{
        const isSaved = savedIds.has(a.id);
        const pInfo = PERSPECTIVES[a.perspective] || {{ name: a.perspective, icon: '📰', badge_class: 'badge-intl' }};
        const title = a.title_es || a.title_original;
        const bodyText = a.text_es || a.text_original || '';
        
        // Párrafos para la tarjeta
        const paragraphs = bodyText.split('\n\n').filter(p => p.trim());
        const firstParagraph = paragraphs[0] || 'Información no disponible.';
        const secondParagraph = paragraphs[1] || '';
        const hasMore = paragraphs.length > 2;

        const langBadge = a.language === 'ru' ? '🇷🇺 Ruso' : (a.language === 'uk' ? '🇺🇦 Ucraniano' : '🇬🇧 Inglés');
        const dateTag = a.date_added ? a.date_added : (a.published ? a.published.substring(0, 10) : '');

        let catBadge = '';
        if (a.category === 'frente') catBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">💥 Frente</span>';
        else if (a.category === 'drones') catBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">🛰️ Drones</span>';
        else if (a.category === 'armamento') catBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">🛡️ Armas</span>';
        else if (a.category === 'diplomacia') catBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">🤝 Diplomacia</span>';
        else if (a.category === 'economia') catBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">📉 Sanciones</span>';

        return `
          <article class="p-4 sm:p-5 rounded-2xl bg-slate-900/85 border border-slate-800 flex flex-col justify-between gap-3 hover:border-slate-700 transition shadow-lg shadow-black/40">
            <div class="space-y-2.5">
              <!-- Meta encabezado -->
              <div class="flex items-center justify-between text-xs gap-2 flex-wrap">
                <div class="flex items-center gap-1.5 truncate">
                  <span class="font-bold text-slate-300 bg-slate-800 px-2 py-0.5 rounded text-[11px] truncate max-w-[140px]">${{a.source_name}}</span>
                  <span class="text-[10px] text-slate-500 font-mono">Traducido del ${{langBadge}}</span>
                  ${{catBadge}}
                </div>
                <div class="flex items-center gap-1 text-[11px] text-slate-500 font-mono">
                  <i data-lucide="calendar" class="w-3 h-3"></i>
                  <span>${{dateTag}}</span>
                </div>
              </div>

              <!-- Título en español -->
              <h3 class="text-sm sm:text-base font-bold text-white hover:text-sky-300 transition leading-snug cursor-pointer" onclick="openModal('${{a.id}}')">
                ${{title}}
              </h3>

              <!-- NOTICIA COMPLETA TRADUCIDA EN ESPAÑOL -->
              <div class="text-xs sm:text-sm text-slate-300 leading-relaxed space-y-2 cursor-pointer" onclick="openModal('${{a.id}}')">
                <p>${{firstParagraph}}</p>
                ${{secondParagraph ? `<p>${{secondParagraph}}</p>` : ''}}
                ${{hasMore ? `<div class="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 pt-1"><span>Ver artículo completo (${{paragraphs.length}} párrafos traducidos)...</span> <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i></div>` : ''}}
              </div>
            </div>

            <!-- Pie de tarjeta -->
            <div class="flex items-center justify-between pt-2.5 border-t border-slate-800/80 text-xs">
              <button onclick="toggleSave('${{a.id}}')" class="p-1 rounded text-slate-400 hover:text-amber-400 transition flex items-center gap-1 ${{isSaved ? 'text-amber-400 font-bold' : ''}}">
                <i data-lucide="star" class="w-3.5 h-3.5 ${{isSaved ? 'fill-amber-400 text-amber-400' : ''}}"></i>
                <span class="text-[11px]">${{isSaved ? 'Guardado' : 'Guardar'}}</span>
              </button>

              <div class="flex items-center gap-2">
                <button onclick="openModal('${{a.id}}')" class="px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold transition text-xs shadow-md shadow-sky-600/20">
                  Leer completo
                </button>
                <a href="${{a.link}}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1.5 rounded-xl bg-slate-800 text-slate-400 hover:text-slate-200 text-xs transition" title="Abrir fuente original">
                  Fuente ↗
                </a>
              </div>
            </div>
          </article>
        `;
      }}).join('');

      if (window.lucide) window.lucide.createIcons();
    }}

    function toggleSave(id) {{
      if (savedIds.has(id)) savedIds.delete(id);
      else savedIds.add(id);
      localStorage.setItem('war_monitor_saved', JSON.stringify(Array.from(savedIds)));
      render();
    }}

    function openModal(id) {{
      const data = getDataset();
      const a = data.find(x => x.id === id) || DAILY_ARTICLES.find(x => x.id === id) || HISTORIC_ARTICLES.find(x => x.id === id);
      if (!a) return;

      const pInfo = PERSPECTIVES[a.perspective] || {{ name: a.perspective }};
      const langBadge = a.language === 'ru' ? '🇷🇺 Ruso' : (a.language === 'uk' ? '🇺🇦 Ucraniano' : '🇬🇧 Inglés');

      document.getElementById('mBadges').innerHTML = `
        <span class="bg-sky-500/20 text-sky-300 font-bold px-2 py-0.5 rounded">${{a.source_name}}</span>
        <span class="bg-slate-800 text-slate-400 px-2 py-0.5 rounded">Traducido del ${{langBadge}}</span>
        <span class="text-slate-500 text-[11px]">${{a.published ? a.published.substring(0, 10) : ''}}</span>
      `;

      document.getElementById('mTitle').textContent = a.title_es || a.title_original;
      document.getElementById('mBiasText').textContent = a.bias_note || 'Fuente periodística en zona de conflicto.';

      // Párrafos completos traducidos
      const paragraphs = (a.text_es || a.text_original || '').split('\n\n').filter(p => p.trim());
      document.getElementById('mFullStory').innerHTML = paragraphs.map(p => `<p class="leading-relaxed mb-3">${{p}}</p>`).join('');

      // Texto original
      const origParas = (a.text_original || '').split('\n\n').filter(p => p.trim());
      document.getElementById('mOriginalStory').innerHTML = `
        <div class="font-bold text-slate-300 mb-1.5">${{a.title_original}}</div>
        ${{origParas.map(p => `<p class="mb-2">${{p}}</p>`).join('')}}
      `;

      document.getElementById('mLink').href = a.link;

      const isSaved = savedIds.has(a.id);
      document.getElementById('mBookmarkLabel').textContent = isSaved ? 'Guardado' : 'Guardar';
      document.getElementById('mBookmarkBtn').onclick = () => {{
        toggleSave(a.id);
        const nowSaved = savedIds.has(a.id);
        document.getElementById('mBookmarkLabel').textContent = nowSaved ? 'Guardado' : 'Guardar';
      }};

      document.getElementById('modal').showModal();
      if (window.lucide) window.lucide.createIcons();
    }}

    // Pestañas Hoy vs Hemeroteca
    const tabTodayBtn = document.getElementById('tabTodayBtn');
    const tabArchiveBtn = document.getElementById('tabArchiveBtn');

    tabTodayBtn.onclick = () => {{
      activeTab = 'today';
      tabTodayBtn.className = "flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-bold transition bg-sky-600 text-white shadow-md shadow-sky-600/20";
      tabArchiveBtn.className = "flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-semibold transition text-slate-400 hover:text-slate-200";
      render();
    }};

    tabArchiveBtn.onclick = () => {{
      activeTab = 'archive';
      tabArchiveBtn.className = "flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-bold transition bg-sky-600 text-white shadow-md shadow-sky-600/20";
      tabTodayBtn.className = "flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-semibold transition text-slate-400 hover:text-slate-200";
      render();
    }};

    // Filtro Guardados
    document.getElementById('savedFilterBtn').onclick = () => {{
      onlySaved = !onlySaved;
      document.getElementById('savedFilterBtn').classList.toggle('bg-amber-500/20', onlySaved);
      document.getElementById('savedFilterBtn').classList.toggle('text-amber-300', onlySaved);
      render();
    }};

    // Filtros por Perspectiva
    document.querySelectorAll('.persp-pill').forEach(btn => {{
      btn.onclick = () => {{
        document.querySelectorAll('.persp-pill').forEach(b => {{
          b.classList.remove('active', 'bg-sky-600/20', 'text-sky-300', 'border-sky-500/30');
          b.classList.add('bg-slate-900', 'text-slate-400', 'border-slate-800');
        }});
        btn.classList.add('active', 'bg-sky-600/20', 'text-sky-300', 'border-sky-500/30');
        btn.classList.remove('bg-slate-900', 'text-slate-400', 'border-slate-800');
        currentPersp = btn.dataset.persp;
        render();
      }};
    }});

    // Filtros por Categoría
    document.querySelectorAll('.cat-pill').forEach(btn => {{
      btn.onclick = () => {{
        document.querySelectorAll('.cat-pill').forEach(b => {{
          b.classList.remove('active', 'bg-slate-800', 'text-slate-200', 'border-slate-700');
          b.classList.add('bg-slate-900', 'text-slate-400', 'border-slate-800');
        }});
        btn.classList.add('active', 'bg-slate-800', 'text-slate-200', 'border-slate-700');
        btn.classList.remove('bg-slate-900', 'text-slate-400', 'border-slate-800');
        currentCat = btn.dataset.cat;
        render();
      }};
    }});

    // Búsqueda en tiempo real
    document.getElementById('searchInput').addEventListener('input', (e) => {{
      searchQuery = e.target.value;
      render();
    }});

    // Cierre modal con click en backdrop
    document.getElementById('modal').addEventListener('click', (e) => {{
      if (e.target.id === 'modal') e.target.close();
    }});

    // Render inicial
    render();
  </script>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] Sitio HTML generado exitosamente en: {OUTPUT_HTML}")

def main():
    print("=" * 65)
    print(" Monitor Rusia-Ucrania — Priorización por Relevancia & Texto Completo ")
    print("=" * 65)

    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] No se encontró el archivo de configuración {CONFIG_FILE}")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    feeds = config.get("feeds", [])
    perspectives = config.get("perspectives", {})

    print(f"[*] Consultando {len(feeds)} fuentes estratégicas de información...")
    all_candidates = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(fetch_feed, f) for f in feeds]
        for fut in futures:
            try:
                res = fut.result()
                all_candidates.extend(res)
            except Exception as e:
                print(f"[WARN] Error en feed: {e}")

    print(f"[*] Total de candidatos relevantes con texto sustancial: {len(all_candidates)}")

    # Deduplicar por título normalizado
    seen = set()
    deduped = []
    for a in all_candidates:
        norm = re.sub(r"[^a-zA-Z0-9Ѐ-ӿ]", "", a["title_original"].lower())[:45]
        if norm and norm not in seen:
            seen.add(norm)
            deduped.append(a)

    print(f"[*] Candidatos únicos filtrados sin ruido ni baja relevancia: {len(deduped)}")

    # Seleccionar Top diario (hasta 8 por perspectiva, noticias de máxima relevancia)
    daily_selected = select_daily_top_articles(deduped, max_per_perspective=8)
    print(f"[*] Seleccionados para la Edición de Hoy: {len(daily_selected)} artículos de máxima relevancia bélica.")

    # Traducir texto completo y archivar en articulos_texto/ e historico_noticias.json
    daily_articles, historic_articles = update_historico_and_translate(daily_selected)

    # Generar sitio web estático
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    generate_html_site(daily_articles, historic_articles, perspectives, now_str)

    print("=" * 65)
    print(" ¡Compilación completada con éxito! ")
    print("=" * 65)

if __name__ == "__main__":
    main()
