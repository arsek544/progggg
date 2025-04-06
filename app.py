from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'staem_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///staem.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    purchases = db.relationship('Purchase', backref='user', lazy=True)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    game = db.relationship('Game')

@app.route('/')
def index():
    games = Game.query.all()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('index.html', games=games, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            return 'Username already exists!'
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
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
            return redirect(url_for('index'))
        return 'Invalid credentials!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/add_funds', methods=['POST'])
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    amount = float(request.form['amount'])
    user = User.query.get(session['user_id'])
    user.balance += amount
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/buy/<int:game_id>')
def buy(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    game = Game.query.get(game_id)
    if game.price > user.balance:
        return 'Not enough funds!'
    if Purchase.query.filter_by(user_id=user.id, game_id=game.id).first():
        return 'Game already purchased!'
    user.balance -= game.price
    purchase = Purchase(user_id=user.id, game_id=game.id)
    db.session.add(purchase)
    db.session.commit()
    return redirect(url_for('library'))

@app.route('/library')
def library():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    purchases = Purchase.query.filter_by(user_id=user.id).all()
    games = [purchase.game for purchase in purchases]
    return render_template('library.html', games=games)

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
    with app.app_context():
        init_db()
    app.run(debug=True)
