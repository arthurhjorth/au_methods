from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import deferred
from app import db, app
from sqlalchemy.types import JSON
from flask_login import UserMixin




user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = deferred(db.Column(JSON, default = {}))
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    documents = db.relationship('Document', backref='collection', lazy='dynamic')
    ## make a one to many  parents
    # and a one to many children
    # parents 

# class Tag(db.Model):
#     id = db.column(db.Integer, primary_key=True)
#     text = db.Column(db.String(25))
#     documents = db.relationship('Document', backref='collection', lazy=True)

# ### change this to one to many
# class Comment(db.Model):
#     id = db.column(db.Integer, primary_key=True)
#     text = db.Column(db.String(500))
#     # documents = db.relationship('Document', backref='collection', lazy=True)

class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15))
    users = db.relationship('User', backref='group', lazy=True)




class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
        backref=db.backref('users', lazy=True))

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15))
