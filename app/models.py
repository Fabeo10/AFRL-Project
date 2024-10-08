from datetime import datetime, timezone, timedelta
from app import db, login_manager
from flask_login import UserMixin
from flask import current_app
import jwt

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    birth_date = db.Column(db.Date)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    gender = db.Column(db.String(10), nullable=False)
    pronouns = db.Column(db.String(30))
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    messages = db.relationship('ChatMessage', backref='author', lazy=True)
    is_profile_complete = db.Column(db.Boolean, default=False)
    test_sessions = db.relationship('TestSession', backref='user', lazy=True)
    openness = db.Column(db.Integer, nullable=True)
    conscientiousness = db.Column(db.Integer, nullable=True)
    extraversion = db.Column(db.Integer, nullable=True)
    agreeableness = db.Column(db.Integer, nullable=True)
    neuroticism = db.Column(db.Integer, nullable=True)
    investment_profile = db.Column(db.String(50), nullable=True) 
    totp_secret = db.Column(db.String(16), nullable=True) 
    tf_active = db.Column(db.Boolean(), nullable=True)
    is_tf_complete = db.Column(db.Boolean(), default=False)
    last_tf = db.Column(db.DateTime)
    last_password_renewal = db.Column(db.DateTime)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.gender}', '{self.image_file}')"

    # Generates a secure token with the user's id 
    def get_token(self):
        token = jwt.encode({
            "exp" : datetime.utcnow() + timedelta(minutes = 30),
            "user_id" : self.id
        }, current_app.config['SECRET_KEY'], algorithm = 'HS256')
        return token
    
    # Decodes and verifies the token and returns the corresponding user ID
    def verify_token(token):
        try:
            decode = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms='HS256')
        except jwt.ExpiredSignatureError:
            return "Token has expired. Please restart the reset password process."
        except jwt.InvalidTokenError:
            return "Token is invalid. Please try again."
        return User.query.get(decode['user_id'])

class ChatMessage(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(140), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    is_user = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"ChatMessage('{self.message}', '{self.timestamp}')"
    
class TestSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    acknowledgement = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"TestSession(user_id={self.user_id}, acknowledgement={self.acknowledgement}, timestamp={self.timestamp})"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(140), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.content}', '{self.timestamp}')"