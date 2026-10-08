-- ============================================================
-- ESQUEMA DEL DATA WAREHOUSE (MODELO DIMENSIONAL KIMBALL)
-- ============================================================

-- 1. Dimensión Canción (Dim_Track)
CREATE TABLE IF NOT EXISTS dim_track (
    track_key SERIAL PRIMARY KEY,
    track_id VARCHAR(100) UNIQUE NOT NULL,
    track_name VARCHAR(500) NOT NULL,
    album_name VARCHAR(500),
    explicit BOOLEAN
);

-- 2. Dimensión Artista (Dim_Artist)
CREATE TABLE IF NOT EXISTS dim_artist (
    artist_key SERIAL PRIMARY KEY,
    artist_name VARCHAR(500) UNIQUE NOT NULL
);

-- 3. Dimensión Género (Dim_Genre)
CREATE TABLE IF NOT EXISTS dim_genre (
    genre_key SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE NOT NULL
);

-- 4. Dimensión Premios Grammy (Dim_Grammy_Award)
CREATE TABLE IF NOT EXISTS dim_grammy_award (
    grammy_key SERIAL PRIMARY KEY,
    grammy_id VARCHAR(100),
    year INT NOT NULL,
    category VARCHAR(500) NOT NULL,
    nominee VARCHAR(500) NOT NULL,
    winner BOOLEAN NOT NULL
);

-- 5. Tabla de Hechos (Fact_Music_Performance)
CREATE TABLE IF NOT EXISTS fact_music_performance (
    fact_key SERIAL PRIMARY KEY,
    track_key INT NOT NULL,
    artist_key INT NOT NULL,
    genre_key INT NOT NULL,
    grammy_key INT NULL, -- Soporta NULL si la canción no estuvo nominada a un Grammy
    
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
    
    -- Integridad Referencial (Foreign Keys)
    CONSTRAINT fk_fact_track FOREIGN KEY (track_key) REFERENCES dim_track(track_key),
    CONSTRAINT fk_fact_artist FOREIGN KEY (artist_key) REFERENCES dim_artist(artist_key),
    CONSTRAINT fk_fact_genre FOREIGN KEY (genre_key) REFERENCES dim_genre(genre_key),
    CONSTRAINT fk_fact_grammy FOREIGN KEY (grammy_key) REFERENCES dim_grammy_award(grammy_key)
);