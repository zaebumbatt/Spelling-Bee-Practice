import sqlite3
from functools import wraps
from tempfile import mkdtemp

from flask import (Flask, flash, json, redirect, render_template, request,
                   session)
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

app.config['SESSION_FILE_DIR'] = mkdtemp()
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute(
    'CREATE TABLE IF NOT EXISTS users '
    '(user_id integer PRIMARY KEY, '
    'username text NOT NULL, '
    'hash text NOT NULL)'
)
c.execute(
    'CREATE TABLE IF NOT EXISTS results '
    '(result_id integer PRIMARY KEY, '
    'user_id integer NOT NULL, '
    'word text NOT NULL, '
    'difficulty text NOT NULL, '
    'result text NOT NULL, '
    'FOREIGN KEY (user_id) REFERENCES users(user_id))'
)
conn.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated_function


words = set()


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        answer = request.get_json()
        user_id = session['user_id']
        difficulty = answer.get('difficulty')
        if answer.get('correct'):
            word = answer.get('correct')
            result = 'correct'
        if answer.get('incorrect'):
            word = answer.get('incorrect')
            result = 'incorrect'
        if word not in words:
            words.add(word)
            with sqlite3.connect('database.db') as conn:
                c = conn.cursor()
                c.execute(
                    'INSERT INTO results (user_id, word, difficulty, result) '
                    'VALUES (?, ?, ?, ?)',
                    (user_id, word, difficulty, result)
                )
                conn.commit()
    beginner_questions = []
    with open('beginner.txt', 'r') as file1:
        for word in file1:
            beginner_questions.append(word.strip())

    intermediate_questions = []
    with open('intermediate.txt', 'r') as file2:
        for word in file2:
            intermediate_questions.append(word.strip())

    advanced_questions = []
    with open('advanced.txt', 'r') as file1:
        for word in file1:
            advanced_questions.append(word.strip())

    beginner_questions = json.dumps(beginner_questions)
    intermediate_questions = json.dumps(intermediate_questions)
    advanced_questions = json.dumps(advanced_questions)

    return render_template(
        'index.html',
        beginner=beginner_questions,
        intermediate=intermediate_questions,
        advanced=advanced_questions
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        row = c.execute('SELECT * FROM users')
        users = [x[1] for x in row]

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            row = c.execute(
                'SELECT * FROM users WHERE username=?',
                (username,)
            )
            result = row.fetchone()
            if check_password_hash(result[2], password):
                session['user_id'] = result[0]
                flash('You were successfully logged in!')
                return redirect('/')
            conn.commit()

    users = json.dumps(users)
    return render_template('login.html', users=users)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        row = c.execute('SELECT * FROM users')
        users = [x[1] for x in row]

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hash_pass = generate_password_hash(password)

        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO users (username, hash) '
                'VALUES (?, ?)',
                (username, hash_pass)
            )
            conn.commit()
            row = c.execute(
                'SELECT * FROM users WHERE username=?',
                (username,)
            )
            result = row.fetchone()
        session['user_id'] = result[0]
        flash('You were successfully registered!')
        return redirect('/')
    return render_template('register.html', users=users)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user_id = session['user_id']
        old_password = request.form.get('old_password')
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            row = c.execute(
                'SELECT hash FROM users WHERE user_id=?',
                (user_id,)
            )
            conn.commit()
        result = row.fetchone()
        if not check_password_hash(result[0], old_password):
            flash('Wrong old password!')
            return redirect('/change_password')

        password = request.form.get('password')
        hash_pass = generate_password_hash(password)

        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute(
                'UPDATE users SET hash=? WHERE user_id=?',
                (hash_pass, user_id)
            )
            conn.commit()
        flash('You were successfully changed password!')
        return redirect('/')
    return render_template('change_password.html')


@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    results = ['correct', 'incorrect']
    info = {}
    for result in results:
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            info[result] = c.execute(
                'SELECT word, difficulty FROM results '
                'WHERE user_id=? AND result=?',
                (user_id, result)
            ).fetchall()
    len_correct = len(info['correct'])
    len_incorrect = len(info['incorrect'])
    if len_correct + len_incorrect != 0:
        overall = round((len_correct / (len_correct + len_incorrect)) * 100, 1)
    else:
        overall = 0
    beginner_correct = [
        info[0] for info in info['correct'] if info[1] == 'beginner'
    ]
    intermediate_correct = [
        info[0] for info in info['correct'] if info[1] == 'intermediate'
    ]
    advanced_correct = [
        info[0] for info in info['correct'] if info[1] == 'advanced'
    ]
    beginner_incorrect = [
        info[0] for info in info['incorrect'] if info[1] == 'beginner'
    ]
    intermediate_incorrect = [
        info[0] for info in info['incorrect'] if info[1] == 'intermediate'
    ]
    advanced_incorrect = [
        info[0] for info in info['incorrect'] if info[1] == 'advanced'
    ]
    return render_template(
        'profile.html',
        beginner_correct=beginner_correct,
        intermediate_correct=intermediate_correct,
        advanced_correct=advanced_correct,
        beginner_incorrect=beginner_incorrect,
        intermediate_incorrect=intermediate_incorrect,
        advanced_incorrect=advanced_incorrect,
        overall=overall
    )


@app.route('/about')
@login_required
def about():
    return render_template('about.html')
