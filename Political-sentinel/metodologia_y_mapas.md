# Metodología y Modelo Matemático de Mapas

Este documento detalla las especificaciones analíticas y formulaciones matemáticas para el cálculo de los mapas en **Political Sentinel**.

---

## 1. Vector de Impacto de la Ley ($\vec{L}$)

Cada ley o indicación votada $l$ se describe mediante un vector normalizado en $\mathbb{R}^6$:

$$\vec{L} = (d_1, d_2, d_3, d_4, d_5, d_6)$$

Donde cada componente $d_k \in [-1, 1]$ representa:
* $d_1$: **Transferencias y Ayuda Directa** ($+1$ crea/aumenta bonos o subsidios directos; $-1$ los reduce o elimina).
* $d_2$: **Acceso a Bienes Públicos** ($+1$ expande gratuidad/cobertura en salud, educación o vivienda pública).
* $d_3$: **Derechos y Protección Social/Laboral** ($+1$ incrementa derechos laborales o protección al consumidor; $-1$ flexibiliza o desregula).
* $d_4$: **Carga Fiscal y Tributaria** ($+1$ crea o sube impuestos/deuda fiscal; $-1$ rebaja impuestos o reduce déficit).
* $d_5$: **Costos de Cumplimiento al Privado** ($+1$ impone nuevas exigencias operacionales/costos a empresas; $-1$ simplifica).
* $d_6$: **Carga Burocrática y Regulatoria** ($+1$ agrega trámites, registros y permisos previos; $-1$ desburocratiza).

---

## 2. Ponderación del Voto Parlamentario ($v_{i, l}$)

Para un parlamentario $i$ frente a la votación $l$, la variable de voto se cuantifica de la siguiente forma:

$$v_{i, l} = \begin{cases} 
+1 & \text{si votó AFIRMATIVO (A favor)} \\
-1 & \text{si votó EN CONTRA} \\
0 & \text{si votó ABSTENCIÓN} \\
\text{null} & \text{si estuvo AUSENTE o con PAREO (no computable en la base activa)}
\end{cases}$$

---

## 3. Reducción a Coordenadas Cartesianas 2D ($X_i, Y_i$)

Para proyectar el comportamiento en el **Plano Cartesiano de Posicionamiento**, se agrupan las 6 dimensiones en dos macro-ejes:

### Eje X: Carga e Intervención Económica
Mide la propensión del legislador a apoyar la extracción de recursos y trabas al sector privado:

$$X_i = \frac{1}{|\mathcal{V}_i|} \sum_{l \in \mathcal{V}_i} v_{i, l} \cdot \left( \frac{w_4 d_{4, l} + w_5 d_{5, l} + w_6 d_{6, l}}{w_4 + w_5 + w_6} \right)$$

Donde:
* $\mathcal{V}_i$ es el conjunto de votaciones en las que participó el parlamentario $i$.
* $w_4, w_5, w_6$ son ponderadores relativos de importancia (por defecto $w_k = 1$).
* Rango: $X_i \in [-1, 1]$.
  * $X_i > 0$: Pro-intervención fiscal y regulatoria.
  * $X_i < 0$: Pro-mercado, reducción de impuestos y menor fricción burocrática.

### Eje Y: Bienestar y Protección Social
Mide la propensión del legislador a apoyar transferencias monetarias, servicios públicos y derechos laborales:

$$Y_i = \frac{1}{|\mathcal{V}_i|} \sum_{l \in \mathcal{V}_i} v_{i, l} \cdot \left( \frac{w_1 d_{1, l} + w_2 d_{2, l} + w_3 d_{3, l}}{w_1 + w_2 + w_3} \right)$$

Donde:
* $w_1, w_2, w_3$ son ponderadores relativos (por defecto $w_k = 1$).
* Rango: $Y_i \in [-1, 1]$.
  * $Y_i > 0$: Alto respaldo a programas de bienestar, bonos y protección laboral.
  * $Y_i < 0$: Oposición a la expansión del gasto social directo y regulaciones laborales.

---

## 4. Agregación de Bancadas y Partidos Políticos

Para un partido o bancada $P$ compuesta por $N_P$ parlamentarios:

### A. Centroide Partidario ($\bar{X}_P, \bar{Y}_P$)
Representa la posición institucional media del partido:

$$\bar{X}_P = \frac{1}{N_P} \sum_{i \in P} X_i, \qquad \bar{Y}_P = \frac{1}{N_P} \sum_{i \in P} Y_i$$

### B. Matriz de Covarianza y Elipse de Cohesión
Para medir la disciplina interna y la dispersión ideológica de la bancada, se calcula la matriz de covarianza $\mathbf{\Sigma}_P$:

$$\mathbf{\Sigma}_P = \begin{pmatrix} \sigma_{X}^2 & \sigma_{XY} \\ \sigma_{XY} & \sigma_{Y}^2 \end{pmatrix}$$

* **Índice de Disciplina Partidaria ($ID_P$):**
  $$ID_P = 1 - \sqrt{\sigma_{X}^2 + \sigma_{Y}^2}$$
  * $ID_P \to 1$: Máxima cohesión interna (bancada monolítica).
  * $ID_P \to 0$: Dispersión extrema (voto fragmentado o presencia de díscolos).

* **Representación Gráfica:**
  Cada partido se dibuja con una elipse cuyo centro es $(\bar{X}_P, \bar{Y}_P)$ y cuyos radios corresponden a los semiejes derivados de los autovalores de $\mathbf{\Sigma}_P$ (elipse de confianza al 68% o 95%).

---

## 5. Interpretación de los Cuadrantes

| Cuadrante | Rango | Filosofía de Voto Observada | Características Conductuales |
| :--- | :--- | :--- | :--- |
| **I. Socialdemocracia / Estado Social** | $X > 0, Y > 0$ | *"Recaudar y regular para proteger"* | Vota consistentemente a favor de bonos y derechos, y respalda reformas tributarias para costearlos. |
| **II. Populismo Fiscal / Asistencialismo No Financiado** | $X \le 0, Y > 0$ | *"Repartir sin pagar el costo"* | Aprueba todos los subsidios y aumentos de gasto, pero vota en contra de cualquier impuesto o carga fiscal para financiarlos. |
| **III. Liberalismo Clásico / Pro-Mercado** | $X \le 0, Y \le 0$ | *"Libertad económica y subsidiariedad"* | Rechaza alzas tributarias, desconfía de la intervención estatal y prefiere que el empleo y el mercado resuelvan las necesidades. |
| **IV. Estatismo Burocrático / Corporativismo** | $X > 0, Y \le 0$ | *"Fricción estatal sin beneficio directo"* | Vota a favor de regulaciones, permisos y tributos que engrosan el aparato público sin generar un alivio social visible al ciudadano. |
