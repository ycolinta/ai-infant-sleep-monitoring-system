import sqlite3
from pathlib import Path


DATABASE_FOLDER = Path(__file__).parent / "database"
DATABASE_PATH = DATABASE_FOLDER / "ism.db"


def initialize_db():
    """
    This function creates the infant sleep monitoring system database
    and its required tables.
    """

    sqlite_connection = None
    cursor = None

    try:
        # Creates the database folder if it does not already exist
        DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

        sqlite_connection = sqlite3.connect(DATABASE_PATH)
        cursor = sqlite_connection.cursor()

        # Enables enforcement of foreign-key relationships in SQLite
        cursor.execute("PRAGMA foreign_keys = ON;")

        # ******* Create 'Model' table *******
        create_table_model = """
            CREATE TABLE IF NOT EXISTS Model (
                model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL UNIQUE,
                model_is_human INTEGER NOT NULL
                    CHECK (model_is_human IN (0, 1))
            );
        """

        cursor.execute(create_table_model)

        # ******* Create 'Images' table *******
        create_table_images = """
            CREATE TABLE IF NOT EXISTS Images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL UNIQUE,
                file_ext TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE
            );
        """

        cursor.execute(create_table_images)

        # ******* Create 'Response' table *******
        create_table_response = """
            CREATE TABLE IF NOT EXISTS Response (
                response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                no_apparent_safety_concerns INTEGER NOT NULL
                    CHECK (no_apparent_safety_concerns IN (0, 1)),
                possible_safety_concerns INTEGER NOT NULL
                    CHECK (possible_safety_concerns IN (0, 1)),
                serious_safety_concerns INTEGER NOT NULL
                    CHECK (serious_safety_concerns IN (0, 1)),
                explanation TEXT NOT NULL,

                FOREIGN KEY (image_id)
                    REFERENCES Images(image_id),

                FOREIGN KEY (model_id)
                    REFERENCES Model(model_id)
            );
        """

        cursor.execute(create_table_response)

        sqlite_connection.commit()

        print(f"Database initialized successfully: {DATABASE_PATH}")
        return True

    except sqlite3.Error as error:
        if sqlite_connection is not None:
            sqlite_connection.rollback()

        print(f"Database initialization failed: {error}")
        return False

    finally:
        if cursor is not None:
            cursor.close()

        if sqlite_connection is not None:
            sqlite_connection.close()


# Helper function to connect to the database
def get_db_connection():
    """
    Creates and returns a connection to the infant sleep monitoring
    system database.
    """

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # Foreign-key enforcement must be enabled for each connection
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


if __name__ == "__main__":
    initialize_db()