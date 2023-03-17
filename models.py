from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    typecode = db.Column(db.String(1), nullable=True)
    map_number = db.Column(db.String(), nullable=False)
    area = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    assigned_to = db.Column(db.String(100))
    assigned_date = db.Column(db.DateTime)
    checked_in_date = db.Column(db.DateTime)
    pdf_file = db.Column(db.String(120), nullable=True)

    def __init__(self, id=None, typecode=None, map_number=None, area=None, name=None, assigned_to=None, assigned_date=None, checked_in_date=None, pdf_file=None):
        self.id = id
        self.typecode = typecode
        self.map_number = map_number
        self.area = area
        self.name = name
        self.assigned_to = assigned_to
        self.assigned_date = assigned_date
        self.checked_in_date = checked_in_date
        self.pdf_file = pdf_file

class MapHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typecode = db.Column(db.String(1), nullable=True)
    map_id = db.Column(db.Integer, db.ForeignKey("map.id"), nullable=False)
    map_number = db.Column(db.String(50), nullable=False)
    area = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    assigned_to = db.Column(db.String(100), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)
    checked_in_date = db.Column(db.DateTime, nullable=True)

    def __init__(self, map_id, typecode, map_number, area, name, assigned_to, assigned_date, checked_in_date):
        self.map_id = map_id
        self.typecode = typecode
        self.map_number = map_number
        self.area = area
        self.name = name
        self.assigned_to = assigned_to
        self.assigned_date = assigned_date
        self.checked_in_date = checked_in_date


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f'<User {self.id} {self.name}>'


