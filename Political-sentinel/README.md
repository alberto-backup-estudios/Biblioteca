# Political Sentinel (Centinela Político)

**Sistema de Inteligencia Legislativa, Clasificación de Impacto Socioeconómico y Mapeo Conductual del Congreso de Chile**

---

## 📌 Visión del Proyecto

**Political Sentinel** es una iniciativa de transparencia y ciencia de datos diseñada para conectar el **impacto real y técnico de las leyes** tramitadas en el Congreso Nacional de Chile con la **conducta de voto individual** de cada diputado, senador y bancada política.

El proyecto supera las etiquetas ideológicas tradicionales ("izquierda" vs. "derecha") evaluando a los legisladores mediante evidencia empírica en dos grandes ejes ortogonales:
1. **Extracción y Carga Estatal:** Propensión a votar a favor de mayores impuestos, burocracia/permisología y costos operacionales para el sector privado.
2. **Bienestar y Protección Social:** Propensión a votar a favor de transferencias directas (bonos/subsidios), ampliación de derechos laborales y acceso a bienes públicos garantizados.

---

## 🗺️ Los Dos Mapas Fundamentales

El núcleo metodológico del proyecto se sustenta en dos mapas simétricos:

### 1. Mapa de Impacto de la Ley (Radar de 6 Dimensiones)
Cada ley se analiza en un perfil multidimensional compuesto por 6 ejes:
* **$D_1$ Transferencias y Ayuda Directa:** Bonos, subsidios y asignaciones a familias o sectores vulnerables.
* **$D_2$ Acceso a Bienes Públicos:** Salud, educación pública, vivienda social y subsidios de infraestructura.
* **$D_3$ Derechos y Protección Social:** Normativa laboral (reducción de jornada, seguridad en el trabajo, salario mínimo, protección al consumidor).
* **$D_4$ Carga Fiscal y Tributaria:** Creación o aumento de impuestos, fin de exenciones o incremento del gasto/deuda pública.
* **$D_5$ Costos de Cumplimiento al Privado:** Exigencias técnicas, auditorías obligatorias, seguros forzosos o adecuaciones de plantilla.
* **$D_6$ Carga Burocrática y Regulatoria:** Nuevos permisos requeridos (*permisología*), registros obligatorios y facultades de fiscalización.

### 2. Mapa de Posicionamiento Parlamentario y Bancadas (Plano Cartesiano 2D)
A partir de la conducta histórica de voto de cada legislador, se calculan coordenadas $(X_i, Y_i)$:
* **Eje X (Horizontal):** Carga e Intervención Económica (Menor intervención $\leftarrow \rightarrow$ Mayor intervención).
* **Eje Y (Vertical):** Bienestar y Protección Social (Menor apoyo $\leftarrow \rightarrow$ Mayor apoyo a derechos y subsidios).

#### Los 4 Cuadrantes Resultantes:
* **Cuadrante I (Arriba - Derecha): Socialdemocracia / Estado de Bienestar:** Vota a favor de derechos sociales y bonos, y vota a favor de los impuestos y regulaciones necesarios para financiarlos.
* **Cuadrante II (Arriba - Izquierda): Populismo Fiscal / Asistencialismo No Financiado:** Vota a favor de todos los subsidios y bonos, pero rechaza sistemáticamente los impuestos y reformas fiscales para costearlos.
* **Cuadrante III (Abajo - Izquierda): Liberalismo Pro-Mercado:** Rechaza alzas tributarias y burocracia, privilegiando la iniciativa privada y la focalización mínima del gasto.
* **Cuadrante IV (Abajo - Derecha): Estatismo Burocrático / Corporativismo:** Respalda impuestos y trabas administrativas sin que se traduzcan en beneficios sociales directos para la ciudadanía.

---

## 🏛️ Fuentes de Datos Oficiales en Chile

El sistema aprovecha datos abiertos oficiales del Congreso Nacional de Chile:
* **Cámara de Diputadas y Diputados:** Web Service SOAP/XML (`https://opendata.camara.cl/camaradiputados/WServices/WSLegislativo.asmx`).
* **Senado de la República:** Servicios XML de tramitación legislativa (`https://tramitacion.senado.cl/wspublico/tramitacion.php`).
* **Informes Financieros (DIPRES):** Datos obligatorios sobre costo fiscal y población beneficiaria de cada proyecto.
* **Informes de Productividad (CNEP):** Evaluación del impacto en costos privados y competencia.
* **Biblioteca del Congreso Nacional (BCN):** Catálogo de Linked Open Data (`datos.bcn.cl`).

---

## 📂 Estructura del Repositorio

```
Political-sentinel/
├── README.md                   # Descripción general y guía rápida
├── conversacion_completa.md    # Registro íntegro del diseño conceptual y acuerdos
├── metodologia_y_mapas.md      # Marco matemático, índices y diseño de cuadrantes
├── requirements.txt            # Dependencias Python
├── schemas/
│   └── taxonomia_leyes.json    # Schema JSON estructurado para clasificación de proyectos
└── src/
    └── extractor_camara.py     # Script extractor de votaciones nominales de la Cámara
```

---

## 🚀 Inicio Rápido (Quickstart)

### Requisitos
* Python 3.9+
* Conexión a internet para consultar los endpoints de datos abiertos

### Instalación y Prueba
```bash
cd Political-sentinel
pip install -r requirements.txt
python src/extractor_camara.py
```
