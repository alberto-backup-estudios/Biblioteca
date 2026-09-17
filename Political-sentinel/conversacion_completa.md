# Registro Histórico y Memoria de Conversación: Political Sentinel

**Fecha de Creación:** 17 de Septiembre de 2026  
**Contexto:** Sesión inicial de ideación, viabilidad técnica, fundamentación metodológica y diseño de arquitectura para el proyecto **Political Sentinel**. Este archivo sirve como memoria completa y punto de partida para continuar el desarrollo en cualquier máquina.

---

## 1. Pregunta Inicial y Viabilidad Técnica en el Congreso de Chile

### Consulta del Usuario
> "¿Puedes investigar si es posible obtener desde el congreso de Chile, las votaciones de cada diputado y senador en las diferentes sesiones que se han realizado?"

### Hallazgos de la Investigación
Es **100% viable** obtener el registro nominal e histórico de votaciones de ambas cámaras por mandato de la Ley de Transparencia y políticas de Datos Abiertos:

1. **Cámara de Diputadas y Diputados:**
   * **Portal Oficial de Datos Abiertos:** `https://opendata.camara.cl`
   * **Servicio Web Principal:** `https://opendata.camara.cl/camaradiputados/WServices/WSLegislativo.asmx`
   * **Protocolo:** XML vía SOAP o peticiones HTTP GET directas.
   * **Métodos principales:**
     * `retornarVotacionesXAnno?prmAnno={YYYY}`: Lista todas las votaciones realizadas en un año.
     * `retornarVotacionesXProyectoLey?prmNumeroBoletin={boletin}`: Retorna votaciones asociadas a un proyecto de ley.
     * `retornarVotacionDetalle?prmVotacionId={id}`: Retorna el **voto nominal de cada diputado** (`AFIRMATIVO`, `EN CONTRA`, `ABSTENCION`, `PAREO`, `DISPENSADO`, `AUSENTE`).

2. **Senado de la República:**
   * **Portal Oficial:** `https://www.senado.cl` (sección Datos Abiertos Legislativos).
   * **Servicios Públicos:** `https://tramitacion.senado.cl/wspublico/tramitacion.php?boletin={num_boletin}`, `votaciones.php`, `sesiones.php`.
   * **Detalle:** Entrega la ficha completa del proyecto, informes y el detalle de votaciones en Sala con el sentido de voto de cada senador.

3. **Biblioteca del Congreso Nacional (BCN):**
   * **Linked Open Data:** `https://datos.bcn.cl` (estándares W3C, endpoint SPARQL, ontologías legislativas y cruce con normativa de *Ley Chile*).

4. **Iniciativas Ciudadanas y de Terceros:**
   * Plataformas como *Voto Visible*, *Cochid Datos*, y proyectos de código abierto en GitHub han comprobado la estabilidad del scraping y consumo de estas fuentes oficiales.

---

## 2. Clasificación de Leyes según Costos, Impuestos y Burocracia

### Consulta del Usuario
> "Existen leyes que regulan una industria o sector y que buscan o crear nuevos impuestos, o crear nuevos costos que afectan a un grupo de personas o empresas, o nueva burocracia que busca obtener o información o recaudación, ¿podríamos ver cómo clasificar las leyes en unos cuántos ámbitos de este tipo para poder ver cómo los políticos votaron según qué buscaba la ley? ¿Existe algo así en el mundo? ¿Podemos hacer algo así?"

### Análisis y Antecedentes Mundiales
* **Scorecards Legislativos en EE. UU.:**
  * *NFIB (National Federation of Independent Business):* Reporte *"How Congress Voted"*, que clasifica votos que generan costos regulatorios, exigencias laborales o impuestos a las PyMEs.
  * *Club for Growth / Americans for Tax Reform:* Evalúan a cada legislador según si votó a favor de alzas impositivas o desregulación.
  * *U.S. Chamber of Commerce:* Califica el impacto en la industria y trabas al comercio.
* **Proyectos Académicos:**
  * *Comparative Agendas Project (CAP):* Clasificación temática de políticas públicas.
  * *Modelos NOMINATE:* Posicionamiento espacial de legisladores basado en votaciones roll-call.

### Ventaja Única de Chile
En Chile, el análisis no se basa en especulaciones porque existen insumos oficiales obligatorios:
* **Informes Financieros (DIPRES):** Obligatorios para cualquier proyecto que toque finanzas públicas o impuestos. Especifican recaudación esperada, costos fiscales y creación de entidades públicas.
* **Informes de Productividad (CNEP):** Evalúan el impacto en costos privados, trámites y competencia de proyectos regulatorios clave.

---

## 3. Incorporación de la Dimensión Social, Bienestar y Redistribución

### Consulta del Usuario
> "Me falta la visión socialista del problema, muchas leyes pueden ser para ayudar personas o sectores, bonos, ayuda directa, subvenciones, etc. que tiene costo para el estado o las empresas pero que pueden significar ayuda a las personas, ¿podemos distinguir esto también?"

### Resolución Metodológica
Para evitar un sesgo pro-mercado unilateral, se adoptó un modelo de **doble dimensión (Trade-off de Política Pública)**:
Toda ley se analiza tanto por sus **Cargas y Costos (quién financia)** como por sus **Beneficios y Protección Social (quién recibe y qué se protege)**.

* **Antecedentes Globales de esta Dimensión:**
  * *ADA (Americans for Democratic Action):* El índice progresista más antiguo de EE. UU. (1947), que mide apoyo a leyes laborales, salud pública y subsidios.
  * *AFL-CIO (Central Sindical de EE. UU.):* Mide leyes de derechos laborales, salud ocupacional y pensiones.
  * *Estudios de Bienestar de la OCDE / Esping-Andersen:* Índice de desmercantilización y cobertura universal.

* **Categorías de Bienestar Integradas:**
  1. Transferencias Monetarias Directas (PGU, IFE, Bono Marzo, Subsidio Único Familiar).
  2. Protección y Derechos Laborales (Ley de 40 Horas, salario mínimo, Ley Karin, postnatal).
  3. Bienes Públicos y Acceso Social (gratuidad educacional, copago cero Fonasa, vivienda social).
  4. Protección al Consumidor y Asimetría de Poder (SERNAC sancionatorio, ley de quiebras de personas).
  5. Subsidios y Fomento a Sectores en Crisis (FOGAPE, subsidio al transporte, alivio agrícola).
  6. Grado de Focalización (extrema pobreza vs. clase media vs. universalismo).

---

## 4. Definición de los Dos Mapas Fundamentales

### Consulta del Usuario
> "Antes me gustaría que pudiéramos definir un mapa que nos ayude a entender cómo una ley afecta todas las dimensiones económicas y sociales que has mostrado, y por otro lado, un mapa parecido para definir a un político ya sea diputado o senador, de acuerdo a esas variables evaluadas, como sabemos además el partido o bancada, el mapa podría agregar la información para posicionar a ese conjunto de políticos en nuestro mapa de evaluación, ¿qué opinas?"

### Los Dos Mapas Diseñados

#### MAPA 1: La Huella de la Ley (Radar de 6 Dimensiones)
Cada ley genera un polígono o vector de 6 puntas:
1. **$D_1$:** Transferencias y Ayuda Directa.
2. **$D_2$:** Acceso a Bienes Públicos (Salud, Educación, Vivienda).
3. **$D_3$:** Derechos y Protección Social / Laboral.
4. **$D_4$:** Carga Fiscal y Tributaria.
5. **$D_5$:** Costos de Cumplimiento al Sector Privado.
6. **$D_6$:** Carga Burocrática y Regulatoria (*permisología*).

#### MAPA 2: Plano Cartesiano de Posicionamiento Parlamentario (2D)
Se proyectan los votos de cada parlamentario en dos ejes consolidados:
* **Eje X (Horizontal):** Extracción Económica y Carga Estatal (Menor $\leftarrow \rightarrow$ Mayor intervención).
* **Eje Y (Vertical):** Bienestar y Protección Social (Menor $\leftarrow \rightarrow$ Mayor apoyo a derechos y subsidios).

**Los 4 Cuadrantes:**
* **Cuadrante I (Arriba - Derecha): Socialdemocracia / Estado Social:** Vota a favor de derechos y bonos, y vota a favor de los impuestos que los financian.
* **Cuadrante II (Arriba - Izquierda): Populismo Fiscal:** Vota a favor de todos los bonos y derechos, pero vota en contra de los impuestos para financiarlos.
* **Cuadrante III (Abajo - Izquierda): Liberalismo Pro-Mercado:** Vota en contra de impuestos y regulaciones, promoviendo el mercado y la focalización estricta.
* **Cuadrante IV (Abajo - Derecha): Estatismo Burocrático:** Vota a favor de impuestos y trabas burocráticas sin que generen beneficios directos a las personas.

**Agregación por Bancada / Partido:**
* **Centroide $(\bar{X}_p, \bar{Y}_p)$:** Posición promedio de la bancada.
* **Elipse de Dispersión:** Mide la **disciplina partidaria** (elipse compacta = alta disciplina de bancada; elipse dispersa = baja cohesión o díscolos).

---

## 5. Instrucciones para la Máquina de Casa

Al abrir este proyecto en el PC de la casa:
1. Ejecutar en PowerShell:
   ```powershell
   cd C:\Claude
   .\sincronizar.ps1 pull
   ```
2. Acceder al directorio:
   ```powershell
   cd C:\Claude\biblioteca\Political-sentinel
   ```
3. Revisar los archivos de especificación:
   * `README.md`: Visión ejecutiva del proyecto.
   * `metodologia_y_mapas.md`: Fórmulas matemáticas, índices y cuadrantes.
   * `schemas/taxonomia_leyes.json`: Formato de clasificación para procesar textos con LLMs.
   * `src/extractor_camara.py`: Script funcional para consultar la API de la Cámara.
