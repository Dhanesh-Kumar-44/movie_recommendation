from models.system import BaseModel
# from main import db
from .db import db
import sqlalchemy as sa


class User(BaseModel):
    # TODO: make it so that people can only edit users if they have
    # permission, but that anyone can create a user.
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    username = db.Column(db.String(30))
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))

class Movie(BaseModel):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    movie_id = db.Column(db.String(255))
    title = db.Column(db.String(30))
    rating = db.Column(db.String(30))