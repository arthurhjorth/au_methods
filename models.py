from datetime import datetime
from sqlalchemy.orm import deferred
from app import db, app
from sqlalchemy.types import JSON
from flask_login import UserMixin
from flask_login import login_user, current_user, logout_user, login_required



# collection_families = db.Table('collection_families',
#     db.Column('parent_ids', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
#     db.Column('children_ids', db.Integer, db.ForeignKey('collection.id'), primary_key=True)
# )


document_tags = db.Table('document_tags',
    db.Column('document_id', db.Integer, db.ForeignKey('document.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)



class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    collections = db.relationship('Collection')
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    tags = db.relationship('Tag')
    comments = db.relationship('Comment')
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Collection(db.Model):
    __tablename__ = 'collection'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    documents = db.relationship('Document', backref='document.id', lazy='dynamic')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    filters = db.Column(JSON, default={})
    headings = db.Column(JSON, default=[])
    collection_tags = db.Column(JSON, default=[])
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'document'
    id = db.Column(db.Integer, primary_key=True)
    data = deferred(db.Column(JSON, default = {}))
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    doc_tags = db.relationship('Tag', secondary=document_tags, lazy='subquery',
        backref=db.backref('tag_docs', lazy='dynamic'))
    doc_comments = db.relationship('Comment')

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(25), unique=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000))
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    doc_id = db.Column(db.Integer, db.ForeignKey('document.id'))

class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15))
    users = db.relationship('User', backref='group', lazy=True)
    projects = db.relationship('Project', backref='group', lazy='dynamic')
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
        backref=db.backref('users', lazy=True))
    
    def get_user_projects(self):
        g = Group.query.get(self.group_id)
        return g.projects

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15))
