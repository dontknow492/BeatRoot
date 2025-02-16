PRAGMA foreign_keys = ON;

-- 1. Artists Table
CREATE TABLE IF NOT EXISTS artists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

-- 2. Albums Table
CREATE TABLE IF NOT EXISTS albums (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    songs_count INTEGER DEFAULT 0
);

-- 3. Album-Artist Relation
CREATE TABLE IF NOT EXISTS album_artists (
    album_id TEXT,
    artist_id TEXT,
    PRIMARY KEY (album_id, artist_id),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

-- 4. Songs Table
CREATE TABLE IF NOT EXISTS songs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    album_id TEXT,
    genre_id TEXT,
    duration INTEGER,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE SET NULL
);

-- 5. Song-Artists Link Table
CREATE TABLE IF NOT EXISTS song_artists (
    song_id TEXT,
    artist_id TEXT,
    PRIMARY KEY (song_id, artist_id),
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

-- 6. Genre Table
CREATE TABLE IF NOT EXISTS genres (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Play History Table
CREATE TABLE IF NOT EXISTS play_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    play_duration INTEGER NOT NULL,
    file_path TEXT
);

-- 8. Liked Songs Table
CREATE TABLE IF NOT EXISTS liked_songs (
    song_id TEXT PRIMARY KEY,
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- 9. Playlists Table
CREATE TABLE IF NOT EXISTS playlists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    cover_art TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Playlist Songs Table
CREATE TABLE IF NOT EXISTS playlist_songs (
    playlist_id TEXT NOT NULL,
    song_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, position),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE (playlist_id, song_id)  
);

-- 11. Playlist History Table (Optional)
CREATE TABLE IF NOT EXISTS playlist_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id TEXT NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
);

-- 12. Full Album History Table (Optional)
CREATE TABLE IF NOT EXISTS full_album_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id TEXT NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);

-- 13. Queue Table
CREATE TABLE IF NOT EXISTS queue (
    song_id TEXT,
    play_position INTEGER NOT NULL,
    file_path TEXT,  -- Store file path here if is local
    PRIMARY KEY(song_id, play_position)
);

--14. Liked Album
CREATE TABLE IF NOT EXISTS liked_albums (
    album_id TEXT PRIMARY KEY,
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
--15. Liked Artist
CREATE TABLE IF NOT EXISTS liked_artists (
    artist_id TEXT PRIMARY KEY,
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

--16. Liked Playlist
CREATE TABLE IF NOT EXISTS liked_playlists (
    playlist_id TEXT PRIMARY KEY,
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
);

-- 17 Local Directories
CREATE TABLE IF NOT EXISTS local_directories (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 18 Local Songs (No file_path here)
CREATE TABLE IF NOT EXISTS local_songs (
    id TEXT PRIMARY KEY,
    title TEXT,
    album TEXT,
    artists TEXT,
    duration INTEGER
);

-- 19 Linking Songs to Directories
CREATE TABLE IF NOT EXISTS local_directory_songs (
    folder_id TEXT,
    song_id TEXT,
    file_path TEXT NOT NULL,  -- Store file path here if songs can be in multiple directories
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (folder_id, song_id),
    FOREIGN KEY (folder_id) REFERENCES local_directories(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES local_songs(id) ON DELETE CASCADE
);
--19. Album Histroy
CREATE TABLE IF NOT EXISTS album_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id TEXT NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);
--20. Donwload Table
    CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL,
    title TEXT,
    downloaded_size FLOAT,
    total_size FLOAT,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT NOT NULL,
    title TEXT,
    downloaded_size FLOAT CHECK (downloaded_size >= 0),
    total_size FLOAT CHECK (total_size > 0),
    status TEXT CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',
    progress FLOAT GENERATED ALWAYS AS (CASE WHEN total_size > 0 THEN (downloaded_size / total_size) * 100 ELSE 0 END) STORED,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    CHECK (downloaded_size <= total_size)
);

CREATE INDEX IF NOT EXISTS idx_downloads_song_id ON downloads(song_id);
CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status);-- Indexes for Performance Optimization
CREATE INDEX IF NOT EXISTS idx_song_id ON play_history(song_id);
CREATE INDEX IF NOT EXISTS idx_artist_id ON song_artists(artist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_id ON playlist_history(playlist_id);
CREATE INDEX IF NOT EXISTS idx_album_id ON full_album_history(album_id);
CREATE INDEX IF NOT EXISTS idx_queue_song_id ON queue(song_id);
