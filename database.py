import sqlite3


DATABASE_NAME = "soccer_data.db"


def create_connection():
    return sqlite3.connect(
        DATABASE_NAME
    )


def create_tables():
    connection = create_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_players (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            team TEXT,
            season INTEGER,
            appearances INTEGER,
            starts INTEGER,
            minutes INTEGER,
            goals INTEGER,
            assists INTEGER
        )
        """
    )

    connection.commit()
    connection.close()  
