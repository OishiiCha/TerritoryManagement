from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    typecode = db.Column(db.String(1), nullable=True)
    map_number = db.Column(db.Integer(), nullable=False)
    area = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    assigned_to = db.Column(db.String(100))
    assigned_date = db.Column(db.DateTime)
    checked_in_date = db.Column(db.DateTime)
    pdf_file = db.Column(db.String(120), nullable=True)
    pdf_data = db.Column(db.LargeBinary, nullable=True)

    def __init__(self, id=None, typecode=None, map_number=None, area=None, name=None, assigned_to=None, assigned_date=None, checked_in_date=None, pdf_file=None, pdf_data=None):
        self.id = id
        self.typecode = typecode
        self.map_number = map_number
        self.area = area
        self.name = name
        self.assigned_to = assigned_to
        self.assigned_date = assigned_date
        self.checked_in_date = checked_in_date
        self.pdf_file = pdf_file
        self.pdf_data = pdf_data

class MapHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typecode = db.Column(db.String(1), nullable=True)
    map_id = db.Column(db.Integer, db.ForeignKey("map.id"), nullable=False)
    map_number = db.Column(db.Integer(), nullable=False)
    area = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=True)
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
    email = db.Column(db.String(100), nullable=True)
    def __repr__(self):
        return f'<User {self.id} {self.name}>'


class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typecode = db.Column(db.String(1), nullable=True)
    map_id = db.Column(db.Integer, db.ForeignKey("map.id"), nullable=False)
    map_number = db.Column(db.Integer(), nullable=False)
    notes = db.Column(db.Integer(), nullable=True)

    def __init__(self, map_id, typecode, map_number, notes):
        self.map_id = map_id
        self.typecode = typecode
        self.map_number = map_number
        self.notes = notes

class Streets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typecode = db.Column(db.String(1), nullable=True)
    map_id = db.Column(db.Integer, db.ForeignKey("map.id"), nullable=False)
    map_number = db.Column(db.Integer(), nullable=False)
    street = db.Column(db.String(20), nullable=False)
    postcode = db.Column(db.String(10), nullable=True)

    def __init__(self, map_id, typecode, map_number, street, postcode):
        self.map_id = map_id
        self.typecode = typecode
        self.map_number = map_number
        self.street = street
        self.postcode = postcode

class DNC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typecode = db.Column(db.String(1), nullable=True)
    map_id = db.Column(db.Integer, db.ForeignKey("map.id"), nullable=False)
    map_number = db.Column(db.Integer(), nullable=False)
    street = db.Column(db.String(50), nullable=False)
    house_number = db.Column(db.String(50), nullable=True)

    def __init__(self, map_id, typecode, map_number, street, house_number):
        self.map_id = map_id
        self.typecode = typecode
        self.map_number = map_number
        self.street = street
        self.house_number = house_number

