
import asyncio
from pathlib import Path
from typing import Dict

import aiosqlite
from PySide6.QtCore import QObject, Signal
from loguru import logger

from data.user.database import initialize_database
from src.utility.duration_parse import seconds_to_duration


class DatabaseManager(QObject):
    error = Signal(str)
    fetched = Signal(list)
    closed = Signal()
    def __init__(self, db_path, sql_path, parent=None):
        super().__init__(parent=parent)
        self.db_path = db_path
        with open(sql_path, 'r') as f:
            self.schema_sql = f.read()
            logger.info("Schema sql loaded succesfully:")
        self.db = None  # Initialize to None, will connect asynchronously
        logger.debug(f"Database initialized at {self.db_path}")
        

    async def create_tables(self):
        """Create necessary tables."""
        try:
            logger.debug("Creating tables...")
            await initialize_database(self.db_path, self.schema_sql)  # Make sure the correct db_path is passed
            self.db = await aiosqlite.connect(self.db_path)  # Re-establish connection after initialization
            # await self.db.execute("PRAGMA foreign_keys = ON;")
            logger.success("Tables created successfully.")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")

    async def _connect_db(self):
        """Connect to the database asynchronously."""
        try:
            if not Path(self.db_path).exists():
                logger.info(f"Database not found at {self.db_path}. Creating a new database.")
                await self.create_tables()

            logger.success(f"Connecting to database at {self.db_path}")
            self.db = await aiosqlite.connect(self.db_path, check_same_thread=False)  # Await the connection
            await self.db.execute("PRAGMA foreign_keys = ON;")
        except aiosqlite.Error as e:
            logger.critical(f"Error connecting database: {e}")
            self.error.emit(str(e))
            self.db = None

    async def fetch_song(self, song_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT id, title, album_id, genre_id, duration FROM songs WHERE id = ?", (song_id,)) as cursor:
                data =  await cursor.fetchone()
                if not data:
                    return None
                song_data = {
                    'videoId': data[0],
                    'title': data[1],
                    'albumId': data[2],
                    'genreId': data[3],
                    'duration': data[4],
                }
                return song_data
        except aiosqlite.Error as e:
            logger.error(f"Database fetch song: '{song_id}' Error: {e}")
            return None
        

    async def insert_artist(self, artist: Dict):
        """
        artist is dict with id, name key 
        """
        if self.db is None:
            await self._connect_db()
        artist_id = artist.get('id', None)
        if not artist_id:
            logger.error("Database Insertion Error: Artist ID is missing")
            return
        artist_name = artist.get('name', "Unknown")
        try:
            async with self.db.execute("""
                INSERT INTO artists (id, name)
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name
            """, (artist_id, artist_name)):
                await self.db.commit()
                logger.success(f"Artist '{artist_id}' inserted/updated successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database artist: '{artist_id}' insert Error: {e}")

    async def insert_album(self, album: Dict):
        if self.db is None:
            await self._connect_db()
        album_id = album.get('id', None)
        if not album_id:
            logger.error("Database Error: Album ID is missing")
            return
        album_name = album.get('name', None) or album.get('title', "Unknown")
        track_count = album.get('trackCount', 0)
        try:
            # Use UPSERT to insert or update the album
            async with self.db.execute("""
                INSERT INTO albums (id, name, songs_count)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name,
                songs_count = excluded.songs_count
            """, (album_id, album_name, track_count)):
                await self.db.commit()
                logger.success(f"Album '{album_id}' inserted or updated successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database album: '{album_id}' insert/update Error: {e}")

    async def insert_playlist(self, playlist: Dict):
        if self.db is None:
            await self._connect_db()
        playlist_id = playlist.get('id', None)
        if not playlist_id:
            logger.error("Database Error: Playlist ID is missing")
            return
        playlist_name = playlist.get('title', "Unknown")
        description = playlist.get('description', "")
        cover_art = playlist.get('cover_art', "")
        
        try:
            # Use UPSERT to insert or update the playlist
            async with self.db.execute("""
                INSERT INTO playlists (id, name, description, cover_art)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET 
                    name = excluded.name,
                    description = excluded.description,
                    cover_art = excluded.cover_art
            """, (playlist_id, playlist_name, description, cover_art)):
                await self.db.commit()
                logger.success(f"Playlist '{playlist_id}' inserted or updated successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database playlist: '{playlist_id}' insert/update Error: {e}")

    logger.catch
    async def insert_song(self, song: Dict):
        if self.db is None:
            await self._connect_db()
        song_id = song.get('videoId', None)
        if not song_id:
            logger.error("Database Error: Song ID is missing")
            return

        title = song.get('title', "Unknown")
        if title != "Unknown":
            title = self._normalize_string(title)
            logger.debug(f"Normalized title: {title}")
        album = song.get('album', {}) or {}
        artists = song.get('artists', []) or []
        duration = song.get('duration', None) or song.get('length', "00:00")
        # Convert duration from "MM:SS" format to seconds (integer)
        try:
            minutes, seconds = map(int, duration.split(':'))
            duration_seconds = minutes * 60 + seconds
        except (ValueError, AttributeError):
            duration_seconds = 0  # Default to 0 if duration is invalid

        # Insert album if it exists
        if album:
            await self.insert_album(album)

        # Insert song
        try:
            async with self.db.execute(
                """INSERT INTO songs (id, title, album_id, duration) VALUES (?, ?, ?, ?)
                ON CONFLICT(id) Do Nothing
                """,
                (song_id, title, album.get('id', None), duration_seconds)
            ):
                await self.db.commit()
                logger.success(f"Song {title}-{song_id} inserted successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database song: '{song_id}' insert Error: {e}")

        # Insert artists and link them to the song
        for artist in artists:
            if artist and artist.get('id'):
                await self.insert_artist(artist)
                await self.link_song_artist(song_id, artist.get('id'))

    async def insert_local_song(self, song: Dict):
        if self.db is None:
            await self._connect_db()
        song_id = song.get('videoId', None)
        if not song_id:
            logger.error("Database Error: Song ID is missing")
            return

        title = song.get('title', "Unknown")
        if title != "Unknown":
            title = self._normalize_string(title)
            logger.debug(f"Normalized title: {title}")
        album = song.get('album', "Unknown")
        artists = song.get('artists', "Unknown")
        duration = song.get('duration', None) or song.get('length', "00:00")
        # Convert duration from "MM:SS" format to seconds (integer)
        try:
            minutes, seconds = map(int, duration.split(':'))
            duration_seconds = minutes * 60 + seconds
        except (ValueError, AttributeError):
            duration_seconds = 0  # Default to 0 if duration is invalid


        # Insert song
        try:
            async with self.db.execute(
                """INSERT INTO local_songs (id, title, artists, album, duration) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) Do Nothing
                """,
                (song_id, title, artists, album, duration_seconds)
            ):
                await self.db.commit()
                logger.success(f"Song {title}-{song_id} inserted successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database song: '{song_id}' insert Error: {e}")

    async def insert_directory_songs(self, song_id: str, folder_id: str, file_path: str):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute(
                """INSERT INTO local_directory_songs (song_id, folder_id, file_path) VALUES (?, ?, ?)
                ON CONFLICT DO NOTHING
                """
                , (song_id, folder_id, file_path)):
                await self.db.commit()
                logger.success(f"Song '{song_id}' added to folder '{folder_id}'")
        except aiosqlite.Error as e:
            logger.error(f"Database local directory song: '{song_id}' insert Error: {e}")
    
    async def insert_playlist_song(self, playlist_id, song_id, position):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute(
                """INSERT INTO playlist_songs (playlist_id, song_id, position) VALUES (?, ?, ?)
                ON CONFLICT DO UPDATE SET position = excluded.position
                """
                , (playlist_id, song_id, position)):
                await self.db.commit()
                logger.success(f"Song '{song_id}' added to playlist '{playlist_id}'")
        except aiosqlite.Error as e:
            logger.error(f"Database playlist: '{playlist_id}' song: '{song_id}' insert Error: {e}")
            
    async def insert_liked_song(self, song_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO liked_songs (song_id) VALUES (?)", (song_id,)):
                await self.db.commit()
                logger.success(f"Song '{song_id}' liked successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database Liked Song Error: {e}")
    
    async def insert_liked_artist(self, artist_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO liked_artists (artist_id) VALUES (?)", (artist_id, )):
                await self.db.commit()
                logger.success(f"Artist '{artist_id}' liked successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database Liked Artist Error: {e}") 
            
    async def insert_liked_album(self, album_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO liked_albums (album_id) VALUES (?)", (album_id, )):
                await self.db.commit()
                logger.success(f"Album '{album_id}' liked successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database Liked Album Error: {e}")
            
    async def insert_liked_playlist(self, playlist_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO liked_playlists (playlist_id) VALUES (?)", (playlist_id,)):
                await self.db.commit()
                logger.success(f"Playlist '{playlist_id}' liked successfully")
        except aiosqlite.Error as e:
            logger.error(f"Database Liked Playlist Error: {e}")
            
    async def insert_play_history(self, song_id: str, duration: int, file_path: str = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO play_history (song_id, play_duration, file_path) VALUES (?, ?, ?)", (song_id, duration, file_path)):
                await self.db.commit()
                logger.success(f"Song '{song_id}' added to play history")
        except aiosqlite.Error as e:
            logger.error(f"Database Play History Error: {e}")
            
    async def insert_full_album_history(self, album_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO full_album_history (album_id) VALUES (?)", (album_id,)):
                await self.db.commit()
                logger.success(f"Album '{album_id}' added to album history")
        except aiosqlite.Error as e:
            logger.error(f"Database Album History Error: {e}")
            
    async def insert_playlist_history(self, playlist_id, song_id, duration):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO playlist_history (playlist_id, song_id, duration) VALUES (?, ?, ?)", (playlist_id, song_id, duration)):
                await self.db.commit()
                logger.success(f"Playlist '{playlist_id}' added to full playlist history")
        except aiosqlite.Error as e:
            logger.error(f"Database Full Playlist History Error: {e}")
            
    async def insert_local_directory(self, folder_id, dir_path):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO local_directories (id, path) VALUES (?, ?)", (folder_id, dir_path)):
                await self.db.commit()
                logger.success(f"Local directory '{dir_path}' added to database")
        except aiosqlite.Error as e:
            logger.error(f"Database Local Directory Error: {e}")
        
    async def insert_queue_song(self, song_id, position, path):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("INSERT INTO queue (song_id, play_position, file_path) VALUES (?, ?, ?)", (song_id, position, path)):
                await self.db.commit()
                logger.success(f"Song '{song_id}' added to queue")
        except aiosqlite.Error as e:
            logger.error(f"Database Queue Song Error: {e}")
            
    async def remove_liked_song(self, song_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("DELETE FROM liked_songs WHERE song_id = ?", (song_id,)):
                await self.db.commit()
                logger.success(f"Song '{song_id}' removed from liked songs")
        except aiosqlite.Error as e:
            logger.error(f"Error removing liked song '{song_id}' from database: {e}")
            
    async def remove_playlist_song(self, playlist_id, song_id):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?", (playlist_id, song_id)):
                await self.db.commit()
                logger.success(f"Song '{song_id}' removed from playlist '{playlist_id}'")
        except aiosqlite.Error as e:
            logger.error(f"Error removing song '{song_id}' from playlist '{playlist_id}' database: {e}")
    
    async def link_album_artists(self, album_id, artist_id):
        if album_id is None or artist_id is None:
            logger.error("Database Error: Can't link because Album ID or Artist ID is missing")
            return
        try:
            async with self.db.execute("""
                                    INSERT INTO album_artists (album_id, artist_id) VALUES (?, ?)
                                    ON CONFLICT(album_id, artist_id) DO NOTHING
                                    """, (album_id, artist_id)):
                await self.db.commit()
                logger.success(f"Album: '{album_id}' linked to artist: '{artist_id}'")
        except aiosqlite.Error as e:
            logger.error(f"Database Link album - artist Error: {e}")
    
    async def link_song_artist(self, song_id, artist_id):
        if song_id is None or artist_id is None:
            logger.error("Database Error: Can't link because Song ID or Artist ID is missing")
            return
        try:
            async with self.db.execute("""
                                    INSERT INTO song_artists (song_id, artist_id) VALUES (?, ?)
                                    ON CONFLICT(song_id, artist_id) DO NOTHING
                                    """, (song_id, artist_id)):
                await self.db.commit()
                logger.success(f"Song: '{song_id}' linked to artist: '{artist_id}'")
        except aiosqlite.Error as e:
            logger.error(f"Database Link song - artist Error: {e}")

    async def get_playlists(self, callback)->list[dict]:
        """fetch playlst form database

        Args:
            callback (function): function that called once fetching done
            

        Returns:
            list[dict]: data = {
                        'id': ,
                        'title': ,
                        'description': ,
                        'cover_art': 
                    }
        """
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT id, name, description, cover_art FROM playlists") as cursor:
                playlists = await cursor.fetchall()
                playlists_data = list()
                for playlist in playlists:
                    data = {
                        'id': playlist[0],
                        'title': playlist[1],
                        'description': playlist[2],
                        'cover_art': playlist[3]
                    }
                    playlists_data.append(data)
                    
                if callback:
                    await callback(playlists_data)
                #     callback(playlists)
                return playlists_data
                    
        except aiosqlite.Error as e:
                logger.error(f"Database Error: {e}")
                
    async def get_song(self, song_id: str, callback = None) -> dict:
        """
        Retrieve song details including album, genre, and artists.
        Returns a dictionary with song data or `None` if not found.
        """
        query = """
            SELECT 
                songs.id AS song_id,
                songs.title AS song_title,
                songs.album_id,
                albums.name AS album_name,
                songs.genre_id,
                genres.name AS genre_name,
                songs.duration,
                artists.id AS artist_id,
                artists.name AS artist_name
            FROM 
                songs
            LEFT JOIN 
                albums ON songs.album_id = albums.id
            LEFT JOIN 
                genres ON songs.genre_id = genres.id
            LEFT JOIN 
                song_artists ON songs.id = song_artists.song_id
            LEFT JOIN 
                artists ON song_artists.artist_id = artists.id
            WHERE 
                songs.id = ?;
        """

        async with self.db.execute(query, (song_id,)) as cursor:
            rows = await cursor.fetchall()

            if not rows:
                logger.error(f"Song not found: {song_id}")
                return None  # Song not found

            # Initialize song data structure
            song_data = {
                "videoId": rows[0][0],
                "title": rows[0][1],
                "album": {
                    'id': rows[0][2],
                    'name': rows[0][3]
                },
                "genre_id": rows[0][4],
                "genre_name": rows[0][5],
                "duration": seconds_to_duration(rows[0][6]),
                "artists": []
            }

            logger.debug(rows)
            # Add artists (handle duplicates if any)
            seen_artists = set()  # To avoid duplicate artists
            for row in rows:
                artist_id = row[7]
                artist_name = row[8]
                if artist_id and artist_name and artist_id not in seen_artists:
                    song_data["artists"].append({
                        "id": artist_id,
                        "name": artist_name
                    })
                    seen_artists.add(artist_id)
            if callback:
                await callback(song_data)
            return song_data
    
    async def get_local_song(self, song_id: str, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM local_songs WHERE id = ?", (song_id,)) as cursor:
                song = await cursor.fetchone()
                if song:
                    song_data = {
                        "videoId": song[0],
                        "title": song[1],
                        "album": song[2],
                        "artists": song[3],
                        "duration_sec": song[4],
                        "duration":seconds_to_duration(song[4])
                    }
                    if callback:
                        await callback(song_data)
                    return song_data
                else:
                    logger.error(f"Song not found: {song_id}")
                    return None
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
                        
    async def get_playlist_songs(self, playlist_id, callback = None):
        """retrive song_id and position of a playlist
        Example:
            

        Args:
            playlist_id (str): playlist id whose song to be retrieve
            callback (function, optional): a function that is called when retrive done. Defaults to None.

        Returns:
            list(tuple): [(playlist_id, song_id, pos)]
        """
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM playlist_songs WHERE playlist_id = ?", (playlist_id, )) as cursor:
                logger.success(f"Playlist: '{playlist_id}' songs fetched")
                songs = await cursor.fetchall()
                if callback:
                    await callback(songs)
                return songs
                #     callback(songs)
        except aiosqlite.Error as e:
                logger.error(f"Database Error: {e}")   
                
    async def get_playlist_info(self, playlist_id, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)) as cursor:
                playlist = await cursor.fetchone()
                if playlist:
                    logger.success(f"Playlist: '{playlist_id}' info fetched")
                    playlist = {
                        "id": playlist[0],
                        "title": playlist[1],
                        "description": playlist[2],
                        "cover_art": playlist[3]
                    }
                    if callback:
                        await callback(playlist)
                    return playlist
                else:
                    logger.error(f"Playlist: '{playlist_id}' not found")
                    return None
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def get_album_songs(self, album_id, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT album_id, id FROM songs WHERE album_id = ?", (album_id,)) as cursor:
                songs = await cursor.fetchall()
                if callback:
                    await callback(songs)
                return songs
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def get_local_directories(self, callback = None)->list[dict]:
        """return directory in form of lis of dict

        Args:
            callback (function, optional): call when done. Defaults to None.

        Returns:
            list[dict]: data = {
                        "id": directory[0],
                        "path": directory[1]
                    }
        """
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM local_directories") as cursor:
                directories = await cursor.fetchall()
                directory_data = list()
                for directory in directories:
                    data = {
                        "id": directory[0],
                        "path": directory[1]
                    }
                    directory_data.append(data)
                if callback:
                    await callback(directory_data)
                return directories
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def get_album_info(self, album_id, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM albums WHERE id = ?", (album_id, )) as cursor:
                album = await cursor.fetchone()
                if callback:
                    await callback(album)
                return album
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def get_liked_albums(self, callback = None)->list[dict]:
        """fetch albums form database

        Args:
            callback (function, optional): function that will be called after the fetching. Defaults to None.

        Returns:
            list[dict]: data = {
                        "id":,
                        "name":
                    }
        """
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute(
            "SELECT liked_albums.album_id, albums.name "
            "FROM liked_albums "
            "LEFT JOIN albums ON liked_albums.album_id = albums.id"
        ) as cursor:
                albums = await cursor.fetchall()
                albums_data = list()
                for album in albums:
                    data = {
                        "id": album[0],
                        "name": album[1]
                    }
                    albums_data.append(data)
                if callback:
                    await callback(albums_data)
                return albums_data
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
        
    async def get_artist_info(self, album_id: str, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM artists where id = ?", (album_id, )) as cursor: 
                result = await cursor.fetchone()
                if callback:
                    await callback(result)
                return result
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
        
    async def get_liked_artists(self, callback = None)->list[dict]:
        """fetch artists form database

        Args:
            callback (function, optional): function that will be called after the fetching. Defaults to None.

        Returns:
            list[dict]: data = {
                        "id":,
                        "name":
                    }
        """
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute(
            "SELECT liked_artists.artist_id, artists.name "
            "FROM liked_artists "
            "LEFT JOIN artists ON liked_artists.artist_id = artists.id"
        ) as cursor:
                artists = await cursor.fetchall()
                artists_data = list()
                for artist in artists:
                    data = {
                        "id": artist[0],
                        "name": artist[1]
                    }
                    artists_data.append(data)
                if callback:
                    await callback(artists_data)
                return artists_data
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
        
    async def get_total_play_duration(self, callback=None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT SUM(play_duration) FROM play_history") as cursor:
                total_duration = await cursor.fetchone()
                if isinstance(total_duration, tuple):
                    total_duration = total_duration[0]
                if callback:
                    asyncio.create_task(callback(total_duration))
                return total_duration
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return 0
    
    async def get_unique_total_played_songs(self, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT COUNT(DISTINCT song_id) FROM play_history") as cursor:
                unique_songs = await cursor.fetchone()
                if isinstance(unique_songs, tuple):
                    unique_songs = unique_songs[0]
                if callback:
                    await callback(unique_songs)
                return unique_songs
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def get_total_artists_played(self, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("""
                SELECT COUNT(DISTINCT sa.artist_id) AS total_distinct_artists
                FROM play_history p
                JOIN song_artists sa ON p.song_id = sa.song_id;                    
                """) as cursor:
                total_artist = await cursor.fetchone()
                if isinstance(total_artist, tuple):
                    total_artist = total_artist[0]
                if callback:
                    asyncio.create_task(callback(total_artist))
                return total_artist
            
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
        
    async def get_total_playlist_played(self, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("""
                SELECT COUNT(DISTINCT playlist_id) AS total_distinct_playlists
                FROM playlist_history;
                """) as cursor:
                total_playlist = await cursor.fetchone()
                if isinstance(total_playlist, tuple):
                    total_playlist = total_playlist[0]
                if callback:
                    asyncio.create_task(callback(total_playlist))
                return total_playlist
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def get_total_liked_songs(self, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT COUNT(*) FROM liked_songs") as cursor:
                total_liked_songs = await cursor.fetchone()
                if isinstance(total_liked_songs, tuple):
                    total_liked_songs = total_liked_songs[0]
                if callback:
                    asyncio.create_task(callback(total_liked_songs))
                return total_liked_songs
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def get_total_full_album_history(self, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT COUNT(*) FROM full_album_history") as cursor:
                total_full_album_history = await cursor.fetchone()
                if isinstance(total_full_album_history, tuple):
                    total_full_album_history = total_full_album_history[0]
                if callback:
                    asyncio.create_task(callback(total_full_album_history))
                return total_full_album_history
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
        
    async def get_top_songs(self, sql_interval: str, limit: int = 10, callback=None) -> list[dict]:
        """
        Fetch the top X songs based on the number of plays for a given time period.

        :param sql_interval: SQL interval string (e.g., '24 hours', '7 days', '1 month', 'all').
        :param limit: Number of top songs to return (default is 10).
        :param callback: Optional callback function to process the results asynchronously.
        :return: A list of dictionaries containing song IDs and play counts.
        """
        if self.db is None:
            await self._connect_db()
        
        # Define the time filter based on the sql_interval
        if sql_interval.lower() == "all":
            time_filter = "1=1"  # No filter, include all records
        else:
            if not sql_interval.startswith("-"):
                sql_interval = f"-{sql_interval}"
            time_filter = f"played_at >= datetime('now', '{sql_interval}')"

        # Construct the SQL query
        query = f"""
            SELECT song_id, 
                COUNT(song_id) AS play_count,
                file_path
            FROM play_history
            WHERE {time_filter}
            GROUP BY song_id
            ORDER BY play_count DESC
            LIMIT ?;
        """

        # Execute the query using aiosqlite
        try:
            async with self.db.execute(query, (limit,)) as cursor:
                results = await cursor.fetchall()
                results = [{"id": row[0], "play_count": row[1], "file_path": row[2]} for row in results]

                # Call the callback if provided
                if callback:
                    asyncio.create_task(callback(results))

                # Return the results as a list of dictionaries
                return results
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return []
        
    async def get_top_artists(self, sql_interval: str, limit: int = 10, callback=None) -> list[dict]:
        """
        Fetch the top X artists based on the number of plays for a given time period.

        :param sql_interval: SQL interval string (e.g., '24 hours', '7 days', '1 month', 'all').
        :param limit: Number of top artists to return (default is 10).
        :param callback: Optional callback function to process the results asynchronously.
        :return: A list of dictionaries containing artist IDs and play counts.
        """
        if self.db is None:
            await self._connect_db()

        # Define the time filter based on the sql_interval
        if sql_interval.lower() == "all":
            time_filter = "1=1"  # No filter, include all records
        else:
            if not sql_interval.startswith("-"):
                sql_interval = f"-{sql_interval}"
            time_filter = f"played_at >= datetime('now', '{sql_interval}')"

        # Construct the SQL query
        query = f"""
            SELECT sa.artist_id,
                COUNT(sa.artist_id) AS play_count
            FROM play_history ph
            JOIN song_artists sa ON ph.song_id = sa.song_id
            WHERE {time_filter}
            GROUP BY sa.artist_id
            ORDER BY play_count DESC
            LIMIT ?;
        """

        # Execute the query using aiosqlite
        try:
            async with self.db.execute(query, (limit, )) as cursor:
                results = await cursor.fetchall()
                results = [{"id": row[0], "play_count": row[1]} for row in results]

                # Call the callback if provided
                if callback:
                    asyncio.create_task(callback(results))

                # Return the results as a list of dictionaries
                return results
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return []

    async def get_top_albums(self, sql_interval: str, limit: int = 10, callback=None) -> list[dict]:
        """
        Fetch the top X albums based on the number of plays for a given time period.

        :param sql_interval: SQL interval string (e.g., '24 hours', '7 days', '1 month', 'all').
        :param limit: Number of top artists to return (default is 10).
        :param callback: Optional callback function to process the results asynchronously.
        :return: A list of dictionaries containing artist IDs and play counts.
        """
        if self.db is None:
            await self._connect_db()

        # Define the time filter based on the sql_interval
        if sql_interval.lower() == "all":
            time_filter = "1=1"  # No filter, include all records
        else:
            if not sql_interval.startswith("-"):
                sql_interval = f"-{sql_interval}"
            time_filter = f"played_at >= datetime('now', '{sql_interval}')"

        # Construct the SQL query
        query = f"""
            SELECT songs.album_id,
                COUNT(songs.album_id) AS play_count
            FROM play_history ph
            JOIN songs ON ph.song_id = songs.id
            WHERE {time_filter}
            GROUP BY songs.album_id
            ORDER BY play_count DESC
            LIMIT ?;
        """

        # Execute the query using aiosqlite
        try:
            async with self.db.execute(query, (limit, )) as cursor:
                results = await cursor.fetchall()
                results = [{"id": row[0], "play_count": row[1]} for row in results]

                # Call the callback if provided
                if callback:
                    asyncio.create_task(callback(results))

                # Return the results as a list of dictionaries
                return results
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return []
        
    async def get_queue_songs(self, callback = None):
        """
        return list of dict with keys id, position and pass results to callback if available
        """
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM queue") as cursor:
                results = await cursor.fetchall()
                queues = list()
                for result in results:
                    data = {
                        "id": result[0],
                        "position": result[1],
                        "path": result[2]
                    }
                    queues.append(data)
                if callback:
                    asyncio.create_task(callback(queues))
                return queues
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
    async def clear_queue_songs(self):
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("DELETE FROM queue") as cursor:
                await self.db.commit()
                logger.success("Queue cleared")
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            
        
    async def check_liked_album(self, album_id)->bool:
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM liked_albums WHERE album_id = ?", (album_id,)) as cursor:
                result = await cursor.fetchone()
                return result is not None
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return False
    
    async def check_playlist(self, playlist_id)->bool:
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)) as cursor:
                result = await cursor.fetchone()
                return result is not None
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return False
        
    async def check_liked_artist(self, artist_id)->bool:
        if self.db is None:
            await self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM liked_artists WHERE artist_id = ?", (artist_id,)) as cursor:
                result = await cursor.fetchone()
                return result is not None
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return False
        
    async def check_liked_song(self, song_id, callback = None):
        if self.db is None:
            self._connect_db()
        try:
            async with self.db.execute("SELECT * FROM liked_songs WHERE song_id = ?", (song_id, )) as cursor:
                result = await cursor.fetchone()
                return result is not None
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
            return False
        
    async def get_recent_songs(self, limit: int = 1, callback = None):
        if self.db is None:
            await self._connect_db()
        try:
            query = f"SELECT song_id FROM play_history ORDER BY played_at DESC LIMIT {limit}"
            async with self.db.execute(query) as cursor:
                result = await cursor.fetchone()
                if isinstance(result, tuple):
                    result = result[0]
                song_data = await self.get_song(result, callback)
                return song_data
        except aiosqlite.Error as e:
            logger.error(f"Database Error: {e}")
                        
    async def close(self):
        if self.db:
            # Commit any pending changes to the database
            await self.db.commit()
            # for task in asyncio.all_tasks():
            #     if task is not asyncio.current_task():
            #         task.cancel()
            # Now it's safe to close the database connection
            await self.db.close()
            logger.debug("Database connection closed")
        else:
            logger.debug("No active database connection: ")
            
    def _normalize_string(self, text: str) -> str:
        return text.encode('utf-8', errors='ignore').decode('utf-8')
            

tracks = [
        {
            "videoId": "xBnc7zN3vLA",
            "title": "Tapa Tini (From \"Belashuru\")",
            "artists": [
                {
                    "name": "Upali Chatterjee, Iman Chakraborty , & Ananya (Khnyada) Bhattacharjee",
                    "id": None
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/xBnc7zN3vLA/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3mWFa24wa3ckrWbo6PIQgolZYbILg",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:29",
            "duration_seconds": 209,
            "feedbackTokens": {
                "add": "AB9zfpKHPHQS4JnFKptOFk3SOkePfdkD0fSWgokZ6U6yG-IEoM5VVwXmS9Wm7si28dxbIONJt8fla0I0eUUe6HlZAejyS_jxvjiZOFG2_9yWXm2PdqL1L5s",
                "remove": "AB9zfpLCtjT9X1wHql6gv6YBYeV-m6mpVxn6KM-DHgMtBPkxY24jyL-Z8j03Nbhy8vBoTXXtjVvuxE0wjSv6GJ9REMQpng8_hj5m9NSBMbORU2cgNZYaRwg"
            }
        },
        {
            "videoId": "1u5rOtZTuuM",
            "title": "Majhi",
            "artists": [
                {
                    "name": "Ananya Chakraborty",
                    "id": "UC-OAcIA0SLrgBuCIxpcLK5g"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/1u5rOtZTuuM/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3m8R5gvetWmE9lQ0lI9I0BHXSmF2A",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:00",
            "duration_seconds": 240,
            "feedbackTokens": {
                "add": "AB9zfpLQp-lgxwNVJvWrtO9L7rg8R1pPR7VHWyZGkff9GspFvMMOR6kXzGNE_KWlBH9B7Il1f5bju2uCvU3D3uL5PwLpak70DEgRLzv-yfzF1zN--0BmHqs",
                "remove": "AB9zfpJFlM3ve69R4BYYLpvXxKv-GtQP0DP-wsRy7il85QJi7_IhsG4ozjQ_lL50FdPvpTZh_8yZHAmvoVntFBQ53i-f18265IP4fJj4E-UCy2WsJE9d5hA"
            }
        },
        {
            "videoId": "HjedoiiBN2s",
            "title": "Arijit Singh Live",
            "artists": [
                {
                    "name": "Arijit Singh",
                    "id": "UCDxKh1gFWeYsqePvgVzmPoQ"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/HjedoiiBN2s/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3lYbUEGoYESxcRdOoeArMZ_DmFyCQ",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:36",
            "duration_seconds": 276,
            "feedbackTokens": {
                "add": "AB9zfpKXU31F9VDTH4MPzJJ4KoskgHtPvXR9FXtNre8o6AvLbq2UfWXE_QE9ToF2M5UAYTqJR84sKH-MLhnAU0x4k9CeHoCy6cNx8Hfz6WJyhcorOOSqE0s",
                "remove": "AB9zfpLkYX_WwuPl9W6yA3KeJhTpRcsdYGHZ7LsPBZjDlSRb7sXCfvNluObIjA2xCfXDZgV6i1xBrJmfukvj7x-GYOXW14Z0iiaIJ4zt-NTHr1AYwuGJBjw"
            }
        },
        {
            "videoId": "0ZsK_1YmOKg",
            "title": "Rater Akashe Jemon Chader Alo |    | Trending |official  | ZaMaN | HD Halim | 2022",
            "artists": [
                {
                    "name": "Channel Mix ZaMaN",
                    "id": "UCXKz-D0EfvFGIzzW4T-ZCHw"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/0ZsK_1YmOKg/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3nO_BzxLxGlzimvjL0AZR_jHBvGAA",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "5:14",
            "duration_seconds": 314,
            "feedbackTokens": {
                "add": "AB9zfpJbSvYEqJIa33pxA-zqFmy0DZ5Oxc_Vt9pK_yvPwqGZ5Wgb4w_oA-oBvqpiXO-Dmicl5FsM6aAxWCAGvggZ-q4xqUPXhNalAwnQPJnQ1_FFdIAZrrc",
                "remove": "AB9zfpKC4F_RcyL7mcwY2YI0f18xrCk37R99q_gK1LcZxOA7FV0b0ijJdug-qE60uaIPytcMCWCQVPo_-2uSrEZ0rHvnbdJ_rAyxLDXF7956fySvnvLObtk"
            }
        },
        {
            "videoId": "koJ1JjAw_jc",
            "title": "Oboseshe",
            "artists": [
                {
                    "name": "Arijit Singh",
                    "id": "UCDxKh1gFWeYsqePvgVzmPoQ"
                }
            ],
            "album": {
                "name": "Oboseshe - Kishmish",
                "id": "MPREb_K0GxmESsrq0"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/VgThFKdsFIz1sb1IXbwKS8xJCAqTYdiPCamAW8IDfff8Kb2xOBfXYt0i0TrTjZmjPOHy8YP3QQhzH5Yk=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/VgThFKdsFIz1sb1IXbwKS8xJCAqTYdiPCamAW8IDfff8Kb2xOBfXYt0i0TrTjZmjPOHy8YP3QQhzH5Yk=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:36",
            "duration_seconds": 216,
            "feedbackTokens": {
                "add": "AB9zfpKib-C-8rCxKMxKY01uQEAQBKul941hJKyz5SRiX7lLbaYOYZBTJnzJtB-ygpobv5dDOWhtuAf9UwDgpgLf9qpGWGwSiuwLiWWVa5w_C8jVVHRfcxk",
                "remove": "AB9zfpJojgXhTmgZ5a9nR8hvutsVkXe1x2EOh65KINwyoMOUG5lHJ_zoXQz8QOl5_nhGFSflMW59MWMHBAMPA6f2agH7ZOxxPVHGaEUl67KFqDgpWAo0Kec"
            }
        },
        {
            "videoId": "a9P8FRmci0M",
            "title": "Mukti Dao (From \"Kacher Manush\")",
            "artists": [
                {
                    "name": "Sonu Nigam",
                    "id": "UCsC4u-BJAd4OX1hJXtwXSOQ"
                }
            ],
            "album": {
                "name": "Mukti Dao (From \"Kacher Manush\")",
                "id": "MPREb_Wzw5Uisbb6Y"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/mSClam0rlf04YASvPtw3lrdAx6w3Q4eDy4rT8SaDHpwseYPmyTQLbd1Yp4eZqVYEsseIM0bJMUMXFeed=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/mSClam0rlf04YASvPtw3lrdAx6w3Q4eDy4rT8SaDHpwseYPmyTQLbd1Yp4eZqVYEsseIM0bJMUMXFeed=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "4:08",
            "duration_seconds": 248,
            "feedbackTokens": {
                "add": "AB9zfpJ8k1mzQZ9_qSt0x1mA3aclDbr79wpg3hihtjT2ZfFNus_1fBQWrGLF2ELcS0fUUavdGLnuoTgrey5l9qkZ7xbwdTziaO-4llGXtdgLmJHAUXTuIms",
                "remove": "AB9zfpL746KPI8Xph-nvlNbMlw2vZyJT4y-5sevZycvT6aM1Nbn2DfH4sRrpCCryjyKiNEt2SXLL3ePPsmzqn4J5hMc7T2c9guSJpnNY-YHX35u0B9fgfdE"
            }
        },
        {
            "videoId": "MuZb2HmfOhM",
            "title": "Ga Chhunye Bolchhi",
            "artists": [
                {
                    "name": "Anupam Roy",
                    "id": "UCahH3l5sz429SqebyK5ZCbA"
                }
            ],
            "album": {
                "name": "Ga Chhunye Bolchhi",
                "id": "MPREb_C5CCrXy2uZL"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/byelGs-xexuPvnPcRci4DgxYuL27qWYmxcyXl-6pYK_ma60K2-6dK8RkrSTOiQa_irclhHxK-AwtzDs8lw=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/byelGs-xexuPvnPcRci4DgxYuL27qWYmxcyXl-6pYK_ma60K2-6dK8RkrSTOiQa_irclhHxK-AwtzDs8lw=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:50",
            "duration_seconds": 230,
            "feedbackTokens": {
                "add": "AB9zfpIJS5al5ocgG3D1agb28HjN1NSmqeClS74qqSemZXq5uGik_S_er2o5NTfvJmQOnItr_-KLkiMxpPRQhLNcy_1cXYnOpLJMLBQjmJX2_jN23ofmg5s",
                "remove": "AB9zfpL-HNGkaIRTMiUUfzdqlypOGwSK8w0V9igSbI0EvjBDPUHwqjI_qF3rhnGvhV827W-izUPNLrNB8ZGh2bFLWJGTP8hbGe_YDe354kZ9cEGtRCKhOBY"
            }
        },
        {
            "videoId": "1kgHdX3E_30",
            "title": "Bala Nacho To Dekhi",
            "artists": [
                {
                    "name": "Iman Chakraborty ",
                    "id": "UCi4oP4G27_lg1K1avCIZ7vw"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/1kgHdX3E_30/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3kEa75lBZV_Y8LnTYX7hP-4kJj0Yg",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:26",
            "duration_seconds": 266,
            "feedbackTokens": {
                "add": "AB9zfpKUh8lVouAKornGc9AAmbVHZsF-ea6m-pNz1yq2K1XzFqf-Wq_EBsE6M25-SaQ06v0xww_EYZohsmpe9V3b4tyXPAfkTsNc8aH4weVw9SQqG6tzjXA",
                "remove": "AB9zfpIUxyMbo8xJYRQ1T7SmtLmKwj538H2QK0PX0pRm_N_fMPVN_ceePnvkt7QmxV_GyorWfrJ0LOBLbQg_WIDQKfRNuTWHCEy-UDqaLuDx2aDgMWmCNTw"
            }
        },
        {
            "videoId": "ReBHEyAd2zk",
            "title": "Dekhechhi Rupshagore ( ) | Mahtim Shakib | Arindom | Ditipriya,Dibyojyoti | SVF Music",
            "artists": [
                {
                    "name": "SVF Music",
                    "id": "UCCPPUrQOQ12l9Xr-B7A351Q"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/ReBHEyAd2zk/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3mSoPPbS0ivgEAQl1gEVshvYrexgg",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_UGC",
            "views": None,
            "duration": "4:05",
            "duration_seconds": 245,
            "feedbackTokens": {
                "add": "AB9zfpL0G8AzhvpJbZvc5Tr3aiBTaiDmblrGjW7kBSzSeG_I-4AXKCtk7vwe5iKBf87jh9ruzrWgMxCfgoPsiRiPPjXPc83-Bw7Dsmdi2-SqTaepWuxr-8s",
                "remove": "AB9zfpI24qzM-FyWfhrHzU1kQ3TR1zO7TCjGU15XNs8mxpOrPW0FyepX2gxZoCR4QDM0ZJPWzn4W5Lsh3xBcKsc3TT4KWYKdXGf2_VRoxSdHgPFB70twQRM"
            }
        },
        {
            "videoId": "XuzTFgEvJ7U",
            "title": "O Mon Re (  )| SVF |Yash & Madhumita |@TanveerEvan|@PiranKhan|Baba Yadav |@SVFMusic",
            "artists": [
                {
                    "name": "SVF",
                    "id": "UC2GXNqco-k7fwg2SMM6SAzQ"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/XuzTFgEvJ7U/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3lxSIKiPDDcVdCT31RdoM3dKNfZZw",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_UGC",
            "views": None,
            "duration": "4:03",
            "duration_seconds": 243,
            "feedbackTokens": {
                "add": "AB9zfpKARuwgCYEbOBi94LVW2OEt5eEtQJC58pCDvQVPBKJDphQNMBqOel6Wv3TxYK49U_IMOFzOyxmGIdSNmd2gxOJ28-C9_Yghr4wfHZxAkAB4KWZTvyA",
                "remove": "AB9zfpLiEtmJorAI1-Yn8vtsRMS4itDp8RK3ST_IrMUuHfPhkzF7i_hkvyJtOYqR9YsJeIZY2Ak43YBleeDMno6hHwh9yIT1VnTzs9UCitAhszAfJdFSQbU"
            }
        },
        {
            "videoId": "C7vPBFL4gx0",
            "title": "Hoyto Konodin (Reprise Version)",
            "artists": [
                {
                    "name": "Keshab Dey",
                    "id": "UCb8extn0Yrkn2jXzsAi0EpA"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/C7vPBFL4gx0/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3koPvmCJ03Wj5zVFNiySy5kTjNjKQ",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:33",
            "duration_seconds": 273,
            "feedbackTokens": {
                "add": "AB9zfpL36rvS0o1N6wI9Zpu5sOYO_rEzKMn_Q2JTrIxEx5fOyGKShGkBs7ghHk-3G5IZURSV0H-__pMH40Hup62YueS_q1deKAAtzN-UP3wxQ0axizSmbj4",
                "remove": "AB9zfpI0TJ6oufrMI_pQzi2cox-EHuJgDZkO7QilMv__2sk2U2NyFTSBKlJmnKbvAZnHRSjzFe4Et1eLZydXoaJkcUbPLb2pRK8AWRumeY-mZhi_J6B_JQA"
            }
        },
        {
            "videoId": "n8lq7tF40jk",
            "title": "Behaya (From Ekannoborti)",
            "artists": [
                {
                    "name": "Lagnajita Chakraborty",
                    "id": "UC_SRoFis3KY1V3P_3ljMjKA"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/n8lq7tF40jk/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3luRkV5s5nFGax0sYOFTRylGYL1HQ",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:42",
            "duration_seconds": 222,
            "feedbackTokens": {
                "add": "AB9zfpJ1AYJSwNQ6GIeraorZgBgZxaQ4iz5tTFNseXk0mHINk55aM8k3VJHGIpKOXhnHkd8HU1WQW3Vpw63J22jMC5v52OW9du5m1MGnPl2i-STA-iigG9U",
                "remove": "AB9zfpLnHSB6DXODo3A1xj8OWOkyyvlEkEfMg0xE5VWNQSv23SlcqKrDYcJwL0tB901GYHho32G5bK-zM7sugHydeVGIXRs10ewku-Q0BnaNKtPhk9HzEXE"
            }
        },
        {
            "videoId": "3bC2suUlS3w",
            "title": "Boshonto Bohilo",
            "artists": [
                {
                    "name": "Ankita Bhattacharyya",
                    "id": "UC15i73AdwWZ3ibTMGDPlVbw"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/3bC2suUlS3w/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3kGaUvaSOipYv2qv5npy-RjMm3-CQ",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:36",
            "duration_seconds": 216,
            "feedbackTokens": {
                "add": "AB9zfpImQBlz6q43gxqUAE7EioG4WAXnwGFbLDpujHJZ0T6qF2GetwJRhaMLjoZYimQI-wmzQve2WwGF5Qp72yOSOZpPaJN8w-1g5665IGHyyxZyIaPaQos",
                "remove": "AB9zfpISmJtk0s749zSXv8UYiUaImiDO_UkTNOnEtshGSoNzzPvjFqE0etx4w-4G6r90JCvrU6AnpWPVS2EIsOQnqL1GlyrGvSs_SYz_bqFlYxbrV0uOJHw"
            }
        },
        {
            "videoId": "SF89uGTBo-o",
            "title": "Phagun Haway Haway (feat. Shovan Ganguly)",
            "artists": [
                {
                    "name": "Ishan Mitra",
                    "id": "UCTEbb_4wyxgNzq9AINZbI1w"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/SF89uGTBo-o/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3kt9gILsG5TqqqgLCQZU6cl1hzH4w",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:02",
            "duration_seconds": 242,
            "feedbackTokens": {
                "add": "AB9zfpLOBSfNk3KjacjNLsytyje9Z6TL_bX8XQ4QK1hP3OOWJO0_ZfyPUhlBpxXYjEJClmoGr8m2oQO3idJPiAGZu-VllzqciX25i6X2KQw6BBfRgBlCG8s",
                "remove": "AB9zfpIOWB40hLqQ4pJq6EkNdIKjcFJj8SP13gTx3uoWqO2LHDqCGEwKSPHAdlRGSJW9NHLgZoXQZhgcy9cMlU0BcOYJq93NMWqP7-oE9NIlleocIH1Q3Y4"
            }
        },
        {
            "videoId": "zjplA5XnacE",
            "title": "Alote Chol",
            "artists": [
                {
                    "name": "Debayan Banerjee",
                    "id": "UCQfbM2wG4PQTz-M5ktNRS1A"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/zjplA5XnacE/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3k59ExJY0WLazogGIVAsUdUaRftQg",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:18",
            "duration_seconds": 258,
            "feedbackTokens": {
                "add": "AB9zfpLPriJ3ww3hNu2Oj4_pczfDq0vY4HjiaPQUwZX6gV1PMn1rVA7QApi-VNwZBbx9qQ-uKjEc85o4Weh79-DVdxIy5VHsRDAEptn9LQZaLQZR75bMyew",
                "remove": "AB9zfpJTV5D5imoZznMMwwxP_Ku70HDDjZqOJ61r1spqGB0ZQJ-SoAVRitTzd-E25OEdNNe1CaHUDNRxBNfQXTjA81Uf3lSZqDy9MPIq_V-gH4C9EeTCMEg"
            }
        },
        {
            "videoId": "UElpQ1D3CkA",
            "title": "Elo Re Pujo Elo",
            "artists": [
                {
                    "name": "Dabbu",
                    "id": "UCAQaCmi3eGGzi5Sd_SuJZig"
                },
                {
                    "name": "Senjuti Das",
                    "id": "UCu8I8k_TRvNGll_sdhflygQ"
                },
                {
                    "name": "Nakash Aziz",
                    "id": "UCJyuvJidXavwjscKBny5TMg"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/UElpQ1D3CkA/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3kbatKMhdqkuDwR2n_efsmExXIMTg",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:10",
            "duration_seconds": 190,
            "feedbackTokens": {
                "add": "AB9zfpKAT1j5a4KvmTN3oKu22rHFyraQmswlZy-qtg2weqip0H138Zfwxs8YmdHOlnerfDYEtPfFpiffHWAojAtuOvmHuAPzfTviVLWaSbsmBcG51GCVEZU",
                "remove": "AB9zfpKdScntzKJnL12vedJ7GTGxr2jbsofA7mxbrkLHGVG2l0qDOww4tzpKXw0KI-nXSABCeGSfyO9Y3AR9yB_2bOHwNj_YYy3Jaxj-l3lbpbRAsoB_Gq4"
            }
        },
        {
            "videoId": "ojOKJR3vIAg",
            "title": "O Boudi 2",
            "artists": [
                {
                    "name": "Sourav Maharaj",
                    "id": "UC3Kc1RGcGxiaBgayOVjD9aA"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/ojOKJR3vIAg/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3lnhN64_BNOzViR1-IFLtRgl2zT7g",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:09",
            "duration_seconds": 189,
            "feedbackTokens": {
                "add": "AB9zfpLv1I3oFe2slWRQIU4PcLOobAxTvUnlpm4k3raykb-y_IyvBYkdBbgH7POl-1ox70RPqIWU5W4dF3aoMDm_xxHGfnuZUk77FXLQvcqICY6ehIR4Cqs",
                "remove": "AB9zfpKWYrBkJj-haUNbJjJ4Vy8sbg_hLP66pqB4s_ZfN41UtDxJp5RokBoUQdZB2oLPruGeiF_dyEbe1VW_MjR-snl2TEc7GBhXDq2xvWjhztjnnmPYbo4"
            }
        },
        {
            "videoId": "10UJYSvAlzk",
            "title": "YOU ARE MY LOVE | RAAVAN | JEET | LAHOMA | ASH KING | IMRAN SARDHARIYA | THE RED KETTLE",
            "artists": [
                {
                    "name": "Grassroot Entertainment",
                    "id": "UC_aUqqh2c9Z7ZTJ2CYmoE3g"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/10UJYSvAlzk/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3kT9-aCBnC7cGl8q2IWJVjKAj1upA",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_UGC",
            "views": None,
            "duration": "3:58",
            "duration_seconds": 238,
            "feedbackTokens": {
                "add": "AB9zfpKdMeQx6q_ImJTrpaEgbO-3_ys6z2CVRHcBh0VF4UYIzncYtnCHBFC9VnppVaIJftm-SRFW3C-239V68yxNCKyWJDhJ5OubkqZ4pCi1ZVb4_92laSs",
                "remove": "AB9zfpJP_8cl0WBa4UviZp2iK7bn1qSjCKEzNNajWOzF0lQK3RiyrTyl6gVfztX7ZY_0CGf-rvTbP2dA26AGZf6o84ZAl8EywXuFKoxqz5Nrmy3JzUwzDbc"
            }
        },
        {
            "videoId": "DHUcbC0k0W4",
            "title": "Sathi Ato Valobasa Tumi Dile Amay",
            "artists": [
                {
                    "name": "Ariyoshi Synthia",
                    "id": "UCht4SrJNRoE6HAX-2bXOxUg"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/DHUcbC0k0W4/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3lB_MW12JdK_pZyBILKNHxmcYdIQQ",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:06",
            "duration_seconds": 186,
            "feedbackTokens": {
                "add": "AB9zfpKnUQsiNZn6wIZoY4b34zXyQwH0PL6g4Imvg4tOwdgyCrbL9b3ZsL-a-DKuA18hzDiZDmydiBu6TpPpBpV7HZ-5YwfG0gf_CpbpvQy4wIhd1AZH2fU",
                "remove": "AB9zfpLINHj16ittQzXfOsVflcV5lat7EeVVgHvTiFHhIFO5FvoSOKmAMrU2Y5HbfxuzeQgRUyPQscIqVNYSKl46xCj7sDLbwDSKAd8Jj8HWTnTN07HKDqo"
            }
        },
        {
            "videoId": "s8jKpLeE5q4",
            "title": "Bhalobashar Morshum (Duet) (From X=Prem) (Original Motion Picture Soundtrack)",
            "artists": [
                {
                    "name": "Shreya Ghoshal",
                    "id": "UCrC-7fsdTCYeaRBpwA6j-Eg"
                },
                {
                    "name": "Arijit Singh",
                    "id": "UCDxKh1gFWeYsqePvgVzmPoQ"
                },
                {
                    "name": "Saptak Sanai Das",
                    "id": "UCLwNkO8S8dXr2P7Dw0gKX4w"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/s8jKpLeE5q4/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3lZxjo7YKHGtJTNVbilOnWWVajoLw",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:17",
            "duration_seconds": 257,
            "feedbackTokens": {
                "add": "AB9zfpJicDahwO8TB1Dr0D75rg-zIoZK4kGitnmHnp7clTL117__VtVTRbb9JVrqNXLDgT0NYjYSfCBBb7RCDFpUSUaMqwo2wKsWuqZ96ecZzN_ffg5_Cy4",
                "remove": "AB9zfpJ2YMyBn1PQEehAK87pqxB0As-YgvspcW5g2Fa_g9GTAJ2S8gY3xyZY0FGFKAymHX2AFvcR4sRrFfqleHzTTHbgXBXDNzZ56yfV3FP0yGmpupa4UAU"
            }
        },
        {
            "videoId": "iT4Lo-xkWao",
            "title": "Amake Nao",
            "artists": [
                {
                    "name": "Debayan Banerjee",
                    "id": "UCQfbM2wG4PQTz-M5ktNRS1A"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/iT4Lo-xkWao/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3noD2-T1mWsBVUbIfJTQPfdpHEwjg",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "2:59",
            "duration_seconds": 179,
            "feedbackTokens": {
                "add": "AB9zfpIqYv7_PEeq9hCC78mtTrDd_VhKbIT3yNsQVgWZNxqZ16_Wmk9ZBxjdDBT055VvX9YFJ6KlqBPIByo1s4jkoLNW-SAaDNYO4IVXzY2WEnQoFhmPMEg",
                "remove": "AB9zfpL3bPD06o1LA8z6Qd41b2zyJaVqmWAewwBfCtQ23MvqVOmFt_BwWX7brl7UZNMIckNpvAta6FpXCA0NayLTB3joDaeA2QdRKRoCdHW5-KTOnE0GnM4"
            }
        },
        {
            "videoId": "RPf0vW_xTrc",
            "title": "Shohage Adore (From \"Belashuru\")",
            "artists": [
                {
                    "name": "Anupam Roy",
                    "id": "UCahH3l5sz429SqebyK5ZCbA"
                }
            ],
            "album": {
                "name": "Shohage Adore (From \"Belashuru\")",
                "id": "MPREb_Y4R73LTwajx"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/VkSP1XkFGKXV1PxIR44ezAJepg67umVtzLzwdgLziX_cJ9IGmqwIQjOdWJvobsudl7oRzkywGwDsk7M=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/VkSP1XkFGKXV1PxIR44ezAJepg67umVtzLzwdgLziX_cJ9IGmqwIQjOdWJvobsudl7oRzkywGwDsk7M=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "5:34",
            "duration_seconds": 334,
            "feedbackTokens": {
                "add": "AB9zfpLd-_iU5C62kmUt6n9DrLWY3dKPSHliwAFsXn3b8RnqxAMKkyVtT6WeTMux0WOKUxzo_0sf4jA8b3CsnwXJfNmugCT9oAxU3Si1PUhbxYVeo7tulSM",
                "remove": "AB9zfpJHhcM73aFcilkMZgBV_ML-qccuLA3VLXtGQsHjERL-mkta5c4ZQpVm4Ro05FV8lgqk2SUsywKHBgTibM0o4dLHWwwXKS01N1fs9mKsn0b20bjY7O4"
            }
        },
        {
            "videoId": "be02A6ynJLo",
            "title": "Tor Mon Paray",
            "artists": [
                {
                    "name": "Mahdi Sultan",
                    "id": "UC1gd95VhTPjrffc-q3HXn-g"
                }
            ],
            "album": {
                "name": "Tor Mon Paray",
                "id": "MPREb_MrINfeqstlj"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/NiGuXFseB_S0b5gJRGVdBRAIUKWB-WbacIsefw6GpLf7XYeQgZThtMHotcISPlwobcsAdkD0_dsanMrV=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/NiGuXFseB_S0b5gJRGVdBRAIUKWB-WbacIsefw6GpLf7XYeQgZThtMHotcISPlwobcsAdkD0_dsanMrV=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "5:10",
            "duration_seconds": 310,
            "feedbackTokens": {
                "add": "AB9zfpLybz9oKa1abR-NqJjjR0lWykiWgU9-wBwmjvcfvRvhq0noQuwSrzznyAEAdYVvBWRHa4rdAL1Q_UMe2ewRF9325bir0iXk3Y5Xy0IZ96BCrO5aR1Y",
                "remove": "AB9zfpIa2_KN7Kj5mVElr46fUDl9l-gYojTslOVwKEuTVWLqqtF9A5JwMfkECyKqhhBykCW-zMHD8CFXqqpCmseNpDHz1BSqfUzHEmVoCytwuO4ES49tas8"
            }
        },
        {
            "videoId": "MSgBuvLDscM",
            "title": "Tor Bhul Bhangabo Ki Kore Bol | Baazi | Jeet | Mimi | Jeet Gannguli | Jubin Nautiyal | Anshuman P.",
            "artists": [
                {
                    "name": "Grassroot Entertainment",
                    "id": "UC_aUqqh2c9Z7ZTJ2CYmoE3g"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/MSgBuvLDscM/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3lqt8XEN3qtms1IEmVZIwyUG_unfA",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_UGC",
            "views": None,
            "duration": "4:17",
            "duration_seconds": 257,
            "feedbackTokens": {
                "add": "AB9zfpIlVOlpMMHwe7_aGCcbxFaKZBbqiI_b4IoICcfbP-oQrDE0DA7tZKN3tpfY-UiPG1MqWhjsjBywiYJn8HFLzxftqwzAaIZMqRmuBHaAr6eDm9eau_8",
                "remove": "AB9zfpJC2MC946NNQYsxMBHO6qWygrnvJRv-1HyOBFfhgsi69MCXM-ARtW9yxJT_-H5qITFW8X8FURI3cb7-IJ9xD4g2cf9JklawSIBYW3rt2PtPmUkFoVI"
            }
        },
        {
            "videoId": "TEk4RnZW2Xg",
            "title": "Ki Mayay (From \"Belashuru\")",
            "artists": [
                {
                    "name": "Shreya Ghoshal",
                    "id": None
                }
            ],
            "album": {
                "name": "Ki Mayay (From \"Belashuru\")",
                "id": "MPREb_g59QizmfuVg"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/EfmLS21p1_53RF-acb-v1vOsKo3j-my_MEkdLYTFC-XzA3pPmhucI-5z9JjfhNP3eUb57YO6xSPT1Ls=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/EfmLS21p1_53RF-acb-v1vOsKo3j-my_MEkdLYTFC-XzA3pPmhucI-5z9JjfhNP3eUb57YO6xSPT1Ls=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:45",
            "duration_seconds": 225,
            "feedbackTokens": {
                "add": "AB9zfpL2csJP86oP66l2lYVAR_Y0FuUeYUjoKV7Skg3Zb_FOye7TFsSYbzKrFq_7MNCEySO4a81VTFmDlNzsCzlk4yIpgqIs9imtqHlmEfFSOcQmPwwf61M",
                "remove": "AB9zfpKXWrWhtiiSI7yNczRnomxM0LtD0-GLVuzZP_BHEgaGleG3rosXsn7i11i7mSUl_uacCNJrWcITKyE-MG0ZKKdHaCgXRz_XCprfcQZ6l7K3qKSSIys"
            }
        },
        {
            "videoId": "MvWxFlkor9I",
            "title": "Chele Tor Preme Porar Karon, Pt. 1",
            "artists": [
                {
                    "name": "Sumi Shabnam",
                    "id": "UCmyQDk-FRo-lfZtZWCMXjxQ"
                }
            ],
            "album": {
                "name": "Chele Tor Preme Porar Karon",
                "id": "MPREb_VSghyy2fX5m"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/VMz1Z4mrz9soZCjOu5Y2d0z0ESJagaHf0grD-YBe4SSdCpaEx8KeCA8vi4A0x2xOp_A8q69GjghAHwsfXQ=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/VMz1Z4mrz9soZCjOu5Y2d0z0ESJagaHf0grD-YBe4SSdCpaEx8KeCA8vi4A0x2xOp_A8q69GjghAHwsfXQ=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "4:04",
            "duration_seconds": 244,
            "feedbackTokens": {
                "add": "AB9zfpLCNV4RcYukHW2NZLxLU1Cy2z3apmBT6Q0NxUzgo4F9melav5PTQALjqsfpbx3n_O78-w8DkbNQF5fRGbrztB6RkMI2jZCTivJub8DtbEp5wtvv9cE",
                "remove": "AB9zfpIS6ApS3W0ahma_t2fSVfrMrdM0nndsIFRsY5nREEatO36vUZ3O8KsTZwVV-V0jyErsR_JJkMOc3EM4mbRLIlWtRFi4G78SdQKedxK08vt3gxt7pCw"
            }
        },
        {
            "videoId": "DEqoi6eJzBk",
            "title": "Shada Shada Kala Kala (feat. Arfan Mredha Shiblu)",
            "artists": [
                {
                    "name": "Hawa",
                    "id": "UCzTBgaGzlQ_aEJxDPGujX9g"
                }
            ],
            "album": {
                "name": "Shada Shada Kala Kala",
                "id": "MPREb_XKTOgEXMIfq"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/9yW8MLF3RtzJdf0W1kCi6azo4Sc3UpfPcK9-1akb9VAtvJrfHqY2XVHIW07hGECkkFtYMcB1E7o9U0nu=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/9yW8MLF3RtzJdf0W1kCi6azo4Sc3UpfPcK9-1akb9VAtvJrfHqY2XVHIW07hGECkkFtYMcB1E7o9U0nu=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:51",
            "duration_seconds": 231,
            "feedbackTokens": {
                "add": "AB9zfpITYEk9xELfx4kgre3qQIKBQEGtb_kUxOVwQ5kxVhqbc2HrSwuK5CZdLkE_A8CqRqqPxX4YCXkIcdbgCpaFXOpafBKAm5Pelb90dh_OE0MqbemoQYA",
                "remove": "AB9zfpIkIJioEgQjVeB5SE7aTRP-bp_FXRjJJIKRr2m1QtOShV6Jtc4ZOTJDyt7AtTXux2USWZq0OoQis5hFZ5EjdWFqGm6TWou3zuskzGSZ7DUGVkx1F8s"
            }
        },
        {
            "videoId": "AHekyci8lkM",
            "title": "Ekhanei",
            "artists": [
                {
                    "name": "Lagnajita Chakraborty",
                    "id": "UC_SRoFis3KY1V3P_3ljMjKA"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/AHekyci8lkM/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3nZvgsEyl3JRgQ_MNpR4zMp1y18dg",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "4:45",
            "duration_seconds": 285,
            "feedbackTokens": {
                "add": "AB9zfpIS8S3fg8Qgox0XED1_FpWH57fjdHWvn1RqLlCqIAyjMn7_L7syM-jciugU9hwJRechCoble-K98R755cHiywR8ju5uPA1rkPmyndxJ4lSxXyd_MJQ",
                "remove": "AB9zfpIrteu3oZqAgqCGkqToa-zCdzyZ0eYfPGUvfcYa02Hcy9wlH9m8uB2B8DUA1jv3cRNY_gpJp_jiBecU7kH464PBGWWCzRI4ylzdm7Qu5FCVphwvvVw"
            }
        },
        {
            "videoId": "5zTSjLw18LU",
            "title": "De De Pal Tule De",
            "artists": [
                {
                    "name": "Tanmay Kar and Friends",
                    "id": "UC5347Y6esKy5ttXKpsDb7Dw"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/5zTSjLw18LU/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3niB6lIOukUUC5ZDp7mVcHl4xr5dA",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:36",
            "duration_seconds": 216,
            "feedbackTokens": {
                "add": "AB9zfpLjJmoIN4G-xdv9ujaufIyE0nXrhRFpus-ebHXbiRnzfyqNzLBjRjWtifA2caAasLill4GEgPsUcwIhB4xoSFT95joFZ6rCzY5DFuyU6s-N_vsNc6Y",
                "remove": "AB9zfpI_PCfVWEMFBgzjTejr2hX_7uASFfFFMKdAA3dm87xedinUrlgVApSwXUJzjyH9QygPsbLF7vgfC1Cv9jGIRHooyqWITVSbQq8hOJMH3rtQuTRdyl4"
            }
        },
        {
            "videoId": "oRGxiL69yz4",
            "title": "Aajke Raatey ( ) | Bismillah | Subhashree, Riddhi | Arijit Singh | Srijato, ID | SVF Music",
            "artists": [
                {
                    "name": "Arijit Singh",
                    "id": "UCDxKh1gFWeYsqePvgVzmPoQ"
                },
                {
                    "name": "Jeet Gannguli",
                    "id": "UC00SotJE71x-1F3ia2T3cvA"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/oRGxiL69yz4/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3mXxZZZ8R2w08ltDRAK0ne1rm6qMA",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:19",
            "duration_seconds": 199,
            "feedbackTokens": {
                "add": "AB9zfpKikqpe1zIOuEn7IJm9P0hDAkZX7PymAEmf5u3HbidoQiDSaSTQlxccXzmm2XGeghul7qQzYsxKZpVnauwTboFEkf8flFSCLZllzg5_1n62HgJII8M",
                "remove": "AB9zfpLByL-2p6XR-UESR39xYSW_Njid9XqhbCSw8aAQ-fP2AJNog2PYFJt_tw_pCY-Y9eazW8Gp7WVbCNUlY7LNAYjbfIzOlWlCXGkBSR43U0-bWXsm0ok"
            }
        },
        {
            "videoId": "GfgkoWDBIOo",
            "title": "Tumi Amar Hero",
            "artists": [
                {
                    "name": "Anupam Roy",
                    "id": "UCahH3l5sz429SqebyK5ZCbA"
                }
            ],
            "album": {
                "name": "Tumi Amar Hero (From \"Projapati\")",
                "id": "MPREb_JfjGsM0vLeF"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/a__m_Gmh_X44a4pXzyG5ZYVD58PXjUpFNcBh93erawG7K-2Tsd7Mw3OzmTQqrSp6OE4lbnr0mkk9FL9tcQ=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/a__m_Gmh_X44a4pXzyG5ZYVD58PXjUpFNcBh93erawG7K-2Tsd7Mw3OzmTQqrSp6OE4lbnr0mkk9FL9tcQ=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "4:04",
            "duration_seconds": 244,
            "feedbackTokens": {
                "add": "AB9zfpJFA7cIPQ_4CcU_S7QDduuvAPodKCr4kerjHUKioj_z7GXmwl4owlBiHyXQ9_GR_6GxxPKdBqX6DZT0-oSfBpUPalm45sdt1Q-LNwclQcPQ1kFkP88",
                "remove": "AB9zfpJOTZHyiRvXMjl12C0Mu8FjlCOpsicSXS8pBdcwnelb5bZCrnFY4Xl_68td0wd7tH0pMwx_WaXOv6PkQbayBcOT8f8l0jBF5IR09cYB2it1GwMZZLM"
            }
        },
        {
            "videoId": "kcHn-ySADyM",
            "title": "Thakur Jamai | Sneha Btattacharya Ft. Sreetama Baidya | Suraj Nag | Rana, Rohan | Bengali Folk Dance",
            "artists": [
                {
                    "name": "Sneha Bhattacharya",
                    "id": "UCYDEJby721kCiB7S46NclgQ"
                }
            ],
            "album": None,
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://i.ytimg.com/vi/kcHn-ySADyM/sddefault.jpg?sqp=-oaymwEWCJADEOEBIAQqCghqEJQEGHgg6AJIWg&rs=AMzJL3nElLWykVLUYpx9eqzjsKOmPmGFbw",
                    "width": 400,
                    "height": 225
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_OMV",
            "views": None,
            "duration": "3:03",
            "duration_seconds": 183,
            "feedbackTokens": {
                "add": "AB9zfpIAVGWX1h9EwP0kZSu9wSnMxtbG6HsyfvxMGT9wgVQhsZx86MfUzkQ73mZhkppK87c_2Afet2cfMAp7mWmUdZ1MErVh60BGcULxiqviqmx5U1GvHqo",
                "remove": "AB9zfpJsIJTwiacLLCoCl0yvaFiY8bwStI3ru4B8ZeOsOERb_WsxLYQ_5awLjTKOpuvuM9pttgElU4GAqt71tzO0OkQsmze0FANcP_qP0pcG6OZIU3Ybmf4"
            }
        },
        {
            "videoId": "HxtgfIPZPEU",
            "title": "Taka Lage (From \"Kacher Manush\")",
            "artists": [
                {
                    "name": "Nilayan Chatterjee",
                    "id": "UCraeR0yYCDVUjORC26LTiDw"
                },
                {
                    "name": "Pranjal Biswas",
                    "id": "UCOvSqOj32lVxt0PrigkOldg"
                }
            ],
            "album": {
                "name": "Taka Lage (From \"Kacher Manush\")",
                "id": "MPREb_MxPI1kQnEKE"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/XdIyAsWUevSlVBaU1UTuarGnYETSD8hHHdhFdSiTzCGIhNUWBAkQZ1-owf32BMQfCnMVnTtk0ofCJVI4=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/XdIyAsWUevSlVBaU1UTuarGnYETSD8hHHdhFdSiTzCGIhNUWBAkQZ1-owf32BMQfCnMVnTtk0ofCJVI4=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:29",
            "duration_seconds": 209,
            "feedbackTokens": {
                "add": "AB9zfpKBrkCtlkhGcxK-5170dflPzK9Rftpa5YG69TeNK-2mW0JkKDfvyHBvaA8X_39b0YFHKUygpqLMKLJC9st0wLoEjOMtvtvSwogqnQhp3IUR9EPx14M",
                "remove": "AB9zfpJdGztuXyO4kyqypAL3KINrAcWqqUaR7uQhX2XCULiGMxsAcNtBIe-XiIT7dJpfgnqIx1t-4pi_3RkFgOwsSiIZfgYKNaI6AUgJUbRdFrGQX1eO3QU"
            }
        },
        {
            "videoId": "yqL5DQkrv5A",
            "title": "Tui Bolbo Na Tumi",
            "artists": [
                {
                    "name": "Nikhita Gandhi",
                    "id": "UCZ3bAw2GF0A_VVI6uHqMC5g"
                },
                {
                    "name": "Subhadeep Pan",
                    "id": "UCuUiM1RgCWD1uPQJZ2VupfA"
                }
            ],
            "album": {
                "name": "Tui Bolbo Na Tumi - Kishmish",
                "id": "MPREb_5u30Lk0kI3L"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/6xwaR7g8vs23XFD58WYIbr2DMWSOjjLIyNiKbMui6R6_dOWSF5TUTgGxRETsh4DBJvVaE9gvWIJYlEcz=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/6xwaR7g8vs23XFD58WYIbr2DMWSOjjLIyNiKbMui6R6_dOWSF5TUTgGxRETsh4DBJvVaE9gvWIJYlEcz=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:15",
            "duration_seconds": 195,
            "feedbackTokens": {
                "add": "AB9zfpLfmMZ62_nO8xueWfRC2wooN0Gzt3l0QGCHrkOy-ake0DakW8Inlt-oCROQ3GRY11x5PXdoOqx3aZGq0A3Z6tZ6KLuWCnDutNTFCRth_qTjc-lD-oM",
                "remove": "AB9zfpLsUn8Yq28Cm0KQ71DDPHXC8wea-cQkhVw6vcgoIHHYj7beK8ML3mYmffyJGE93x11eF7u6nGN_pIS3q5wt179q_ljWze23RPzeWLnwFpD7flgruXI"
            }
        },
        {
            "videoId": "1b5s20Juk2M",
            "title": "Dustu Projapoti (From \"Rest in Prem 2\")",
            "artists": [
                {
                    "name": "Arob Dey Chowdhuri",
                    "id": "UCJnPimzYTZ8NQgpsMOW-VRg"
                }
            ],
            "album": {
                "name": "Dustu Projapoti (From \"Rest in Prem 2\")",
                "id": "MPREb_iwNZ04d7nCn"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/Jk54XyTh1yL4NVZKNxPjrzbbOQfLuMpf0fpxXW1pmE9q7VbFU9_QmNcerTwRkRifyRkwWjf5XlHWWBM=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/Jk54XyTh1yL4NVZKNxPjrzbbOQfLuMpf0fpxXW1pmE9q7VbFU9_QmNcerTwRkRifyRkwWjf5XlHWWBM=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "2:36",
            "duration_seconds": 156,
            "feedbackTokens": {
                "add": "AB9zfpK9WXm11DlSAJRhYPgL5uh4G8IIau_VCsFyINk87bpywUpnzyS4oA47Ue-1MXCKQfnk9at0u4NxT9r3wy10U95XBgcPgIkz49aICztSvNVKMtBh7uM",
                "remove": "AB9zfpITNdSsiPjlsWN8NgxMHpUzZQQJ5RQqf3AabR2xRnOd6z1h2kX_MGphrJOAukvOz2u20jlEFktxjNHdGe4WRKAJVZsZlPJlgJRvnH9CSRKW_2EmqN0"
            }
        },
        {
            "videoId": "N_IqGUDUNwQ",
            "title": "Amar Dugga Esheche",
            "artists": [
                {
                    "name": "Akriti Kakar",
                    "id": "UC48zN7C674VV7o28O-FIIhw"
                }
            ],
            "album": {
                "name": "Amar Dugga Esheche",
                "id": "MPREb_KdTpLfpXSIy"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/IqZteTNIvW4zT4ueDR1s-SOxEP5pky45udWbXNEogrqDCPrYrj-l3o0GZkodSApmEThcvbv5K-8gwZLx=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/IqZteTNIvW4zT4ueDR1s-SOxEP5pky45udWbXNEogrqDCPrYrj-l3o0GZkodSApmEThcvbv5K-8gwZLx=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:29",
            "duration_seconds": 209,
            "feedbackTokens": {
                "add": "AB9zfpK4281n2uJvpENSU0mgQ9QZi9hzWT4e1ZwWZ1qbvTC8ghgw8vXsBuRCXePqjoZe-ZI7Dw4AYP2BeBPseHy5LmEnYRzh-Ac_sFDh842hp5jwauSFKmc",
                "remove": "AB9zfpLv90WybdM6AvEZG43hb3BHUHBdag9VLs0zwFuwCV0BZ4wxoqt1foxp3mR4V3T2puwH8-DlLBwgvEqhR0cU8oU5XnegxAjgmrTbkAoDCSkwKBEd6bs"
            }
        },
        {
            "videoId": "9fA4XZN68ro",
            "title": "Chumbok Mon (From \"Kacher Manush\")",
            "artists": [
                {
                    "name": "Nilayan Chatterjee",
                    "id": "UCraeR0yYCDVUjORC26LTiDw"
                },
                {
                    "name": "Usha Uthup",
                    "id": "UCfs2-fZPB8jgLlYm1WElo_Q"
                }
            ],
            "album": {
                "name": "Chumbok Mon (From \"Kacher Manush\")",
                "id": "MPREb_eHc2ozEpuUV"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/nzDslQjir65Mnz25Xx_HAMkloTgHcDmkqGoUFlIjyFbZ5elH3O0KeyC7idGDYaIN1EJ2erLy38SvuKE=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/nzDslQjir65Mnz25Xx_HAMkloTgHcDmkqGoUFlIjyFbZ5elH3O0KeyC7idGDYaIN1EJ2erLy38SvuKE=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:01",
            "duration_seconds": 181,
            "feedbackTokens": {
                "add": "AB9zfpLinfRiJrxlRmD1g33fK03ctNu4-yjlZZXMsMriL_5RvmlqRopyaHNqZLs_OsxLpIF6eiI-ghnPZXHmv3kF0ryy8wKYTELeKvO73IUdZUtQ5MdJC-Q",
                "remove": "AB9zfpJiGgsnbBMSgPE3PZCy0JKvC5Jg-nmb0eTaVS3fdvAAbx5RwO_dNbhgX4l307p3uuHRb4RWTY9muaLFVQwy8jO5-4x0EZqbfcWiKSMIrHE8-en88ZE"
            }
        },
        {
            "videoId": "9fB1I3f5WYk",
            "title": "Janina Bhalolaga",
            "artists": [
                {
                    "name": "Nikhita Gandhi",
                    "id": "UCZ3bAw2GF0A_VVI6uHqMC5g"
                },
                {
                    "name": "Shashwat Singh",
                    "id": "UCYzHQaZCaQWXMoXCEfuKURw"
                }
            ],
            "album": {
                "name": "Janina Bhalolaga - Kishmish",
                "id": "MPREb_pmmi2A2h4KY"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/c4hSH9U0JnQRdeWdTMO8TnTx0Iw03KwBL6XjHgEp55eyuczMV3pd4Q6tPZsbiOA9O2eC_WL8OB2pPmNj=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/c4hSH9U0JnQRdeWdTMO8TnTx0Iw03KwBL6XjHgEp55eyuczMV3pd4Q6tPZsbiOA9O2eC_WL8OB2pPmNj=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "3:37",
            "duration_seconds": 217,
            "feedbackTokens": {
                "add": "AB9zfpJSTgKTa_phT8sXTMBipWkAAPOcoGS5lw2TxY1eEWJMUV76aWl0NacNTLWxGVYWA0AMthRAfsDl3QXhL0dXIdxAelBptpA3OMcscwl7L3JIhc0y3YU",
                "remove": "AB9zfpK-7syYyC5eXW_G1W3LTd7yLFv2XV6Kat4LNRCRBfBoGVb6KhEiodFfwJSmYd3soC7G8QpgoOR0bI7KTtt-K7lcviFtdt4opqxmvyUaV2Zc_juIwfA"
            }
        },
        {
            "videoId": "aqWQQThjwfU",
            "title": "Geetabitan Er Dibbi (Male)",
            "artists": [
                {
                    "name": "Ranajoy Bhattacharjee",
                    "id": "UCBUd_C56uKWr48WVK4A62tg"
                }
            ],
            "album": {
                "name": "Kolkata Chalantika (Original Motion Picture Soundtrack)",
                "id": "MPREb_B2cae0Mh9f9"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/zJV0gRKMg5nV_ECr037E5Alh1ZPmcV7mSYp4P4Xqr_Uc4YoX5g8Ccb7b1ZxEZj6uRNpfzDtyXx-AQZK_5g=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/zJV0gRKMg5nV_ECr037E5Alh1ZPmcV7mSYp4P4Xqr_Uc4YoX5g8Ccb7b1ZxEZj6uRNpfzDtyXx-AQZK_5g=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "4:06",
            "duration_seconds": 246,
            "feedbackTokens": {
                "add": "AB9zfpJSSSHMG16-oF0ezWOp5dql2EX2zU8tqmyl0yqhjbqrzdDnR5vWZStqNFGfkhy7J9iSGlhJTSsGqEWbPO-xR1J7UgSp8Y3Fua26bFuUDuhhZ4W1VcU",
                "remove": "AB9zfpLMK5xyWpn3GzIl1AjwzoeJk4moXxWlOTncQycQVocdvOAgEAurYRGPAHKokaHvIrsw_PG-SBcDLhYF5kAXH2_3BIQKV3qgzUgBtcAchFNebS_wxnU"
            }
        },
        {
            "videoId": "-e2to10y5Uc",
            "title": "Boka Boka Ei Mon (From \"Shrimati\")",
            "artists": [
                {
                    "name": "Anupam Roy",
                    "id": "UCahH3l5sz429SqebyK5ZCbA"
                },
                {
                    "name": "Soumya Rit",
                    "id": "UCIZfX9fvsMSraSghNogHf6g"
                }
            ],
            "album": {
                "name": "Boka Boka Ei Mon (From \"Shrimati\")",
                "id": "MPREb_QSRuYOPD2bb"
            },
            "likeStatus": "INDIFFERENT",
            "inLibrary": False,
            "thumbnails": [
                {
                    "url": "https://lh3.googleusercontent.com/BEloIU-Hm98-fDwfjJdzNFr0ld1hWng4Z701ATu4vznkVP8BIoNVLqoMqSuSn8Rk6g8JLiHNRp7GuyET=w60-h60-l90-rj",
                    "width": 60,
                    "height": 60
                },
                {
                    "url": "https://lh3.googleusercontent.com/BEloIU-Hm98-fDwfjJdzNFr0ld1hWng4Z701ATu4vznkVP8BIoNVLqoMqSuSn8Rk6g8JLiHNRp7GuyET=w120-h120-l90-rj",
                    "width": 120,
                    "height": 120
                }
            ],
            "isAvailable": True,
            "isExplicit": False,
            "videoType": "MUSIC_VIDEO_TYPE_ATV",
            "views": None,
            "duration": "4:18",
            "duration_seconds": 258,
            "feedbackTokens": {
                "add": "AB9zfpLzLufacQpUfpZgv-ZxsxX3lP-To-fBXDbVcTLsg6hg_iYjczXTjtrl-3SNETdVrOyRJI8P7Vs0DhopMOFaSSDc-04rqwZ44cbWR8g-9vs9MMHRlQk",
                "remove": "AB9zfpIXwf2zU2veOVQtWRY-QjR35lacEsCkWnkM7lnxM0ZpT0-hV9PBlvWKUNSZZk5HbFZJ56zuO41ZGDWsU1Dstj5Vk5z4gfjOPzapdLCy4KL7XMy1JMk"
            }
        }
    ]
            
async def main():
    db = DatabaseManager("data/user/database.db")
    dirs = [
        r"D:\Media\Music\Dance",
        r"D:\Media\Music\Party",
        r"D:\Media\Music\Sad Song",
        r"D:\Media\Music\Romantic",
        r"D:\Media\Music\Song"
    ]
    ids = ['3a2c062e2ddfd945', 'fa9a5b715c59cf32', '4fe20e0269a64557', 'd679616daf70c186', 'ec1e9745eff40982']
    await db._connect_db()
    
    data = {
        "videoId": ids[0],
        'title': "Test",
        'artists': "Ghost",
        'album': "Tance",
        'duration': "2:36"   
            }
    
    # print(await db.get_song("xBnc7zN3vLA"))
    # await db.insert_local_song(data)
    data = await db.fetch_song("Lkq2Fic8rCY")
    logger.debug(f"Data: {data}")
    # for uid, directory in zip(ids, dirs):
    #     await db.insert_local_directory(uid, directory)
        
if __name__ == "__main__":
    # app = QApplication([])
    # window = QMainWindow()
    asyncio.run(main())
    # window.show()
    # QtAsyncio.run()
    
    