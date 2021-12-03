from datetime import datetime
from sqlalchemy.orm import deferred
import app
# from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.types import JSON
from flask_login import UserMixin
from flask_login import login_user, current_user, logout_user, login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer



# collection_families = app.db.Table('collection_families',
#     app.db.Column('parent_ids', app.db.Integer, app.db.ForeignKey('collection.id'), primary_key=True),
#     app.db.Column('children_ids', app.db.Integer, app.db.ForeignKey('collection.id'), primary_key=True)
# )
@app.login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

collection_documents = app.db.Table('collection_document',
    app.db.Column('document_id', app.db.Integer, app.db.ForeignKey('document.id'), primary_key=True),
    app.db.Column('collection_id', app.db.Integer, app.db.ForeignKey('collection.id'), primary_key=True)
)

document_tags = app.db.Table('document_tags',
    app.db.Column('document_id', app.db.Integer, app.db.ForeignKey('document.id'), primary_key=True),
    app.db.Column('tag_id', app.db.Integer, app.db.ForeignKey('tag.id'), primary_key=True)
)

user_roles = app.db.Table('user_roles',
    app.db.Column('user_id', app.db.Integer, app.db.ForeignKey('user.id'), primary_key=True),
    app.db.Column('role_id', app.db.Integer, app.db.ForeignKey('role.id'), primary_key=True)
)

class Analysis(app.db.Model):
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(25))
    group_id = app.db.Column(app.db.Integer, app.db.ForeignKey('group.id'))
    project_id = app.db.Column(app.db.Integer, app.db.ForeignKey('project.id'))
    data = app.db.Column(JSON, default={})
    reflections = app.db.Column(app.db.String(2000))
    name = app.db.Column(app.db.String(25))

class Project(app.db.Model):
    __tablename__ = 'project'
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(25))
    collections = app.db.relationship('Collection')
    group_id = app.db.Column(app.db.Integer, app.db.ForeignKey('group.id'))
    tags = app.db.relationship('Tag')
    comments = app.db.relationship('Comment')
    time_created = app.db.Column(app.db.DateTime, nullable=False, default=datetime.utcnow)


class Collection(app.db.Model):
    __tablename__ = 'collection'
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(25), default='Unnamed')
    documents = app.db.relationship('Document', secondary=collection_documents, lazy='dynamic',
        backref=app.db.backref('collections', lazy='dynamic'))
    project_id = app.db.Column(app.db.Integer, app.db.ForeignKey('project.id'))
    filters = app.db.Column(JSON, default={})
    headings = app.db.Column(JSON, default=[])
    parent_id = app.db.Column(app.db.Integer, app.db.ForeignKey('collection.id'))
    parent_filters = app.db.Column(JSON, default={})
    collection_tags = app.db.Column(JSON, default=[])
    analysis_results = app.db.Column(JSON, default={})
    time_created = app.db.Column(app.db.DateTime, nullable=False, default=datetime.utcnow)
    hidden = app.db.Column(app.db.Boolean, default=False)
    doc_count = app.db.Column(app.db.Integer, default=0)

class Document(app.db.Model):
    __tablename__ = 'document'
    id = app.db.Column(app.db.Integer, primary_key=True)
    data = deferred(app.db.Column(JSON, default = {}))
    collection_id = app.db.Column(app.db.Integer, app.db.ForeignKey('collection.id'), nullable=False)
    doc_tags = app.db.relationship('Tag', secondary=document_tags, lazy='subquery',
        backref=app.db.backref('tag_docs', lazy='dynamic'))
    doc_comments = app.db.relationship('Comment')

class Tag(app.db.Model):
    __tablename__ = 'tag'
    id = app.db.Column(app.db.Integer, primary_key=True)
    text = app.db.Column(app.db.String(25), unique=True)
    project_id = app.db.Column(app.db.Integer, app.db.ForeignKey('project.id'))
    time_created = app.db.Column(app.db.DateTime, nullable=False, default=datetime.utcnow)

class Comment(app.db.Model):
    __tablename__ = 'comment'
    id = app.db.Column(app.db.Integer, primary_key=True)
    text = app.db.Column(app.db.String(1000))
    user_id = app.db.Column(app.db.Integer, app.db.ForeignKey('user.id'))
    time_created = app.db.Column(app.db.DateTime, nullable=False, default=datetime.utcnow)
    project_id = app.db.Column(app.db.Integer, app.db.ForeignKey('project.id'))
    doc_id = app.db.Column(app.db.Integer, app.db.ForeignKey('document.id'))

class Group(app.db.Model):
    __tablename__ = 'group'
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(15))
    users = app.db.relationship('User', backref='group', lazy=True)
    projects = app.db.relationship('Project', backref='group', lazy='dynamic')
    time_created = app.db.Column(app.db.DateTime, nullable=False, default=datetime.utcnow)


class User(app.db.Model, UserMixin):
    __tablename__ = 'user'
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(25))
    group_id = app.db.Column(app.db.Integer, app.db.ForeignKey('group.id'))
    comments = app.db.relationship('Comment', backref='user', lazy='dynamic')
    email = app.db.Column(app.db.String(120), unique=True)
    password = app.db.Column(app.db.String(60), nullable=False)
    admin = app.db.Column(app.db.Boolean, default=False)
    roles = app.db.relationship('Role', secondary=user_roles, lazy='subquery',
        backref=app.db.backref('users', lazy=True))

    def get_user_projects(self):
        g = Group.query.get(self.group_id)
        return g.projects

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.image_file}')"

class Role(app.db.Model):
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String(15))
