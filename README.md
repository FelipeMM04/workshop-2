# Workshop 2: Data Pipeline & Data Warehouse para Análisis Musical (Spotify & Grammy Awards)

## 📌 Descripción del Proyecto
Este proyecto implementa una arquitectura de datos de extremo a extremo (ETL Pipeline y Data Warehouse) en PostgreSQL. El sistema integra dos fuentes de datos principales:
1. **Spotify Tracks Dataset**: Registros CSV con información de reproducciones, métricas de audio y metadatos de canciones.
2. **Grammy Awards Dataset**: Registro histórico almacenado en una base de datos relacional PostgreSQL con las nominaciones y ganadores de los Premios Grammy.

El objetivo analítico principal es evaluar la relación entre el desempeño comercial/características de audio de las canciones en plataformas de streaming y su reconocimiento por parte de la academia de premios Grammy.

---

## 🛠️ Tecnologías Utilizadas
* **Lenguaje:** Python 3.12
* **Base de Datos / DW:** PostgreSQL 16
* **Contenerización:** Docker & Docker Compose
* **Librerías Python:** `pandas`, `psycopg2`, `great_expectations`, `jupyter`
* **Entorno de Desarrollo:** Visual Studio Code (Jupyter Extension)

---

## 📁 Estructura del Proyecto

text
workshop-2/
│
├── data/
│   └── raw/
│       └── spotify_dataset.csv     # Dataset crudo de Spotify
│
├── notebooks/
│   └── data_profiling.ipynb        # Cuaderno reproducible de perfilamiento
│
├── sql/
│   └── source_setup.sql            #DDL para la tabla cruda raw_grammys
│
├── src/
│   ├── quality.py                  # Suite de validación de calidad con Great Expectations
│   └── transform.py                # Módulo de limpieza y transformación de datos
│
├── docker-compose.yaml             # Configuración del contenedor de PostgreSQL
├── requirements.txt                # Dependencias del proyecto
└── README.md                       # Documentación técnica del proyecto

---


### 🚀 Avances e Hitos Completados Hasta el Momento

#### 1. Configuración de Entorno e Infraestructura (Secciones 4 y 5)
- [x] **Despliegue de contenedor PostgreSQL**: Configurado y desplegado con Docker Compose en el puerto `5432`.
- [x] **Persistencia de datos**: Implementada mediante volúmenes de Docker (`postgres_data`).
- [x] **Ingesta inicial**: Creación de la tabla `raw_grammys` e ingesta completa de **4,810 registros** históricos.

#### 2. Perfilamiento y Análisis de Riesgos de Calidad (Secciones 6.2 y 6.3)
- [x] **Desarrollo del notebook** (`notebooks/data_profiling.ipynb`): Cubre las 7 dimensiones requeridas por la rúbrica:
  - **Structure & Completeness**: Conteo e interpretación de nulos (1 nulo en metadata de Spotify; nulos parciales en `artist`, `workers` e `img` en Grammy).
  - **Uniqueness & Duplication**: Detección de **24,259 registros duplicados** por `track_id` en Spotify debido a múltiples clasificaciones por género (`track_genre`).
  - **Categorical & Numerical Content**: Verificación de rangos numéricos (`popularity` de 0 a 100, `duration_ms` $\ge 0$).
  - **Temporal & Cross-Source Content**: Cobertura histórica en Grammy (1958–2019/2020) y evaluación de coincidencias exactas de nombres de artistas.

  ---

  ### 📊 Matriz de Análisis de Riesgos de Calidad de Datos (Data Quality Risk Matrix)

| Dataset / Attribute | Profiling Evidence | Potential Quality Risk | Related Requirement |
| :--- | :--- | :--- | :--- |
| **Spotify / `track_id`** | 24,259 registros duplicados por pertenecer a varios géneros. | Duplicación de métricas numéricas y sesgo en agregaciones del Data Warehouse. | **Transformación**: Deduplicación por `track_id` conservando el registro con mayor `popularity`. |
| **Spotify / `Unnamed: 0`** | Columna con índice secuencial redundante. | Ruido en los datos y desperdicio de almacenamiento. | **Limpieza**: Eliminación explícita de la columna. |
| **Spotify / `duration_ms`** | Registros con duración $\ge 0\text{ ms}$. | Posibles valores atípicos o muestras incompletas. | **Validación**: Expectativa automatizada $\ge 0\text{ ms}$. |
| **Grammy / `artist`** | 1,840 valores nulos/faltantes. | Pérdida de integridad referencial al enlazar con la dimensión Artista. | **Transformación**: Imputación con `'Varios / No especificado'`. |
| **Grammy / `workers`, `img`** | Presencia de nulos en metadata complementaria. | Fallos en el pipeline por valores `NULL`. | **Transformación**: Imputación con cadenas vacías `''`. |
| **Cross-Source / Matching** | Variaciones ortográficas y de formato entre ambas fuentes. | Fallos en los cruces (*joins*) entre fuentes. | **Estandarización**: Limpieza de cadenas (`trim`, minúsculas). |

---

#### 3. Validación Automatizada de Calidad con Great Expectations (Sección 6.3)
- [x] **Creación del script `src/quality.py`**: Aplica validaciones automatizadas sobre ambas fuentes:
  - **Integridad**: No nulidad en `track_id` (Spotify) y `year` (Grammy).
  - **Rangos Numéricos**: Popularidad ($0 \le \text{popularity} \le 100$) y duración ($\text{duration\_ms} \ge 0$).
  - **Cobertura Temporal**: Rango de años en Grammy ($1950 \le \text{year} \le 2030$).

#### 4. Diseño del Modelo Dimensional (Sección 6.4)
- [x] **Definición formal de la arquitectura bajo la metodología Kimball**:

| Decisión de Diseño | Contenido Requerido | Definición de Arquitectura |
| :--- | :--- | :--- |
| **Business Process** | Proceso del negocio | **Análisis de Desempeño Musical y Reconocimiento**: Evaluación de métricas de reproducción junto a reconocimientos históricos de la industria. |
| **Grain of the Fact Table** | Grano de la tabla de hechos | Un registro por `track_id` único de Spotify consolidado, asociado a su género principal y a su estado de premiación Grammy. |
| **Dimensions** | Contextos analíticos | • `Dim_Track` (`track_key`, `track_id`, `track_name`, `album_name`, `explicit`)<br>• `Dim_Artist` (`artist_key`, `artist_name`)<br>• `Dim_Genre` (`genre_key`, `genre_name`)<br>• `Dim_Grammy_Award` (`grammy_key`, `year`, `category`, `nominee`, `winner`) |
| **Measures** | Métricas numéricas | • `popularity`<br>• `duration_ms`<br>• Métricas de audio (`danceability`, `energy`, `valence`, `tempo`, etc.)<br>• `is_grammy_nominated` (1 / 0)<br>• `is_grammy_winner` (1 / 0) |
| **Keys and Relationships** | Claves primarias y foráneas | **Surrogate Keys** numéricas auto-incrementales en dimensiones y **Foreign Keys** en la tabla de hechos con integridad referencial (soportando `NULL` para canciones sin premios). |
| **Requirement Support** | Soporte analítico | Permite consultas cruzadas para comparar métricas de audio y popularidad por género según estado de premiación Grammy a lo largo del tiempo. |

---

## 6.4 Diseños del Modelo Dimensional (Dimensional Model Design)

### 1. Definición del Arquitectura Dimensional (Kimball)
Antes de diseñar la lógica final de transformación e integración, se definió el modelo dimensional objetivo a partir de los requerimientos analíticos del proyecto y los datos disponibles en las fuentes origen (`spotify_dataset.csv` y `raw_grammys` en PostgreSQL).

| Decisión de Diseño | Contenido Requerido | Definición de Arquitectura en el Data Warehouse |
| :--- | :--- | :--- |
| **Business Process** | Proceso del negocio | **Análisis de Desempeño Musical y Reconocimiento de la Industria**: Evaluación integrada de las métricas de reproducción/popularidad en plataformas de streaming junto con el historial de reconocimientos y galardones de la industria (Grammy Awards). |
| **Grain of the Fact Table** | Grano de la tabla de hechos | **Un registro por canción única de Spotify (`track_id`), asociada a su género principal y a su estado de premiación en los Grammy (si aplica)**. |
| **Dimensions** | Contextos analíticos descriptivos | • **`dim_track`**: Metadatos descriptivos de la canción (`track_id`, `track_name`, `album_name`, `explicit`).<br>• **`dim_artist`**: Entidad de artista (`artist_name`).<br>• **`dim_genre`**: Clasificación por género musical (`genre_name`).<br>• **`dim_grammy_award`**: Contexto del premio histórico (`year`, `category`, `nominee`, `winner`). |
| **Measures** | Métricas numéricas o hechos | • **Métricas continuas**: `popularity` (0-100), `duration_ms` (duración en ms), `danceability`, `energy`, `loudness`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence`, `tempo`.<br>• **Indicadores booleanos/contables**: `is_grammy_nominated` ($1$ / $0$), `is_grammy_winner` ($1$ / $0$). |
| **Keys and Relationships** | Claves primarias, foráneas y estrategia de llaves | • **Surrogate Keys (Claves Sustitutas)**: Claves primarias numéricas auto-incrementales (`SERIAL PRIMARY KEY`) en todas las dimensiones (`track_key`, `artist_key`, `genre_key`, `grammy_key`).<br>• **Business Keys (Claves de Negocio)**: `track_id` (Spotify) y clave compuesta `(year, category, nominee)` (Grammy).<br>• **Foreign Keys**: `fact_music_performance` contiene las llaves foráneas hacia cada dimensión, permitiendo valores `NULL` en `grammy_key` para canciones que no tienen nominación/premio registrado. |
| **Requirement Support** | Soporte a requerimientos analíticos | Permite realizar consultas cruzadas y agregaciones SQL para comparar atributos de audio y niveles de popularidad entre canciones ganadoras/nominadas a los Grammy vs. no nominadas, desglosadas por género y evolución temporal a lo largo de los años. |

---

### 2. Esquema Físico DDL del Data Warehouse (`sql/dw_schema.sql`)

El modelo dimensional definido fue implementado en la base de datos PostgreSQL `music_dw` mediante el siguiente script DDL:

sql
-- 1. Dimensión Canción
CREATE TABLE IF NOT EXISTS dim_track (
    track_key SERIAL PRIMARY KEY,
    track_id VARCHAR(100) UNIQUE NOT NULL,
    track_name VARCHAR(500) NOT NULL,
    album_name VARCHAR(500),
    explicit BOOLEAN
);

-- 2. Dimensión Artista
CREATE TABLE IF NOT EXISTS dim_artist (
    artist_key SERIAL PRIMARY KEY,
    artist_name VARCHAR(500) UNIQUE NOT NULL
);

-- 3. Dimensión Género
CREATE TABLE IF NOT EXISTS dim_genre (
    genre_key SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE NOT NULL
);

-- 4. Dimensión Premios Grammy
CREATE TABLE IF NOT EXISTS dim_grammy_award (
    grammy_key SERIAL PRIMARY KEY,
    grammy_id VARCHAR(100),
    year INT NOT NULL,
    category VARCHAR(500) NOT NULL,
    nominee VARCHAR(500) NOT NULL,
    winner BOOLEAN NOT NULL
);

-- 5. Tabla de Hechos
CREATE TABLE IF NOT EXISTS fact_music_performance (
    fact_key SERIAL PRIMARY KEY,
    track_key INT NOT NULL,
    artist_key INT NOT NULL,
    genre_key INT NOT NULL,
    grammy_key INT NULL,
    
    -- Métricas de Spotify
    popularity INT,
    duration_ms INT,
    danceability FLOAT,
    energy FLOAT,
    key INT,
    loudness FLOAT,
    mode INT,
    speechiness FLOAT,
    acousticness FLOAT,
    instrumentalness FLOAT,
    liveness FLOAT,
    valence FLOAT,
    tempo FLOAT,
    
    -- Indicadores de Premiación
    is_grammy_nominated INT DEFAULT 0,
    is_grammy_winner INT DEFAULT 0,
    
    -- Restricciones de Integridad Referencial
    CONSTRAINT fk_fact_track FOREIGN KEY (track_key) REFERENCES dim_track(track_key),
    CONSTRAINT fk_fact_artist FOREIGN KEY (artist_key) REFERENCES dim_artist(artist_key),
    CONSTRAINT fk_fact_genre FOREIGN KEY (genre_key) REFERENCES dim_genre(genre_key),
    CONSTRAINT fk_fact_grammy FOREIGN KEY (grammy_key) REFERENCES dim_grammy_award(grammy_key)
);

---

## 6.5 Reglas de Calidad de Datos y Diseño de Validación (Data Quality Rules and Validation Design)

Se convierten los riesgos identificados durante la fase de perfilamiento en **7 reglas explícitas de calidad de datos** aplicadas a lo largo de las capas del pipeline (Raw, Transformación y Carga al Data Warehouse).

### 1. Matriz de Reglas de Calidad (Data Quality Rules Matrix)

| Rule ID | Dataset / Layer | Attribute(s) | Quality Dimension | Quality Rule | Metric / Threshold | Severity | Related Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **QR-01** | Spotify / Raw | `track_id` | **Completeness** | No deben existir registros con identificador principal nulo o vacío. | $0\%$ Nulos ($\text{Success} = 100\%$) | **Critical** | Identificación unívoca de entidades en dimensiones y llaves foráneas. |
| **QR-02** | Spotify / Raw | `popularity` | **Validity** | El índice de popularidad debe estar en el rango válido de la API de Spotify. | $0 \le \text{popularity} \le 100$ | **Critical** | Precisión en agregaciones y comparaciones de rendimiento comercial. |
| **QR-03** | Spotify / Raw | `duration_ms` | **Validity** | La duración de la canción en milisegundos debe ser un número no negativo. | $\text{duration\_ms} \ge 0$ | **Warning** | Evitar métricas atípicas o registros con errores de muestreo en streaming. |
| **QR-04** | Spotify / Clean | `track_id` | **Uniqueness** | Garantizar que el grano de la tabla limpia no tenga IDs de canción duplicados. | $0$ duplicados tras deduplicación por mayor popularidad. | **Critical** | Prevención de duplicación de métricas al cargar la tabla de hechos. |
| **QR-05** | Grammy / Raw | `year` | **Completeness / Validity** | El año del premio debe ser no nulo y dentro del periodo de premiaciones históricas. | No nulo y $1950 \le \text{year} \le 2030$ | **Critical** | Integridad del análisis temporal y filtrado por décadas. |
| **QR-06** | Grammy / Clean | `artist` | **Completeness** | Tratar registros de artistas ausentes para mantener la integridad referencial. | $0\%$ nulos post-imputación (`'Varios / No especificado'`). | **Warning** | Evitar pérdidas de filas al realizar el *join* con `Dim_Artist`. |
| **QR-07** | Integrated / DW | `track_key`, `artist_key`, `genre_key` | **Integrity** | Las claves foráneas en la tabla de hechos no deben romper la integridad con dimensiones. | $0\%$ de huérfanos sin correspondencia en las dimensiones. | **Critical** | Integridad referencial del Modelo Dimensional Kimball. |

---

### 2. Justificación Técnica de Umbrales y Políticas de Severidad

* **`Critical` (Bloqueante)**: Reglas **QR-01, QR-02, QR-04, QR-05, QR-07**. Un fallo en estas reglas compromete directamente la integridad del Data Warehouse (duplicación de métricas o inconsistencia referencial). La política exige detener la ejecución del lote (*batch*).
* **`Warning` (Advertencia/Monitoreo)**: Reglas **QR-03, QR-06**. Los valores atípicos de duración o metadatos faltantes de artista son tratados en la capa de transformación mediante imputación o filtrado controlado sin abortar la carga global.

---

### 3. Justificación de Umbrales de Ingeniería (Threshold Engineering Rationale)

Cada umbral seleccionado responde a restricciones del dominio de negocio y del modelo dimensional target, evitando la fijación arbitraria de parámetros:

* **QR-01 (`track_id` No Nulo - 100% Success)**:
  * *Justificación*: El atributo `track_id` es la Clave de Negocio (*Business Key*) utilizada para identificar unívocamente las canciones de Spotify. Permitir un solo registro nulo quebrantaría el grano de la dimensión `dim_track` e impediría la generación de su `track_key` (Surrogate Key).
* **QR-02 (`popularity` entre 0 y 100)**:
  * *Justificación*: Definido por la especificación del contrato de la API de Spotify. Valores fuera de este rango denotan corrupción de datos en la fuente cruda y alterarían el cálculo de métricas agregadas (`AVG(popularity)`).
* **QR-03 (`duration_ms` $\ge 0$)**:
  * *Justificación*: Basado en los hallazgos del perfilamiento donde se detectaron registros con $0\text{ ms}$. Un umbral de $1\text{ ms}$ abortaba innecesariamente el pipeline frente a muestras cortas o registros por imputar. Fijar $\ge 0$ permite que la capa de extracción capture el dato y traslade la regla de limpieza a la capa de transformación.
* **QR-04 (0 Duplicados en `track_id` post-limpieza)**:
  * *Justificación*: En el perfilamiento se identificaron 24,259 duplicados en Spotify por pertenecer a múltiples géneros. Para garantizar la integridad del modelo en estrella (relación 1 a N entre dimensión y hechos), la capa de transformación debe garantizar $0$ duplicados antes de la carga.
* **QR-05 (`year` en Grammy entre 1950 y 2030)**:
  * *Justificación*: Los premios Grammy iniciaron en 1958. Un rango $[1950, 2030]$ protege la ingesta contra años corruptos (ej. valores negativos, 0 o fechas futuras inconsistentes) garantizando la validez en el análisis de series de tiempo.
* **QR-06 (0% Nulos en `artist` post-imputación)**:
  * *Justificación*: Existen 1,840 registros en Grammy sin artista especificado (categorías grupales o compilaciones). En lugar de descartar las nominaciones, se imputa `'Varios / No especificado'` para asegurar que el $100\%$ de los registros de hechos puedan enlazarse con la dimensión `dim_artist`.
* **QR-07 (0% Huérfanos de Integridad Referencial)**:
  * *Justificación*: Exigencia estricta de la metodología Kimball. Toda clave foránea (`track_key`, `artist_key`, `genre_key`) en `fact_music_performance` debe existir previamente en su respectiva tabla de dimensión.

---

## 6.6 Diseño e Implementación de Great Expectations (GX Design)

### 1. Elementos del Diseño de Validación

| Elemento de Diseño | Documentación Requerida | Implementación en el Proyecto |
| :--- | :--- | :--- |
| **Expectation** | Chequeos individuales que implementan las reglas de calidad declaradas. | Métodos nativos de GX (`expect_column_values_to_not_be_null`, `expect_column_values_to_be_between`). |
| **Expectation Suite** | Conjunto coherente de reglas aplicado a un dataset o capa. | `spotify_raw_suite` (Capa Spotify CSV) y `grammy_raw_suite` (Capa Grammy PostgreSQL). |
| **Validation Definition** | Asociación explícita entre la fuente de datos y la suite. | Vinculación mediante DataFrames de Pandas cargados desde las fuentes crudas (`gx.from_pandas()`). |
| **Checkpoint / Execution** | Control de ejecución, retención de resultados y política de severidad. | Orquestador en `src/quality.py` que evalúa las reglas, calcula estadísticas numéricas por ítem (`unexpected_count`, `unexpected_percent`) y aplica política de bloqueo ante reglas `Critical`. |

---

### 2. Mapeo de Expectativas GX a Reglas de Calidad (Rule ID Mapping)

| Rule ID | Dataset / Layer | Attribute(s) | Expectativa de Great Expectations (GX) | Metric / Threshold | Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **QR-01** | Spotify / Raw | `track_id` | `expect_column_values_to_not_be_null('track_id')` | $0\%$ Nulos (`unexpected_count = 0`) | **Critical** |
| **QR-02** | Spotify / Raw | `popularity` | `expect_column_values_to_be_between('popularity', min_value=0, max_value=100)` | $0 \le \text{pop} \le 100$ | **Critical** |
| **QR-03** | Spotify / Raw | `duration_ms` | `expect_column_values_to_be_between('duration_ms', min_value=0)` | $\text{duration\_ms} \ge 0$ | **Warning** |
| **QR-05a** | Grammy / Raw | `year` | `expect_column_values_to_not_be_null('year')` | $0\%$ Nulos (`unexpected_count = 0`) | **Critical** |
| **QR-05b** | Grammy / Raw | `year` | `expect_column_values_to_be_between('year', min_value=1950, max_value=2030)` | $1950 \le \text{year} \le 2030$ | **Critical** |
| **QR-06** | Grammy / Raw | `winner` | `expect_column_values_to_not_be_null('winner')` | $0\%$ Nulos (`unexpected_count = 0`) | **Critical** |

---

### 3. Evidencia Preservada de Resultados de Validación (Validation Results Evidence)

#### A. Ejecución Exitosa (Successful Execution Log)
text
======================================================================
 [GX EXECUTION] EVALUANDO EXPECTATION SUITE: spotify_raw_suite (SUCCESS CASE)
======================================================================

[Rule QR-01] track_id NOT NULL:
  - Success: True
  - Element Count: 114,000
  - Unexpected Count: 0

[Rule QR-02] popularity BETWEEN 0 AND 100:
  - Success: True
  - Unexpected Count: 0

[Rule QR-03] duration_ms >= 0:
  - Success: True
  - Unexpected Count: 0

======================================================================
 [GX EXECUTION] EVALUANDO EXPECTATION SUITE: grammy_raw_suite
======================================================================

[Rule QR-05a] year NOT NULL:
  - Success: True
  - Element Count: 4,810
  - Unexpected Count: 0

[Rule QR-05b] year BETWEEN 1950 AND 2030:
  - Success: True
  - Unexpected Count: 0

[Rule QR-06] winner NOT NULL:
  - Success: True
  - Unexpected Count: 0

======================================================================
✅ RESULTADO GLOBAL CHECKPOINT: SUITE COMPLETA APROBADA
======================================================================

---

## 6.7 Extracción de Datos y Validación Cruda (Data Extraction and Raw Validation)

### 1. Arquitectura de Ramas de Origen Independientes (Source Branches)

El pipeline implementa dos ramas de extracción y validación aisladas e independientes antes de cualquier proceso de limpieza o integración:

text
[Rama Spotify] : extract_spotify ──> validate_spotify_raw (Gate 1) ──┐
                                                                      ├──> [Transformación / Carga]
[Rama Grammy]  : extract_grammys ──> validate_grammys_raw (Gate 2) ──┘

---

## 6.8 Transformación de Datos e Integración (Data Transformation and Integration)

### 1. Decisiones de Transformación de Datos (Data Transformation Rationale)

| Decision | Rule and Rationale | Affected Fields | Before / After Behavior | Exception Handling | Analytical Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Deduplicación de Streaming** | Conservar el registro de mayor popularidad. El perfilamiento reveló $24,259$ duplicados en Spotify por pertenecer a varios géneros. | `track_id`, `popularity`, `track_genre` | **Antes**: Mismo `track_id` repetido hasta 10 veces.<br>**Después**: $1$ solo registro por `track_id` conservando el valor con mayor `popularity`. | Si dos registros tienen igual popularidad, se selecciona el primero ordenado por género. | Evita la duplicación de métricas de reproducción y distorsión en agregaciones (`SUM`/`AVG`) en el Data Warehouse. |
| **Limpieza de Atributos Redundantes** | Eliminación de índices secuenciales sin significado de negocio (`Unnamed: 0`). | Columna `Unnamed: 0` | **Antes**: Columna de índice redundante de extracción.<br>**Después**: Atributo descartado completamente de la memoria. | Descarte directo de la columna si está presente. | Optimización de almacenamiento en disco e higiene en el esquema dimensional `dim_track`. |
| **Normalización de Cadenas para Matching** | Limpieza de caracteres de control, espacios extremales (*trim*) y conversión a minúsculas en entidades principales. | `track_name`, `artists` (Spotify) y `nominee`, `artist` (Grammy) | **Antes**: Cadenas con variaciones ortográficas y espacios (ej. `" Adele "`, `"Adele"`).<br>**Después**: Formato estandarizado en minúsculas y limpio (`"adele"`). | Sustitución por `'desconocido'` si la cadena resulta vacía tras la limpieza. | Aumenta la tasa de coincidencia exacta (*match rate*) en el cruce entre fuentes heterogéneas. |
| **Imputación de Metadatos Ausentes** | Tratamiento de valores nulos o vacíos en la fuente de premios para categorías colectivas. | `artist` (en Grammy, $1,840$ nulos) | **Antes**: Valores `NaN` / `NULL`.<br>**Después**: Reemplazados por el literal `'Varios / No especificado'`. | Asignación predeterminada a un elemento reservado en la dimensión. | Garantiza la integridad referencial con `dim_artist` sin desechar nominaciones históricas reales. |

---

### 2. Contrato de Integración (Integration Contract)

#### A. Estrategia de Cruce y Preprocesamiento

| Item | Team Decision and Evidence |
| :--- | :--- |
| **Integration Key(s)** | Estrategia de coincidencia en 2 capas:<br>1. **Primary Strategy (Exact Normalized Match)**: Llave compuesta trazable `clean_track_name + '||' + clean_artist_name`.<br>2. **Fallback Strategy**: Coincidencia por nombre de nominado/artista `clean_artist_name` y año de lanzamiento para piezas de catálogo. |
| **Cardinality** | **Relación $0..1$ a $N$ (Zero-or-One to Many)**:<br>• Una canción única en `dim_track` puede no tener ningún registro en los Grammy ($0$).<br>• Una canción o artista en Spotify puede estar asociada a $1$ o múltiples nominaciones/premios Grammy históricamente ($N$). |
| **Preprocessing** | 1. Aplicación de `strip()`, remoción de acentos/puntuación básica y `lower()` en nombres de pista y artistas.<br>2. Extracción y aislamiento del artista principal cuando el campo contiene colaboraciones (*feat. / with*). |

#### B. Manejo de Excepciones y Limitaciones

| Item | Team Decision and Evidence |
| :--- | :--- |
| **Unmatched Records** | Las canciones de Spotify sin coincidencia en la fuente de los Grammy permanecen en el Data Warehouse con `grammy_key = NULL`, fijando las banderas `is_grammy_nominated = 0` e `is_grammy_winner = 0`. Esto preserva la totalidad de la muestra de streaming para análisis de control. |
| **Duplicate Matches** | Si una canción coincide con múltiples categorías o años en los Grammy, se genera un registro en la tabla de hechos por cada nominación individual asociada a la misma clave de dimensión `track_key`, vinculando el `grammy_key` correspondiente a cada ceremonia. |
| **Assumptions and Limitations** | **Asunción**: El nombre del artista en Spotify coincide razonablemente con el campo `nominee`/`artist` de los Grammy.<br>**Limitación**: Canciones grabadas con variaciones de nombre de banda extremas o traducciones no cruzarán de forma automática sin un índice de similitud tipográfica (*Fuzzy Matching*). |

---

### 3. Evidencia de Transformación e Integración (Execution Evidence)

text
[TRANSFORM SPOTIFY] Registros limpios y deduplicados: 89,741
[TRANSFORM GRAMMYS] Registros limpios e imputados: 4,810

[INTEGRATION] Ejecutando cruce bajo el Integration Contract...
 -> Total registros consolidados: 89,778
 -> Coincidencias con nominaciones Grammy: 272

 ---

 ## 6.9 Validación de Datos Preparados (Prepared Data Validation - Gate 2)

### 1. Arquitectura de Control de Dos Puertas (Two-Gate Architecture)

El pipeline de ingesta implementa un control de calidad en dos fases obligatorias para garantizar la estabilidad e integridad del Data Warehouse Kimball:

text
                  Gate 1: Raw Validation                     Gate 2: Prepared Validation
[Data Sources] ───────────► [validate_raw] ───► [Transform & Integrate] ───► [validate_prepared] ───► [load_dw]
                                                                                      │
                                                                             (If Critical Fail) ──► ❌ BLOCK LOAD

---                                                                       

| Puerta de Validación | Pregunta Principal | Objetivo de Control |
| :--- | :--- | :--- |
| **Gate 1: Raw Validation** | ¿Pueden estos datos ingresar de manera segura a la transformación? | Garantizar que las fuentes de origen no contengan corrupción que altere la lógica de transformación. |
| **Gate 2: Prepared Validation** | ¿La transformación produjo datos aceptables y listos para la carga? | Verificar unicidad de dimensiones, rangos de métricas consolidadas, integridad de banderas y preparación analítica antes de invocar `load_dw`. |

---

## 6.10 Carga del Data Warehouse y Modelado Dimensional (Data Warehouse Loading and Dimensional Modeling)

### 1. Estrategia de Carga y Aislamiento del Data Warehouse
La etapa final de carga al Data Warehouse (`load_dw` en `src/load.py`) es una fase desacoplada e independiente del proceso de ingesta inicial (`raw_grammys`). Se encarga de transformar los datos integrados y validados en el **Modelo Dimensional Kimball (Esquema en Estrella)** implementado en PostgreSQL (`music_dw`).

* **Aislamiento de Capas**: La tabla `raw_grammys` actúa únicamente como zona de *staging* para la extracción cruda. La carga final escribe de manera estricta sobre las tablas dimensionales del Data Warehouse (`dim_track`, `dim_artist`, `dim_genre`, `dim_grammy_award` y `fact_music_performance`).
* **Poblado Secuencial de Dimensiones**: Se limpian e insertan primero las tablas de dimensión generando sus respectivas Claves Sustitutas numéricas auto-incrementales (`SERIAL PRIMARY KEY`).
* **Inserción Idempotente**: Implementa un reinicio en cascada (`TRUNCATE ... RESTART IDENTITY CASCADE`) para garantizar la repetibilidad de la ejecución sin generar duplicación de claves ni registros.

---

### 2. Mapeo de Claves Sustitutas e Integridad Referencial

| Clave / Relación | Tipo de Clave | Estrategia de Mapeo y Tratamiento de Excepciones |
| :--- | :--- | :--- |
| **`track_key`** | Surrogate Key (PK) | Generada automáticamente en `dim_track`. Mapeada mediante la Business Key `track_id`. Si el título o álbum vienen nulos, se imputan valores por defecto (`'Sin Título'`, `'Sin Álbum'`). |
| **`artist_key`** | Surrogate Key (PK) | Generada automáticamente en `dim_artist`. Mapeada mediante la Business Key `artist_name`. Nulos se reemplazan por `'Artista Desconocido'`. |
| **`genre_key`** | Surrogate Key (PK) | Generada automáticamente en `dim_genre`. Mapeada mediante `genre_name`. Nulos se reemplazan por `'Desconocido'`. |
| **`grammy_key`** | Surrogate Key (PK) | Generada automáticamente en `dim_grammy_award`. Mapeada mediante la clave compuesta `(year, category, nominee)`. Para las canciones de Spotify sin premio/nominación registrada, se inserta un valor `NULL` en la FK de la tabla de hechos, preservando la regla de integridad Kimball. |

---

### 3. Evidencia de Ejecución de Carga al Data Warehouse (Load Execution Proof)

```text
======================================================================
 [DW LOAD] INICIANDO CARGA DIMENSIONAL EN POSTGRESQL (music_dw)
======================================================================
 -> Reiniciando tablas del modelo dimensional...
 -> Cargando dim_track...
 -> Cargando dim_artist...
 -> Cargando dim_genre...
 -> Cargando dim_grammy_award...
 -> Resolviendo Surrogate Keys para fact_music_performance...
 -> Insertando registros en fact_music_performance...
✅ [DW LOAD COMPLETO] Insertados 89,777 registros en fact_music_performance.