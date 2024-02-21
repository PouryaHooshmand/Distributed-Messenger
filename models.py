from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import functions

db = SQLAlchemy()

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False, server_default='Anonymous')
    content = db.Column(db.Text, nullable=False, server_default='')
    posted_at = db.Column(db.DateTime(timezone=True), server_default=functions.now())
    media_links = db.relationship('MediaLink', backref='post')

class MediaLink(db.Model):
    __tablename__ = 'media_links'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(100), nullable=False)

