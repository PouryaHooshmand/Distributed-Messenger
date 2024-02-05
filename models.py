from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import functions
from flask_user import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime())

    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    language = db.Column(db.String(100, collation='NOCASE'), server_default='en')


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False, server_default='')
    posted_at = db.Column(db.DateTime(timezone=True), server_default=functions.now())
    media_links = db.relationship('MediaLink', backref='post')

class MediaLink(db.Model):
    __tablename__ = 'media_links'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(100), nullable=False)

