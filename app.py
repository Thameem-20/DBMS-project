from flask import Flask, render_template, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,SelectField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy.orm import joinedload



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databases.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisanewsecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Turf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turf_name = db.Column(db.String(255), nullable=False)
    turf_location = db.Column(db.String(255), nullable=False)
    turf_phone = db.Column(db.String(15), nullable=True)

    # Relationship with Game
    games = db.relationship('Game', backref='turf', lazy=True)
    reviews = db.relationship('TurfReview', backref='turf', lazy=True)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('turf.id'), nullable=False)
    host_name = db.Column(db.String(255), nullable=False)
    host_phone = db.Column(db.String(15), nullable=True)
    game_time = db.Column(db.DateTime, nullable=False)
    sports = db.Column(db.String(50), nullable=False)

    # Relationship with Player
    players = db.relationship('Player', backref='game', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    player_name = db.Column(db.String(255), nullable=False)
    player_address = db.Column(db.String(255), nullable=False)
    player_phone = db.Column(db.String(15), nullable=True)

class TurfReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('turf.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    
    # Define relationship with User model
    user = db.relationship('User', backref='reviews')


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    email = StringField(validators=[InputRequired(), Email(message="Invalid email"), Length(max=120)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()

        if existing_user_username:
            raise ValidationError("This username already exists, please try a different one.")

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()

        if existing_user_email:
            raise ValidationError("This email address is already registered.")

            
class LoginForm(FlaskForm):
    username_email = StringField(validators=[InputRequired(), Length(min=4, max=120)], render_kw={"placeholder": "Username or Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    review = TextAreaField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username_email.data) | (User.email == form.username_email.data)).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    turfs = Turf.query.all()
    return render_template('dashboard.html', username=current_user.username, turfs=turfs)

@app.route('/register', methods = ['GET','POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data,email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))


    return render_template('register.html', form=form)

from flask import render_template

@app.route('/turf/<int:turf_id>', methods=['GET', 'POST'])
@login_required
def turf_detail(turf_id):
    turf = Turf.query.get_or_404(turf_id)
    hosted_games = turf.games

    return render_template('turf_detail.html', turf=turf, hosted_games=hosted_games)

# host game route
@app.route('/turf/<int:turf_id>/host_game', methods=['GET', 'POST'])
@login_required
def host_game(turf_id):
    turf = Turf.query.get_or_404(turf_id)

    if request.method == 'POST':
        host_name = current_user.username
        host_phone = request.form.get('host_phone')
        game_date = request.form.get('game_date')
        game_time = request.form.get('game_time')
        sports = request.form.get('sports')

        game_datetime_str = f'{game_date} {game_time}'
        game_time = datetime.strptime(game_datetime_str, '%Y-%m-%d %H:%M')

        # Create a new game
        new_game = Game(turf_id=turf.id, host_name=host_name, host_phone=host_phone, game_time=game_time, sports=sports)
        db.session.add(new_game)
        db.session.commit()

        flash('Game hosted successfully!', 'success')
        return redirect(url_for('turf_detail', turf_id=turf.id))

    return render_template('host_game.html', turf=turf)


@app.route('/turf/<int:turf_id>/join_game/<int:game_id>', methods=['GET', 'POST'])
@login_required
def join_game(turf_id, game_id):
    turf = Turf.query.get_or_404(turf_id)
    game = Game.query.get_or_404(game_id)

    if request.method == 'POST':
        player_name = current_user.username
        player_address = request.form.get('player_address')
        player_phone = request.form.get('player_phone')

        # Create a new player for the game
        new_player = Player(game_id=game.id, player_name=player_name, player_address=player_address, player_phone=player_phone)
        db.session.add(new_player)
        db.session.commit()

        flash('Joined the game successfully!', 'success')
        
        # Redirect to the players list after joining the game
        return redirect(url_for('players_list', game_id=game.id))

    return render_template('join_game.html', turf=turf, game=game)

from flask import render_template

@app.route('/game/<int:game_id>/players_list')
@login_required
def players_list(game_id):
    game = Game.query.get_or_404(game_id)
    players = game.players
    return render_template('players_list.html', players=players)

@app.route('/turf/<int:turf_id>/reviews')
def turf_reviews(turf_id):
    turf = Turf.query.get_or_404(turf_id)
    reviews = TurfReview.query.filter_by(turf_id=turf_id).options(joinedload(TurfReview.user)).all()
    return render_template('turf_reviews.html', turf=turf, reviews=reviews)


@app.route('/turf/<int:turf_id>/write_review', methods=['GET', 'POST'])
@login_required
def write_review(turf_id):
    form = ReviewForm()
    turf = Turf.query.get_or_404(turf_id)
    
    if form.validate_on_submit():
        new_review = TurfReview(turf_id=turf.id, user_id=current_user.id,
                                rating=form.rating.data, review_text=form.review.data)
        db.session.add(new_review)
        db.session.commit()
        flash('Your review has been submitted!', 'success')
        return redirect(url_for('turf_reviews', turf_id=turf.id))
    
    return render_template('write_review.html', form=form, turf=turf)


@app.route('/truncate_turf_reviews', methods=['GET'])
def truncate_turf_reviews():
    from models import TurfReview  # Import your TurfReview model
    db.session.query(TurfReview).delete()
    db.session.commit()
    flash('TurfReview table truncated successfully!', 'success')
    return redirect(url_for('home'))



@app.route('/clear_hosted_games', methods=['GET'])
def clear_hosted_games():
    Game.query.delete()
    db.session.commit()

    return 'Hosted games table cleared successfully!'

if __name__ == '__main__':
    if __name__ == '__main__':
        with app.app_context():
            db.create_all()
        app.run(debug=True)

