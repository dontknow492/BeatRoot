import aiosqlite
import asyncio

import os
import sys

def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Use this function to locate your files
DB_NAME = get_resource_path("data\\user\\database.db")
SCHEMA_SQL_PATH = get_resource_path("data\\user\\schema.sql")

# SQL Schema
with open(SCHEMA_SQL_PATH, "r") as sql_file:
    SCHEMA_SQL = sql_file.read()

async def initialize_database(db_name: str = DB_NAME):
    """Initializes the SQLite database with the schema."""
    try:
        async with aiosqlite.connect(db_name) as conn:
            await conn.executescript(SCHEMA_SQL)
            await conn.execute("pragma foreign_keys=on")
            await conn.commit()
            print("Database initialized successfully!")
            await conn.close()
    except aiosqlite.Error as e:
        print(f"Error initializing database: {e}")

async def main():
    await initialize_database()
    

if __name__ == "__main__":
    asyncio.run(main())
