from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, join_room, send, emit
from flask_migrate import Migrate
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'b3Xt5Q9Zp2Lm7KfR1yN8vA4jH6uE0cW'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
# main = Blueprint('main', __name__)
socketio = SocketIO(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, default=0)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('leaderboard.html', users=users)


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('game_lobby'))
    else:
        flash("Invalid username or password!")
        return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    if password != confirm_password:
        flash("Passwords don't match!")
        return redirect(url_for('index'))
    elif User.query.filter_by(username=username).first():
        flash("Username already exists!")
        return redirect(url_for('index'))
    else:
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.")
        return redirect(url_for('index'))

@app.route('/game_lobby')
def game_lobby():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('game_lobby.html', username=session['username'])

app.config['SESSION_COOKIE_SECURE'] = True
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

@app.route('/enter_game')
def enter_game():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('game_enter.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@socketio.on('join_game')
def handle_join_game(username):
    join_room('game')
    code, answer = generate_code()
    session['correct_answer'] = answer
    session['guesses'] = 0
    emit('code', code, room='game')
    send(f'{username} has joined the game.', room='game')

@socketio.on('guess')
def handle_guess(guess):
    correct_answer = session.get('correct_answer', '')
    guesses = session.get('guesses', 0)
    
    if guess == correct_answer:
        send(f'{session["username"]}: {guess} (Correct!)', room='game')
        new_code, new_answer = generate_code()
        session['correct_answer'] = new_answer
        session['guesses'] = 0
        emit('code', new_code, room='game')
    else:
        guesses += 1
        session['guesses'] = guesses
        send(f'{session["username"]}: {guess} (Incorrect!)', room='game')
        
        if guesses >= 3:
            send(f'Correct answer was: {correct_answer}', room='game')
            new_code, new_answer = generate_code()
            session['correct_answer'] = new_answer
            session['guesses'] = 0
            emit('code', new_code, room='game')

def generate_code():
    codes = [
        ("def add(a, b):\n    return a + ___", "b"),
        ("for i in range(___):\n    print(i)", "10"),
        ("if ___:\n    print('True')\nelse:\n    print('False')", "a > b"),
    ]
    return random.choice(codes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)

@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('leaderboard.html', users=users)

