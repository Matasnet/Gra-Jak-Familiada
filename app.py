from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import create_connection, get_random_question, get_question_answers, mark_question_as_used
import sqlite3
import random

app = Flask(__name__)

class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.team1 = {'name': 'Drużyna 1', 'score': 0, 'warnings': 0}
        self.team2 = {'name': 'Drużyna 2', 'score': 0, 'warnings': 0}
        self.current_question = None
        self.revealed_answers = []
        self.current_team = 1
        self.total_revealed = 0
        self.correctly_guessed_answer_id = None

game_state = GameState()

def get_current_team():
    return game_state.team1 if game_state.current_team == 1 else game_state.team2

def switch_team():
    game_state.current_team = 2 if game_state.current_team == 1 else 1
    return game_state.current_team

def reset_warnings():
    game_state.team1['warnings'] = 0
    game_state.team2['warnings'] = 0

@app.route('/')
def home():
    return render_template('index.html', game_state=game_state.__dict__)

@app.route('/start', methods=['POST'])
def start_game():
    print("--> Wywołano POST /start")
    data = request.get_json()
    team1_name = data.get('team1Name', 'Drużyna 1')
    team2_name = data.get('team2Name', 'Drużyna 2')
    starting_team = data.get('startingTeam', 1)

    conn = create_connection()
    if not conn:
        print("Błąd: Nie udało się połączyć z bazą danych.")
        return jsonify({'success': False, 'error': 'Database error'})

    try:
        game_state.reset()
        game_state.team1['name'] = team1_name
        game_state.team2['name'] = team2_name
        game_state.current_team = starting_team

        question = get_random_question(conn)
        if question:
            game_state.current_question = {'id': question['id'], 'question_text': question['question_text']}
            answers = get_question_answers(conn, game_state.current_question['id'])
            game_state.current_question['answers'] = [dict(row) for row in answers]
            print(f"Pomyślnie rozpoczęto grę. Pytanie: {game_state.current_question['question_text']}")
            print(f"Odpowiedzi: {game_state.current_question['answers']}")
            return jsonify({
                'success': True,
                'question': game_state.current_question,
                'game_state': game_state.__dict__
            })
        else:
            print("Błąd: Brak dostępnych pytań w bazie danych.")
            return jsonify({'success': False, 'error': 'No questions available'})
    except Exception as e:
        print(f"Wystąpił błąd podczas obsługi /start: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()
            print("Połączenie z bazą danych zamknięte po /start.")

@app.route('/answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    answer = data.get('answer', '').strip().lower()
    team = game_state.current_team

    if not answer or not game_state.current_question:
        return jsonify({'success': False, 'error': 'Invalid data'})

    conn = create_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'})

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, points, answer_text FROM answers
            WHERE question_id = ? AND LOWER(answer_text) = ? AND id NOT IN ({})
        """.format(','.join('?' * len(game_state.revealed_answers))),
        [game_state.current_question['id'], answer] + game_state.revealed_answers)

        result = cursor.fetchone()
        response = {'success': True}

        if result:
            answer_id, points, answer_text = result['id'], result['points'], result['answer_text']
            game_state.revealed_answers.append(answer_id)
            game_state.total_revealed += points
            get_current_team()['score'] += points
            
            # Inicjalizacja listy poprawnych odpowiedzi jeśli nie istnieje
            if not hasattr(game_state, 'correct_answers'):
                game_state.correct_answers = []
            
            # Dodanie poprawnej odpowiedzi do listy
            if answer_id not in game_state.correct_answers:
                game_state.correct_answers.append(answer_id)
            
            response.update({
                'correct': True,
                'answer_id': answer_id,
                'points': points,
                'answer_text': answer_text,
                'game_state': game_state.__dict__
            })
        else:
            get_current_team()['warnings'] += 1
            response.update({
                'correct': False,
                'warning': get_current_team()['warnings'],
                'game_state': game_state.__dict__
            })
            if get_current_team()['warnings'] >= 3:
                response['force_reveal'] = True
                switch_team()

        return jsonify(response)
    except Exception as e:
        print(f"Wystąpił błąd podczas obsługi /answer: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()


@app.route('/reveal_all', methods=['POST'])
def reveal_all_answers():
    if not game_state.current_question:
        return jsonify({'success': False, 'error': 'No active question'})

    conn = create_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'})

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, answer_text, points FROM answers
            WHERE question_id = ? AND id NOT IN ({})
        """.format(','.join('?' * len(game_state.revealed_answers))),
        [game_state.current_question['id']] + game_state.revealed_answers)

        revealed = []
        for row in cursor.fetchall():
            game_state.revealed_answers.append(row['id'])
            game_state.total_revealed += row['points']
            revealed.append({'id': row['id'], 'text': row['answer_text'], 'points': row['points']})

        return jsonify({
            'success': True,
            'revealed': revealed,
            'game_state': game_state.__dict__
        })
    except Exception as e:
        print(f"Wystąpił błąd podczas obsługi /reveal_all: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/next', methods=['POST'])
def next_question():
    conn = create_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'})

    try:
        if game_state.current_question and game_state.current_question.get('id'):
            mark_question_as_used(conn, game_state.current_question['id'])
        reset_warnings()
        # Resetujemy również listę poprawnych odpowiedzi
        game_state.correct_answers = []
        question = get_random_question(conn)
        if question:
            game_state.current_question = {'id': question['id'], 'question_text': question['question_text']}
            answers = get_question_answers(conn, game_state.current_question['id'])
            game_state.current_question['answers'] = [dict(row) for row in answers]
            game_state.revealed_answers = []
            game_state.total_revealed = 0
            return jsonify({
                'success': True,
                'question': game_state.current_question,
                'game_state': game_state.__dict__
            })
        else:
            return jsonify({'success': False, 'error': 'No questions available'})
    except Exception as e:
        print(f"Wystąpił błąd podczas obsługi /next: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/admin')
def admin_panel():
    conn = create_connection()
    if not conn:
        return "Błąd połączenia z bazą danych"
    cursor = conn.cursor()
    cursor.execute("SELECT id, question_text FROM questions")
    questions = cursor.fetchall()
    conn.close()
    return render_template('admin.html', questions=questions)

@app.route('/admin/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        answers_text = [request.form.get(f'answer_text_{i}').strip() for i in range(1, 6) if request.form.get(f'answer_text_{i}') and request.form.get(f'answer_text_{i}').strip()]

        if question_text and answers_text:
            conn = create_connection()
            if not conn:
                return "Błąd połączenia z bazą danych"
            cursor = conn.cursor()
            cursor.execute("INSERT INTO questions (question_text) VALUES (?)", (question_text,))
            question_id = cursor.lastrowid

            num_answers = len(answers_text)
            base_points = 35 // num_answers if num_answers > 0 else 0
            remainder = 35 % num_answers if num_answers > 0 else 0
            points_per_answer = [base_points + (1 if i < remainder else 0) + random.randint(0, 5) for i in range(num_answers)]
            random.shuffle(points_per_answer)
            total_points = sum(points_per_answer)

            if total_points < 35:
                diff = 35 - total_points
                for i in range(diff):
                    points_per_answer[random.randint(0, len(points_per_answer) - 1)] += 1
                total_points = sum(points_per_answer)
            elif total_points > 100:
                diff = total_points - 100
                for i in range(diff):
                    points_per_answer[random.randint(0, len(points_per_answer) - 1)] = max(0, points_per_answer[random.randint(0, len(points_per_answer) - 1)] - 1)

            for i, ans_text in enumerate(answers_text):
                cursor.execute("INSERT INTO answers (question_id, answer_text, points) VALUES (?, ?, ?)", (question_id, ans_text, points_per_answer[i]))

            conn.commit()
            conn.close()
            return redirect(url_for('admin_panel'))
        else:
            return "Proszę podać treść pytania i co najmniej jedną odpowiedź."
    return render_template('add_question.html')

@app.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    conn = create_connection()
    if not conn:
        return "Błąd połączenia z bazą danych"
    cursor = conn.cursor()

    if request.method == 'POST':
        question_text = request.form['question_text']
        answers_data = []
        for i in range(1, 6):
            answer_text = request.form.get(f'answer_text_{i}')
            points = request.form.get(f'points_{i}', 0, type=int)
            if answer_text and answer_text.strip():
                answers_data.append({'text': answer_text.strip(), 'points': points})

        total_points = sum(ans['points'] for ans in answers_data)
        if 35 <= total_points <= 100 and answers_data:
            cursor.execute("UPDATE questions SET question_text = ? WHERE id = ?", (question_text, question_id))
            cursor.execute("DELETE FROM answers WHERE question_id = ?", (question_id,))
            for answer in answers_data:
                cursor.execute("INSERT INTO answers (question_id, answer_text, points) VALUES (?, ?, ?)", (question_id, answer['text'], answer['points']))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_panel'))
        else:
            conn.close()
            return "Suma punktów odpowiedzi musi być między 35 a 100 i musi być co najmniej jedna odpowiedź."

    cursor.execute("SELECT question_text FROM questions WHERE id = ?", (question_id,))
    question = cursor.fetchone()
    cursor.execute("SELECT id, answer_text, points FROM answers WHERE question_id = ?", (question_id,))
    answers = cursor.fetchall()
    conn.close()
    if question:
        return render_template('edit_question.html', question=question, answers=answers, question_id=question_id)
    else:
        return "Pytanie nie znaleziono."

@app.route('/admin/delete_question/<int:question_id>')
def delete_question(question_id):
    conn = create_connection()
    if not conn:
        return "Błąd połączenia z bazą danych"
    cursor = conn.cursor()
    cursor.execute("DELETE FROM answers WHERE question_id = ?", (question_id,))
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/switch_team', methods=['POST'])
def switch_team_endpoint():
    switch_team()  # Ta funkcja już istnieje w Twoim kodzie
    return jsonify({
        'success': True,
        'game_state': game_state.__dict__
    })

if __name__ == '__main__':
    app.run(debug=True)