from operator import add
import os
import json, requests, copy
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from forms import AddGroupForm, AddCommentForm, AddTagForm, CreateTagForm
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import not_, and_

secrets = json.loads(open('secrets.json').read())


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://au_methods_postgres:Hermes_2014@localhost:5432/au_methods_postgres" ## THIS WORKS FOR POSTGRES
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////mnt/media/a/data/sqlite/site.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.db'
db = SQLAlchemy(app)


import models
import pandas as pd

@app.route('/')
@app.route('/home')
def home():
    projects = models.Project.query.all()
    print(projects)
    return render_template('index.html', projects = projects)

@app.route('/add_collection')
def add_collection():
    return jsonify({})

@app.route('/add_group')
def add_group():
    form = AddGroupForm()
    return render_template('add_group.html')

@app.route('/add_user')
def add_user():
    return jsonify({})

@app.route('/view_document2/<int:project_id>/<int:doc_id>', methods=['POST', 'GET'])
def view_document2(project_id, doc_id):
    doc_data = {}
    the_doc = models.Document.query.get(doc_id)
    ## get tag names for buttons, and for making sure we dont get doublets
    project = models.Project.query.get(project_id)
    tag_names = [t.text for t in project.tags]
    doc_tags = [t.text for t in the_doc.doc_tags]
    add_comment_form = AddCommentForm()
    add_tag_form = AddTagForm()
    create_tag_form = CreateTagForm()
    project_tag_names = [tname for tname in tag_names if tname not in doc_tags]
    doc_tag_names = [tname for tname in doc_tags if tname not in project_tag_names ]
    doc_data['doc_tags'] = doc_tag_names
    doc_data['project_tags'] = project_tag_names
    doc_data['project_id'] = project_id
    if request.method == 'POST' and 'delete_tag' in request.form.to_dict():
        tag_text = request.form.to_dict()['delete_tag']
        the_tag = models.Tag.query.filter_by(text=tag_text, project_id=project.id).first()
        print(the_tag)
        print(the_doc.doc_tags )
        tags = the_doc.doc_tags
        tags.remove(the_tag)
        the_doc.doc_tags = tags
        db.session.add(the_doc)
        db.session.commit()
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    if request.method == 'POST' and 'add_tag' in request.form.to_dict():
        tag_text = request.form.to_dict()['add_tag']
        the_tag = models.Tag.query.filter_by(text=tag_text).first()
        the_doc.doc_tags = the_doc.doc_tags + [the_tag]
        db.session.add(the_doc)
        db.session.commit()
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    if request.method == 'POST' and 'submit_tag_name' in request.form.to_dict():
        print("new tag")
        the_tag_text = create_tag_form.tag_name.data.strip().lower()
        the_tag_text = the_tag_text.replace(" ", "_")
        new_tag = models.Tag(text=the_tag_text, project_id=c.project_id)
        print(tag_names)
        if the_tag_text not in tag_names:
            db.session.add(new_tag)
            db.session.commit()
        create_tag_form.tag_name.data = ''
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    if request.method == 'POST' and 'submit_comment' in request.form.to_dict():
        the_comment = add_comment_form.text.data
        new_comment = models.Comment(text=the_comment, project_id = c.project_id, doc_id=the_doc.id)
        db.session.add(new_comment)
        db.session.commit()
        print("Collection", c.id, "doc", doc_id)
        add_comment_form.text.data = ""
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    return render_template('view_document.html', document=the_doc, comment_form = add_comment_form, add_tag_form=add_tag_form, create_tag_form=create_tag_form, doc_data=doc_data)
@app.route('/view_document/<int:collection>/<int:doc_id>', methods=['POST', 'GET'])
def view_document(collection, doc_id):
    doc_data = {}
    c = models.Collection.query.get(collection)
    the_doc = c.documents.filter_by(id=doc_id).first()
    headings = sorted(list(the_doc.data.keys()))
    ## get tag names for buttons, and for making sure we dont get doublets
    project = models.Project.query.get(c.project_id)
    tag_names = [t.text for t in project.tags]
    doc_tags = [t.text for t in the_doc.doc_tags]
    add_comment_form = AddCommentForm()
    add_tag_form = AddTagForm()
    create_tag_form = CreateTagForm()
    project_tag_names = [tname for tname in tag_names if tname not in doc_tags]
    doc_tag_names = [tname for tname in doc_tags if tname not in project_tag_names ]
    doc_data['doc_tags'] = doc_tag_names
    doc_data['project_tags'] = project_tag_names
    if request.method == 'POST' and 'delete_tag' in request.form.to_dict():
        tag_text = request.form.to_dict()['delete_tag']
        the_tag = models.Tag.query.filter_by(text=tag_text, project_id=project.id).first()
        print(the_tag)
        print(the_doc.doc_tags )
        tags = the_doc.doc_tags
        tags.remove(the_tag)
        the_doc.doc_tags = tags
        db.session.add(the_doc)
        db.session.commit()
        return redirect(url_for('view_document', collection=collection, doc_id=doc_id ))
    if request.method == 'POST' and 'add_tag' in request.form.to_dict():
        tag_text = request.form.to_dict()['add_tag']
        the_tag = models.Tag.query.filter_by(text=tag_text).first()
        the_doc.doc_tags = the_doc.doc_tags + [the_tag]
        db.session.add(the_doc)
        db.session.commit()
        return redirect(url_for('view_document', collection=collection, doc_id=doc_id ))
    if request.method == 'POST' and 'submit_tag_name' in request.form.to_dict():
        print("new tag")
        the_tag_text = create_tag_form.tag_name.data.strip().lower()
        the_tag_text = the_tag_text.replace(" ", "_")
        new_tag = models.Tag(text=the_tag_text, project_id=c.project_id)
        print(tag_names)
        if the_tag_text not in tag_names:
            db.session.add(new_tag)
            db.session.commit()
        create_tag_form.tag_name.data = ''
        return redirect(url_for('view_document', collection=collection, doc_id=doc_id ))
    if request.method == 'POST' and 'submit_comment' in request.form.to_dict():
        the_comment = add_comment_form.text.data
        new_comment = models.Comment(text=the_comment, project_id = c.project_id, doc_id=the_doc.id)
        db.session.add(new_comment)
        db.session.commit()
        print("Collection", c.id, "doc", doc_id)
        add_comment_form.text.data = ""
        return redirect(url_for('view_document', collection=collection, doc_id=doc_id ))
    return render_template('view_document.html', document=the_doc, comment_form = add_comment_form, add_tag_form=add_tag_form, create_tag_form=create_tag_form, doc_data=doc_data)

@app.route('/filter_collection/<int:collection>/<string:contains>/<string:excludes>/<int:page_start>', methods=["POST", "GET"])
def filter_collection(collection, contains, excludes, page_start):
    contained_words = contains.split(",") if len(contains) > 1 else []
    excluded_words = excludes.split(",") if len(excludes) > 1 else []
    print(contained_words)
    print(excluded_words)
    print(models.Collection.query.all())
    c = models.Collection.query.get(collection)
    query = c.documents
    if len(contained_words) > 0:
        for w in contained_words:
            query = query.filter(models.Document.data['reviewText'].contains(w))
    if len(excluded_words) > 0:
        for w in excluded_words:
            query = query.filter(not_(models.Document.data['reviewText'].contains(w)))
    docs = [d.data.update({'id' : d.id}) for d in query.paginate(page_start, 25).items]
    print(docs)
    return jsonify(docs)

@app.route('/view_tag/<int:tag_id>/<int:page_start>', methods=["POST", "GET"])
def view_tag(tag_id, page_start):
    tag = models.Tag.query.get(tag_id)
    docs = [d.data for d in tag.tag_docs.paginate(page_start, 25).items]
    doc_ids = [d.id for d in tag.tag_docs.paginate(page_start, 25).items]
    for n, doc in enumerate(docs):
        doc['id'] = doc_ids[n]
    headings = sorted(list(set([key for doc in docs for key in doc.keys()])))
    return render_template('view_tag.html', table = docs, table_name = 'documents', headings=headings, project_id=tag.project_id, tag_name=tag.text)

@app.route('/view_collection/<int:collection>/<int:page_start>', methods=["POST", "GET"])
def view_collection(collection, page_start):
    c = models.Collection.query.get(collection)
    p = models.Project.query.get(c.project_id)
    docs = [d.data for d in c.documents.paginate(page_start, 25).items]
    doc_ids = [d.id for d in c.documents.paginate(page_start, 25).items]
    for n, doc in enumerate(docs):
        doc['id'] = doc_ids[n]
    # docs = [d.data for d in c.documents.paginate(page_start, 25).items]
    collections_data = [{'collection_id' : c.id, 'entries' : c.documents.count(), 'collection_name' : c.name} for c in p.collections]
    headings = sorted(list(set([key for doc in docs for key in doc.keys()])))
    return render_template('view_collection.html', table = docs, table_name = 'documents', headings=headings, project_id=p.id)

@app.route('/project/<int:project_id>', methods=['POST', 'GET'])
def project(project_id):
    p = models.Project.query.get(project_id)
    collections_data = [{'collection_id' : c.id, 'entries' : c.documents.count(), 'collection_name' : c.name} for c in p.collections]
    return render_template('project.html', project=p, collections_data=collections_data)


app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)
