import sqlite3
from sqlite3 import Error
import random

DATABASE_NAME = 'familiada.db'

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    except Error as e:
        print(e)
    return conn

def create_tables(conn):
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                points INTEGER NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        """)

        conn.commit()
    except Error as e:
        print(e)

def initialize_database():
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()

def add_sample_data():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            questions_data = [
                ("Name something you might find in a kitchen", ["Refrigerator", "Stove", "Sink", "Microwave"]),
                ("Name a color of the rainbow 1", ["Red", "Blue", "Green", "Yellow"]),
                ("Name a sport played with a ball", ["Football", "Basketball", "Tennis", "Volleyball"]),
                ("Name a color of the rainbow 2", ["Red", "Blue", "Green", "Yellow"]),
                ("Name a color of the rainbow 4", ["Red", "Blue", "Green", "Yellow"]),
                ("Name a color of the rainbow 5", ["Red", "Blue", "Green", "Yellow"]),
                ("Name a color of the rainbow 6", ["Red", "Blue", "Green", "Yellow"]),
                ("Name a color of the rainbow 7", ["Red", "Blue", "Green", "Yellow"]),
                ("Name a color of the rainbow 8", ["Red", "Blue", "Green", "Yellow"]),
                ("Name a color of the rainbow 9", ["Red", "Blue", "Green", "Yellow"])
            ]

            for q_text, answers_text in questions_data:
                cursor.execute("INSERT INTO questions (question_text, used) VALUES (?, ?)", (q_text, 0))
                question_id = cursor.lastrowid
                num_answers = len(answers_text)
                base_points = 35 // num_answers if num_answers > 0 else 0
                remainder = 35 % num_answers if num_answers > 0 else 0
                points_per_answer = [base_points + (1 if i < remainder else 0) + random.randint(0, 5) for i in range(num_answers)]
                random.shuffle(points_per_answer)
                total_points = sum(points_per_answer)

                if 35 <= total_points <= 100 and num_answers > 0:
                    for i, answer_text in enumerate(answers_text):
                        cursor.execute("INSERT INTO answers (question_id, answer_text, points) VALUES (?, ?, ?)", (question_id, answer_text, points_per_answer[i]))
                else:
                    cursor.execute("DELETE FROM answers WHERE question_id = ?", (question_id,))
                    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
                    print(f"Ostrzeżenie: Nie udało się wygenerować punktów dla '{q_text}' w zakresie 35-100. Pytanie usunięto.")

            conn.commit()
        except Error as e:
            print(e)
        finally:
            conn.close()

def get_random_question(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, question_text FROM questions WHERE used = 0 ORDER BY RANDOM() LIMIT 1")
    return cursor.fetchone()

def get_question_answers(conn, question_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id, answer_text, points FROM answers WHERE question_id = ?", (question_id,))
    return cursor.fetchall()

def mark_question_as_used(conn, question_id):
    cursor = conn.cursor()
    cursor.execute("UPDATE questions SET used = 1 WHERE id = ?", (question_id,))
    conn.commit()

if __name__ == '__main__':
    initialize_database()
    add_sample_data()