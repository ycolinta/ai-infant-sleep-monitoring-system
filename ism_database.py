import sqlite3
from pathlib import Path

# main project folder
PROJECT_FOLDER = Path(__file__).parent

DATABASE_FOLDER = PROJECT_FOLDER / "database"
DATABASE_PATH = DATABASE_FOLDER / "ism.db"
IMAGES = PROJECT_FOLDER / "images"


def initialize_db():
    """
    Create sleep monitoring system database
    and its required tables.
    """

    sqlite_connection = None
    cursor = None

    try:
        # Creates the database folder if it does not already exist
        DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)
        # connect to db
        sqlite_connection = sqlite3.connect(DATABASE_PATH)
        cursor = sqlite_connection.cursor()

        # Enables foreign-key relationships in SQLite
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

        # Save the tables created
        sqlite_connection.commit()

        print(f"Database initialized successfully: {DATABASE_PATH}")
        return True

    except sqlite3.Error as error:
        # if something fails, go back and undo changes
        if sqlite_connection is not None:
            sqlite_connection.rollback()

        print(f"Database initialization failed: {error}")
        return False

    finally:
        # Close cursor and connection
        if cursor is not None:
            cursor.close()

        if sqlite_connection is not None:
            sqlite_connection.close()


def get_db_connection():
    """
    Helper function that opens and returns a connection to the database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # Rows to be accessed by column names
    connection.row_factory = sqlite3.Row

    # Foreign-key enforcement must be enabled for each connection
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def insert_models():
    """
    Inserts different intelligent models, including human, into the Model table.
    """

    models = [
        ("Human-Parent Assessor", 1),
        ("Gemini 2.5 Flash", 0),
        ("GPT-4.1 Mini", 0),
        ("Claude Sonnet 4-6", 0)
    ]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Insert all model types
        cursor.executemany (
            """
            INSERT INTO Model (model_name, model_is_human)
            VALUES (?, ?);
            """,
            models
        )

        connection.commit()
        print("Model records inserted successfully.")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Failed to insert model records: {error}")

    finally:
        cursor.close()
        connection.close()


def insert_images():
    """
    Inserts image metadata for each image found in
    'images' folder.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Process every data in the images folder
        for image_path in IMAGES.iterdir():
            # Skip non-file entries
            if not image_path.is_file():
                continue

            # Store a relative path to the project folder
            relative_path = image_path.relative_to(Path(__file__).parent)

            cursor.execute(
                """
                INSERT INTO Images (file_name, file_ext, file_path)
                VALUES (?, ?, ?);
                """,
                (
                    image_path.name,
                    image_path.suffix.lower(),
                    str(relative_path)
                )
            )

        connection.commit()
        print("Images have been inserted successfully.")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Failed to insert image records: {error}")

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    if initialize_db():
        insert_models()
        insert_images()