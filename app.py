from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Password configuration
ADMIN_PASSWORD = "admin123"
HOST_PASSWORD = "host123"

def get_db_connection():
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    password = request.form.get('password', '')
    
    if role == 'admin' and password == ADMIN_PASSWORD:
        session['role'] = 'admin'
        return redirect(url_for('admin'))
    elif role == 'host' and password == HOST_PASSWORD:
        session['role'] = 'host'
        return redirect(url_for('host'))
    elif role == 'player':
        session['role'] = 'player'
        return redirect(url_for('player'))
    else:
        return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin.html')

@app.route('/host')
def host():
    if session.get('role') != 'host':
        return redirect(url_for('index'))
    return render_template('host.html')

@app.route('/player')
def player():
    if session.get('role') != 'player':
        session['role'] = 'player'
    return render_template('player.html')

# API endpoints
@app.route('/api/game_state')
def get_game_state():
    conn = get_db_connection()
    game_state = conn.execute('SELECT * FROM game_state LIMIT 1').fetchone()
    current_question = None
    answers = []
    teams = []
    
    if game_state['current_question_id']:
        current_question = conn.execute('SELECT * FROM questions WHERE id = ?', 
                                      (game_state['current_question_id'],)).fetchone()
        
        # Dla hosta pokazuj punkty ale nie treść ukrytych odpowiedzi
        if session.get('role') == 'host':
            answers = conn.execute('''SELECT id, question_id, points, revealed, 
                                     CASE WHEN revealed = 1 THEN answer ELSE 'Ukryte' END as answer 
                                     FROM answers WHERE question_id = ? ORDER BY points DESC''',
                                  (game_state['current_question_id'],)).fetchall()
        else:
            answers = conn.execute('SELECT * FROM answers WHERE question_id = ? ORDER BY points DESC',
                                  (game_state['current_question_id'],)).fetchall()
    
    teams = conn.execute('SELECT * FROM teams ORDER BY id').fetchall()
    conn.close()
    
    return jsonify({
        'game_active': bool(game_state['game_active']),
        'current_round': game_state['current_round'],
        'round_points': game_state['round_points'],
        'current_question': dict(current_question) if current_question else None,
        'answers': [dict(answer) for answer in answers],
        'teams': [dict(team) for team in teams],
        'user_role': session.get('role')
    })

@app.route('/api/start_game', methods=['POST'])
def start_game():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Brak uprawnień'}), 403

# Analogicznie w innych endpointach
    
    conn = get_db_connection()
    conn.execute('UPDATE game_state SET game_active = 1')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/next_round', methods=['POST'])
def next_round():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    game_state = conn.execute('SELECT * FROM game_state LIMIT 1').fetchone()
    new_round = game_state['current_round'] + 1
    
    # Get a random question for the new round
    question = conn.execute('SELECT * FROM questions WHERE round_number = ? ORDER BY RANDOM() LIMIT 1',
                           (new_round,)).fetchone()
    
    if question:
        conn.execute('UPDATE game_state SET current_round = ?, current_question_id = ?, round_points = 0',
                    (new_round, question['id']))
        # Reset answer states
        conn.execute('UPDATE answers SET revealed = 0 WHERE question_id = ?', (question['id'],))
        # Reset team warnings
        conn.execute('UPDATE teams SET warnings = 0')
    else:
        conn.close()
        return jsonify({'success': False, 'error': 'No questions available for this round'})
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/reveal_answer', methods=['POST'])
def reveal_answer():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    answer_id = request.json.get('answer_id')
    if not answer_id:
        return jsonify({'success': False, 'error': 'Missing answer_id'}), 400
    
    conn = get_db_connection()
    
    # Get answer points
    answer = conn.execute('SELECT points FROM answers WHERE id = ?', (answer_id,)).fetchone()
    if not answer:
        conn.close()
        return jsonify({'success': False, 'error': 'Answer not found'}), 404
    
    # Update answer state
    conn.execute('UPDATE answers SET revealed = 1 WHERE id = ?', (answer_id,))
    
    # Add points to round total
    conn.execute('UPDATE game_state SET round_points = round_points + ?', (answer['points'],))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/award_round_points', methods=['POST'])
def award_round_points():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Brak uprawnień'}), 403
    
    team_id = request.json.get('team_id')
    if not team_id:
        return jsonify({'success': False, 'error': 'Brak ID zespołu'}), 400
    
    conn = get_db_connection()
    try:
        game_state = conn.execute('SELECT round_points FROM game_state LIMIT 1').fetchone()
        points = game_state['round_points'] or 0
        
        if points > 0:
            conn.execute('UPDATE teams SET score = score + ? WHERE id = ?', (points, team_id))
            conn.execute('UPDATE game_state SET round_points = 0')
            conn.commit()
            return jsonify({'success': True, 'points_awarded': points})
        else:
            return jsonify({'success': False, 'error': 'Brak punktów do przyznania'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/reset_round_points', methods=['POST'])
def reset_round_points():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    conn.execute('UPDATE game_state SET round_points = 0')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/add_warning', methods=['POST'])
def add_warning():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Brak uprawnień'}), 403
    
    team_id = request.json.get('team_id')
    if not team_id:
        return jsonify({'success': False, 'error': 'Brak ID zespołu'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE teams SET warnings = warnings + 1 WHERE id = ?', (team_id,))
        conn.commit()
        
        # Zwracamy zaktualizowaną liczbę ostrzeżeń
        updated_warnings = conn.execute('SELECT warnings FROM teams WHERE id = ?', (team_id,)).fetchone()['warnings']
        return jsonify({'success': True, 'warnings': updated_warnings})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()
        
@app.route('/api/update_team_name', methods=['POST'])
def update_team_name():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    team_id = request.json.get('team_id')
    new_name = request.json.get('new_name')
    
    if not team_id or not new_name:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    
    conn = get_db_connection()
    conn.execute('UPDATE teams SET name = ? WHERE id = ?', (new_name, team_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/reset_team_names', methods=['POST'])
def reset_team_names():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    conn.execute('UPDATE teams SET name = "Team A" WHERE id = 1')
    conn.execute('UPDATE teams SET name = "Team B" WHERE id = 2')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)