CREATE TABLE IF NOT EXISTS raw_grammys (
    year INT,
    title VARCHAR(500),
    category VARCHAR(500),
    nominee VARCHAR(500),
    artist VARCHAR(500),
    workers TEXT,
    img TEXT,
    winner BOOLEAN,
    id VARCHAR(100),
    updated_at TIMESTAMP
);