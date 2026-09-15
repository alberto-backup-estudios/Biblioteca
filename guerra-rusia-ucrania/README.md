# ⚔️ Monitor de Inteligencia: Guerra Rusia-Ucrania

Plataforma de seguimiento y agregación en tiempo real del conflicto entre Rusia y Ucrania con **traducción automática al español**, categorización temática de inteligencia militar y resúmenes ejecutivos de lectura rápida (30 seg).

El monitor recopila y contrasta fuentes rusas (estatales y disidentes), ucranianas y análisis internacional estratégico (OSINT).

---

## 🎯 Fuentes Monitoreadas y Perspectivas

| Perspectiva | Fuente | Idioma Original | Contexto / Sesgo Editorial |
| :--- | :--- | :--- | :--- |
| **🇺🇦 Ucrania** | *The Kyiv Independent* | Inglés | Medio ucraniano independiente de investigación con reporteros sobre el terreno. |
| **🇺🇦 Ucrania** | *Ukrainska Pravda* | Ucraniano / Inglés | Uno de los medios periodísticos más antiguos e influyentes de Ucrania. |
| **🇺🇦 Ucrania** | *Ukrinform* | Inglés / Ucraniano | Agencia de noticias oficial del Estado ucraniano. |
| **🕊️ Rusia Independiente** | *Meduza* | Ruso / Inglés | Principal medio ruso de investigación en el exilio (sede en Riga), prohibido por el Kremlin. |
| **🕊️ Rusia Independiente** | *The Moscow Times* | Inglés | Medio ruso independiente crítico con la administración de Vladímir Putin. |
| **🕊️ Rusia Independiente** | *Novaya Gazeta Europe* | Ruso | Fundada por periodistas del Nobel Dmitry Muratov; seguimiento riguroso de la sociedad y política rusa. |
| **🇷🇺 Rusia Oficial** | *TASS (ТАСС)* | Ruso | Agencia oficial estatal rusa; comunicados del Kremlin y del Ministerio de Defensa de Rusia. |
| **🇷🇺 Rusia Oficial** | *RIA Novosti (РИА)* | Ruso | Red estatal rusa subordinada a Rossiya Segodnya. |
| **🌐 Análisis Internacional** | *ISW (Institute for the Study of War)* | Inglés | Máximo referente global en análisis militar diario, mapas operacionales y movimientos del frente. |
| **🌐 Análisis Internacional** | *BBC News (Europa)* | Inglés | Cobertura verificada con corresponsales en ambos países y diplomacia europea. |

---

## 🚀 Características Principales

1. **Traducción Automática al Español:**
   - Traduce del ruso (`ru`), ucraniano (`uk`) e inglés (`en`) al español (`es`).
   - Mantiene un botón para desplegar el **texto original** y contrastar la traducción.
2. **Protección de API & Control de Cuota:**
   - Para no saturar las APIs de traducción ni recibir bloqueos (HTTP 429), traduce un cupo balanceado por ejecución (por defecto 35 artículos nuevos por ciclo).
   - **Caché persistente (`translations_cache.json`):** Una vez traducido un artículo, se guarda y **nunca** vuelve a gastar cuota.
3. **Resúmenes Ejecutivos (30 seg):**
   - Sintetiza la información clave (*quién, qué ocurrió, dónde y qué bando lo afirma*) para lectura veloz sin perder datos esenciales.
4. **Resumen Rápido de Inteligencia Superior:**
   - Barra en la parte superior con los 4 ángulos clave de las últimas horas.
5. **Buscador en Vivo y Filtros Temáticos:**
   - Filtro por perspectiva (Ucrania, Rusia Oficial, Rusia Independiente, Internacional).
   - Filtro por categoría: *Frente y Combates*, *Drones y Misiles*, *Armas y Ayuda Militar*, *Diplomacia*, *Sanciones y Energía*, *Impacto Civil*.
   - Búsqueda en vivo por palabra clave (ciudades, armamento, líderes, etc.).

---

## 💻 Uso Local en Windows

Para actualizar las noticias y abrir el panel en tu navegador:
1. Haz doble clic en el archivo **`actualizar.bat`**.
2. El script consultará las fuentes, aplicará los filtros, traducirá los nuevos artículos y abrirá automáticamente **`index.html`** en tu navegador web.

---

## 🌐 Publicación en GitHub Pages

El monitor está optimizado para publicarse de forma estática en GitHub:

1. Haz commit y push de esta carpeta dentro de tu repositorio `Biblioteca`.
2. En GitHub, ve a **Settings** > **Pages**.
3. En **Build and deployment**, selecciona la rama `main` y la carpeta `/ (root)`.
4. El sitio estará disponible en:
   `https://alberto-backup-estudios.github.io/Biblioteca/guerra-rusia-ucrania/`
5. Además, el flujo de trabajo en `.github/workflows/update_war_monitor.yml` se ejecutará **automáticamente cada 4 horas en los servidores de GitHub** para actualizar las noticias sin que tengas que tener la computadora encendida.
