
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'staem-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///staem.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    games = db.relationship('Game', secondary='library')

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    image_url = db.Column(db.String(300))
    price = db.Column(db.Float)

class Library(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    all_games = Game.query.all()
    owned_games = {g.id for g in user.games}
    return render_template('index.html', user=user, games=all_games, owned_games=owned_games)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/buy/<int:game_id>')
def buy(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    game = Game.query.get(game_id)
    if game in user.games:
        flash('Already owned')
    elif user.balance >= game.price:
        user.games.append(game)
        user.balance -= game.price
        db.session.commit()
        flash(f'You bought {game.name}')
    else:
        flash('Not enough money')
    return redirect(url_for('home'))

@app.route('/topup', methods=['POST'])
def topup():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    amount = float(request.form['amount'])
    user = User.query.get(session['user_id'])
    user.balance += amount
    db.session.commit()
    return redirect(url_for('home'))

@app.before_first_request
def init_db():
    db.create_all()
    if not Game.query.first():
        games = [
            Game(name='Fortnite', image_url='https://upload.wikimedia.org/wikipedia/en/thumb/0/09/Fortnite_cover.jpg/220px-Fortnite_cover.jpg', price=0.0),
            Game(name='Minecraft', image_url='https://upload.wikimedia.org/wikipedia/en/5/51/Minecraft_cover.png', price=26.95),
            Game(name='Terraria', image_url='https://upload.wikimedia.org/wikipedia/en/1/1e/Terraria_Steam_artwork.jpg', price=9.99),
            Game(name='Rust', image_url='https://upload.wikimedia.org/wikipedia/en/7/70/Rust_coverart.jpg', price=39.99),
            Game(name='Dota 2', image_url='https://upload.wikimedia.org/wikipedia/en/6/6d/Dota_2_cover.jpg', price=0.0),
        ]
        db.session.add_all(games)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
