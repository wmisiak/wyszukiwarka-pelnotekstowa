
-- Utworzenie tabeli files
CREATE TABLE IF NOT EXISTS files (
    id BIGINT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    index_structure JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indeks po nazwie pliku
CREATE INDEX IF NOT EXISTS idx_files_filename
    ON files(filename);

-- Indeks GIN dla struktury JSONB
CREATE INDEX IF NOT EXISTS idx_files_index_structure
    ON files USING gin (index_structure);
