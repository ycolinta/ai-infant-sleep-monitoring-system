import sqlite3
import json
from pathlib import Path

# main project folder
PROJECT_FOLDER = Path(__file__).parent

DATABASE_FOLDER = PROJECT_FOLDER / "database"
DATABASE_PATH = DATABASE_FOLDER / "ism.db"
IMAGES = PROJECT_FOLDER / "images"
RESULTS_FOLDER = PROJECT_FOLDER / "results"

# Gemini's Flash model
GEMINI_OUTPUT = RESULTS_FOLDER / "updated_run" / "gemini_outputs"
GEMINI_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "gemini_invalid_outputs"

# OpenAI's GPT model
OPENAI_OUTPUT = RESULTS_FOLDER / "updated_run" / "openai_outputs"
OPENAI_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "openai_invalid_outputs"

# Anthropic's claude model
ANTHROPIC_OUTPUT = RESULTS_FOLDER / "updated_run" / "anthropic_outputs"
ANTHROPIC_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "anthropic_invalid_outputs"

# Mistral's model
MISTRAL_OUTPUT = RESULTS_FOLDER / "updated_run" / "mistral_outputs"
MISTRAL_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "mistral_invalid_outputs"

# Parent's model
PARENT_MODEL_NAME = "Human-Parent Assessor"

PARENT_OUTPUT = PROJECT_FOLDER / "parent_assessments"


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
                
                UNIQUE (image_id, model_id),
                
                FOREIGN KEY (image_id)
                    REFERENCES Images(image_id),

                FOREIGN KEY (model_id)
                    REFERENCES Model(model_id)
            );
        """

        # ******* Create 'InvalidResponse' table *******
        create_table_invalid_response = """  
            CREATE TABLE IF NOT EXISTS InvalidResponse (
                invalid_response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                raw_response TEXT NOT NULL,
                explanation_error TEXT NOT NULL,
        
                UNIQUE (image_id, model_id),
        
                FOREIGN KEY (image_id)
                    REFERENCES Images(image_id),
        
                FOREIGN KEY (model_id)
                    REFERENCES Model(model_id)
            );
        """

        cursor.execute(create_table_response)
        cursor.execute(create_table_invalid_response)

        # Prevent duplicate valid responses for the same image and model
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_response_image_model
            ON Response (image_id, model_id);
            """
        )

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
        ("Claude Sonnet 4-6", 0),
        ("Mistral Medium 3.5", 0)
    ]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Insert all model types
        cursor.executemany(
            """
            INSERT OR IGNORE INTO Model (model_name, model_is_human)
            VALUES (?, ?);
            """,
            models
        )

        connection.commit()
        print("Model records checked and inserted successfully.")

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
            relative_path = image_path.relative_to(PROJECT_FOLDER)

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


def insert_image(image_path):
    """
    Inserts an image into the Images table.
    Returns its image id.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        relative_path = image_path.relative_to(PROJECT_FOLDER)
        cursor.execute(
            """
            INSERT OR IGNORE INTO Images (
            file_name,
            file_ext,
            file_path
            )
            VALUES (?, ?, ?);
            """,
            (
                image_path.name,
                image_path.suffix.lower(),
                str(relative_path)
            )
        )

        connection.commit()
        cursor.execute(
            """
            SELECT image_id
            FROM Images
            WHERE file_name = ?;
            """,
            (image_path.name,)
        )

        result = cursor.fetchone()

        if result is None:
            raise ValueError(f"Error in retrieving image: {image_path.name}")

        return result["image_id"]

    finally:
        cursor.close()
        connection.close()


def get_image_id(file_name):
    """
    Returns the image_id associated with the given file name.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT image_id
            FROM Images
            WHERE file_name = ?;
            """,
            (file_name,)
        )

        result = cursor.fetchone()

        if result is None:
            raise ValueError(f"Image '{file_name}' was not found.")

        return result["image_id"]

    finally:
        cursor.close()
        connection.close()


def get_images_by_ids(image_ids):
    """
    Returns the images associated with the given image ids.
    """
    if not image_ids:
        return []

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Parameterized query here
        placeholders = ", ".join("?" for _ in image_ids)
        cursor.execute(
            f"""
            SELECT
                image_id,
                file_name,
                file_path
            FROM Images
            WHERE image_id IN ({placeholders})
            ORDER BY image_id;
            """,
            image_ids
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_model_id(model_name):
    """
    Returns the model_id associated with the given model name.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT model_id
            FROM Model
            WHERE model_name = ?;
            """,
            (model_name,)
        )

        result = cursor.fetchone()

        if result is None:
            raise ValueError(f"Model '{model_name}' was not found.")

        return result["model_id"]

    finally:
        cursor.close()
        connection.close()


def populate_response_table(model_name, output_folder):
    """
    Reads JSON files from one model's output folder
    and inserts responses that are not already stored.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Find the model's database ID
        cursor.execute(
            """
            SELECT model_id
            FROM Model
            WHERE model_name = ?;
            """,
            (model_name,)
        )

        model_record = cursor.fetchone()

        if model_record is None:
            print(f"Model was not found: {model_name}")
            return False

        model_id = model_record["model_id"]

        # Process every JSON file in the output folder
        for json_path in output_folder.iterdir():

            if not json_path.is_file() or json_path.suffix.lower() != ".json":
                continue

            with json_path.open("r", encoding="utf-8") as json_file:
                response = json.load(json_file)

            # Find the image's database ID
            cursor.execute(
                """
                SELECT image_id
                FROM Images
                WHERE file_name = ?;
                """,
                (response["file_name"],)
            )

            image_record = cursor.fetchone()

            if image_record is None:
                print(f"Image was not found: {response['file_name']}")
                continue

            image_id = image_record["image_id"]

            # Check whether this response was already inserted
            cursor.execute(
                """
                SELECT response_id
                FROM Response
                WHERE image_id = ?
                  AND model_id = ?;
                """,
                (image_id, model_id)
            )

            existing_response = cursor.fetchone()

            if existing_response is not None:
                print(
                    f"Response already exists for "
                    f"{response['file_name']} from {model_name}. Skipping."
                )
                continue

            # Insert the new response
            cursor.execute(
                """
                INSERT INTO Response (
                    image_id,
                    model_id,
                    no_apparent_safety_concerns,
                    possible_safety_concerns,
                    serious_safety_concerns,
                    explanation
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    image_id,
                    model_id,
                    int(response["no_apparent_safety_concerns"]),
                    int(response["possible_safety_concerns"]),
                    int(response["serious_safety_concerns"]),
                    response["explanation"]
                )
            )

            print(
                f"Inserted {model_name} response for "
                f"{response['file_name']}."
            )

        connection.commit()
        return True

    except (
            sqlite3.Error,
            OSError,
            json.JSONDecodeError,
            KeyError
    ) as error:
        connection.rollback()
        print(f"Failed to populate Response table: {error}")
        return False

    finally:
        cursor.close()
        connection.close()


def insert_response(image_id, model_name, response_obj):
    """
    Function that inserts one valid AI response into the Response table.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        model_id = get_model_id(model_name)

        cursor.execute(
            """
            INSERT INTO Response (
                image_id,
                model_id,
                no_apparent_safety_concerns,
                possible_safety_concerns,
                serious_safety_concerns,
                explanation
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                image_id,
                model_id,
                int(response_obj["no_apparent_safety_concerns"]),
                int(response_obj["possible_safety_concerns"]),
                int(response_obj["serious_safety_concerns"]),
                response_obj["explanation"]
            )
        )

        connection.commit()
        print(f"Inserted {model_name} response for image ID {image_id}.")
        return True

    except sqlite3.IntegrityError as error:
        connection.rollback()
        print(f"Could not insert {model_name} response for image ID {image_id}: {error}")
        return False

    except (sqlite3.Error, KeyError, ValueError) as error:
        connection.rollback()
        print(f"Failed to insert valid response: {error}")
        return False

    finally:
        cursor.close()
        connection.close()


def insert_invalid_response(image_id, model_name, raw_response, explanation_error):
    """
    Inserts one invalid AI response into the InvalidResponse table.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        model_id = get_model_id(model_name)

        cursor.execute(
            """
            INSERT INTO InvalidResponse (
                image_id,
                model_id,
                raw_response,
                explanation_error
            )
            VALUES (?, ?, ?, ?);
            """,
            (
                image_id,
                model_id,
                raw_response,
                explanation_error
            )
        )

        connection.commit()
        print(f"Inserted invalid {model_name} response for image ID {image_id}.")
        return True

    except sqlite3.IntegrityError as error:
        connection.rollback()
        print(f"Could not insert invalid {model_name} response for image ID {image_id}: {error}")
        return False

    except (sqlite3.Error, ValueError) as error:
        connection.rollback()
        print(f"Failed to insert invalid response: {error}")
        return False

    finally:
        cursor.close()
        connection.close()


def get_comparison_table(image_ids):
    """
    Function that compares each AI model output response with parents
    for the provided image unique ID and retrieves data of the row:
        - Image filename, AI model name, parent truth label, AI model label
        - Whether the labels match y/n
        - Parent explanation
        - AI model explanation
    """
    if not image_ids:
        return []

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Create one SQL placeholder for each image ID.
        placeholders = ", ".join(
            "?" for _ in image_ids
        )

        cursor.execute(
            f"""
            SELECT
                i.image_id,
                i.file_name,

                ai_model.model_name
                    AS ai_model_name,

                CASE
                    WHEN parent_response.no_apparent_safety_concerns = 1
                        THEN 'No apparent safety concerns'
                    WHEN parent_response.possible_safety_concerns = 1
                        THEN 'Possible safety concerns'
                    WHEN parent_response.serious_safety_concerns = 1
                        THEN 'Serious safety concerns'
                END AS parent_truth_label,

                CASE
                    WHEN ai_response.no_apparent_safety_concerns = 1
                        THEN 'No apparent safety concerns'
                    WHEN ai_response.possible_safety_concerns = 1
                        THEN 'Possible safety concerns'
                    WHEN ai_response.serious_safety_concerns = 1
                        THEN 'Serious safety concerns'
                END AS ai_model_label,

                CASE
                    WHEN
                        parent_response.no_apparent_safety_concerns
                        = ai_response.no_apparent_safety_concerns
                    AND
                        parent_response.possible_safety_concerns
                        = ai_response.possible_safety_concerns
                    AND
                        parent_response.serious_safety_concerns
                        = ai_response.serious_safety_concerns
                    THEN 'Yes'
                    ELSE 'No'
                END AS exact_label_match,

                parent_response.explanation
                    AS parent_explanation,

                ai_response.explanation
                    AS ai_model_explanation

            FROM Images AS i

            JOIN Response AS parent_response
                ON i.image_id = parent_response.image_id

            JOIN Model AS parent_model
                ON parent_response.model_id = parent_model.model_id

            JOIN Response AS ai_response
                ON i.image_id = ai_response.image_id

            JOIN Model AS ai_model
                ON ai_response.model_id = ai_model.model_id

            WHERE i.image_id IN ({placeholders})
              AND parent_model.model_name = ?
              AND ai_model.model_name != ?

            ORDER BY 
                i.image_id,
                ai_model.model_name;
            """,
            (
                *image_ids,
                PARENT_MODEL_NAME,
                PARENT_MODEL_NAME
            )
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def print_comparison_table(comparison_rows):
    """
    Prints the parent and AI comparison table for one
    monitoring session.
    """

    if not comparison_rows:
        print("\nNo comparison results were found.")
        return

    print("\nSession Comparison Results\n")

    print(
        f"{'Image File':<30}"
        f"{'AI Model':<15}"
        f"{'Parent Truth Label':<30}"
        f"{'AI Model Label':<30}"
        f"{'Match':<10}"
    )

    print("_" * 120)

    for row in comparison_rows:
        print(
            f"{row['file_name']:<30}"
            f"{row['ai_model_name']:<15}"
            f"{row['parent_truth_label']:<30}"
            f"{row['ai_model_label']:<30}"
            f"{row['exact_label_match']:<10}"
        )

        print(f"Parent Explanation: {row['parent_explanation']}")
        print(f"AI Model Explanation: {row['ai_model_explanation']}")

        print("_" * 120)


if __name__ == "__main__":
    if initialize_db():
        insert_models()

        populate_response_table(
            "Gemini 2.5 Flash",
            GEMINI_OUTPUT
        )

        populate_response_table(
            "GPT-4.1 Mini",
            OPENAI_OUTPUT
        )

        populate_response_table(
            "Claude Sonnet 4-6",
            ANTHROPIC_OUTPUT
        )

        populate_response_table(
            "Mistral Medium 3.5",
            MISTRAL_OUTPUT
        )

        populate_response_table(
            "Human-Parent Assessor",
            PARENT_OUTPUT
        )
