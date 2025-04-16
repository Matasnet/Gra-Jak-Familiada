import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('questions.db')
        return conn
    except Error as e:
        print(e)
    return conn

def create_tables(conn):
    try:
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS questions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      question TEXT NOT NULL,
                      round_number INTEGER NOT NULL)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS answers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      question_id INTEGER NOT NULL,
                      answer TEXT NOT NULL,
                      points INTEGER NOT NULL,
                      revealed INTEGER DEFAULT 0,
                      FOREIGN KEY (question_id) REFERENCES questions (id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS teams
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      score INTEGER DEFAULT 0,
                      warnings INTEGER DEFAULT 0)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS game_state
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      current_round INTEGER DEFAULT 1,
                      current_question_id INTEGER,
                      game_active INTEGER DEFAULT 0,
                      round_points INTEGER DEFAULT 0)''')
        
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
        c = conn.cursor()
        
        # Clear existing data
        c.execute("DELETE FROM questions")
        c.execute("DELETE FROM answers")
        c.execute("DELETE FROM teams")
        c.execute("DELETE FROM game_state")

        # Add sample questions and answers
        questions = [
            ("Wymień popularny owoc jagodowy", 1),
            ("Podaj nazwę znanego polskiego piłkarza", 2),
            ("Jak nazywa się stolica Polski?", 3),
            ("Wymień popularny gatunek drzewa liściastego", 4),
            ("Podaj nazwę cieśniny łączącej Morze Bałtyckie z Morzem Północnym", 5),
            ("Jak nazywa się program telewizyjny z teleturniejami?", 6),
            ("Wymień popularny składnik sałatki jarzynowej", 7),
            ("Podaj nazwę pasma górskiego w Polsce", 8),
            ("Jak nazywa się ssak z długą trąbą?", 9),
            ("Wymień popularny rodzaj sera", 10),
            ("Podaj nazwę planety Układu Słonecznego innej niż Ziemia", 11),
            ("Jak nazywa się urządzenie do zdalnego sterowania telewizorem?", 12)
        ]

        answers = [
            [
                ("Truskawka", 40),
                ("Malina", 35),
                ("Jagoda", 30),
                ("Borówka", 25),
                ("Poziomka", 20)
            ],
            [
                ("Robert Lewandowski", 45),
                ("Kamil Glik", 38),
                ("Jakub Błaszczykowski", 31),
                ("Piotr Zieliński", 24),
                ("Wojciech Szczęsny", 17)
            ],
            [
                ("Warszawa", 45),
                ("Stolica", 30),
                ("Największe miasto Polski", 25),
                ("Miasto nad Wisłą", 20)
            ],
            [
                ("Dąb", 42),
                ("Buk", 36),
                ("Brzoza", 30),
                ("Klon", 24),
                ("Lipа", 18),
                ("Jesion", 12)
            ],
            [
                ("Cieśnina Duńska", 45),
                ("Sund", 35),
                ("Wielki Bełt", 25),
                ("Mały Bełt", 15),
                ("Kattegat", 11)
            ],
            [
                ("Familiada", 40),
                ("Jeden z dziesięciu", 34),
                ("Milionerzy", 28),
                ("Koło Fortuny", 22),
                ("Va Banque", 16)
            ],
            [
                ("Marchew", 41),
                ("Pietruszka", 35),
                ("Seler", 29),
                ("Groszek", 23),
                ("Kukurydza", 17),
                ("Por", 11)
            ],
            [
                ("Tatry", 43),
                ("Karkonosze", 37),
                ("Beskidy", 31),
                ("Sudety", 25),
                ("Pieniny", 19)
            ],
            [
                ("Słoń", 45),
                ("Mamut", 30),
                ("Trąbowiec", 20),
                ("Afrykański", 11)
            ],
            [
                ("Żółty ser", 40),
                ("Biały ser", 34),
                ("Ser pleśniowy", 28),
                ("Twaróg", 22),
                ("Mozzarella", 16),
                ("Feta", 11)
            ],
            [
                ("Mars", 40),
                ("Jowisz", 34),
                ("Saturn", 28),
                ("Wenus", 22),
                ("Merkury", 16),
                ("Uran", 11)
            ],
            [
                ("Pilot", 45),
                ("Pilocik", 30),
                ("Sterownik", 20),
                ("Przełącznik kanałów", 11)
            ]
        ]
        
        for i, (question, round_num) in enumerate(questions):
            c.execute("INSERT INTO questions (question, round_number) VALUES (?, ?)", 
                      (question, round_num))
            question_id = c.lastrowid
            for answer, points in answers[i]:
                c.execute("INSERT INTO answers (question_id, answer, points) VALUES (?, ?, ?)",
                          (question_id, answer, points))
        
        # Add default teams
        c.execute("INSERT INTO teams (name) VALUES (?)", ("Team A",))
        c.execute("INSERT INTO teams (name) VALUES (?)", ("Team B",))
        
        # Initialize game state
        c.execute("INSERT INTO game_state (current_round, game_active, round_points) VALUES (0, 0, 0)")
        
        conn.commit()
        conn.close()

if __name__ == '__main__':
    initialize_database()
    add_sample_data()