import time

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app import db, login

class Trip(db.Model):
    """Contains all information about a trip"""
    __tablename__ = 'trips'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    photo_url = db.Column(db.String())
    published = db.Column(db.String())

    def __init__(self, name, photo_url, published):
        self.name = name
        self.photo_url = photo_url
        self.published = published

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'photo_url': self.photo_url,
            'published':self.published
        }

class Adventure(db.Model):
    """Related to what we did on a specific day"""
    __tablename__ = 'adventures'

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer())
    name = db.Column(db.String())
    summary = db.Column(db.String())
    published = db.Column(db.String())

    def __init__(self, trip_id, name, summary, published):
        self.trip_id = trip_id
        self.name = name
        self.summary = summary
        self.published = published

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def serialize(self):
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'name': self.name,
            'summary': self.summary,
            'published':self.published
        }


class Location(db.Model):
    """Related to what we did at a specific site"""
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    adventure_id = db.Column(db.Integer())
    name = db.Column(db.String())
    summary = db.Column(db.String())
    visit_time = db.Column(db.String())

    def __init__(self, name, summary, visit_time, adventure_id):
        self.name = name
        self.summary = summary
        self.visit_time = visit_time
        self.adventure_id = adventure_id

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'summary': self.summary,
            'visit_time': self.visit_time,
            'adventure_id': self.adventure_id
        }

class Photo(db.Model):
    """Photos that describe the location"""
    __tablename__ = 'photos'

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer)
    subtitle = db.Column(db.String())
    photo_url = db.Column(db.String())

    def __init__(self, location_id, subtitle, photo_url):
        self.location_id = location_id
        self.subtitle = subtitle
        self.photo_url = photo_url

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def serialize(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'subtitle': self.subtitle,
            'photo_url': self.photo_url
        }

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    """Users that can modify the site"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String())
    password_hash = db.Column(db.String())

    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def serialize(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'subtitle': self.subtitle,
            'photo_url': self.photo_url
        }
