import asyncio
import os
import sys

import aiosqlite
async def initialize_database(db_name: str , schema_sql: str):
    """Initializes the SQLite database with the schema."""
    try:
        async with aiosqlite.connect(db_name) as conn:
            await conn.executescript(schema_sql)
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
