from operator import add
import os
import json, requests, copy
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from sqlalchemy.sql.expression import or_
from flask_sqlalchemy import SQLAlchemy
from forms import AddGroupForm, AddCommentForm, AddTagForm, CreateFilteredCollectionForm, CreateTagForm, FilterForm, LoginForm, RegistrationForm, FilterForm2
from flask_login import login_user, current_user, logout_user, login_required, LoginManager
from sqlalchemy import not_, and_
from flask_bcrypt import Bcrypt
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text
from flask_migrate import Migrate
secrets = json.loads(open('secrets.json').read())

app = Flask(__name__)
print(type(secrets))
print(secrets['SECRET_KEY'])
# app.config['SECRET_KEY'] = secrets['secretkey']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
migrate = Migrate(app, db)

import models
import pandas as pd



# @login_manager.user_loader
# def load_user(user_id):
#     return models.User.query.get(user_id)

@app.route('/')
@app.route('/home')
@login_required
@login_required
def home():
    projects = user_projects()
    return render_template('index.html', projects = projects)


@app.route('/add_collection')
@login_required
def add_collection():
    return jsonify({})

@app.route('/add_group')
@login_required
def add_group():
    form = AddGroupForm()
    return render_template('add_group.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)



@app.route('/reset_request')
def reset_request():
    return jsonify({})

@app.route('/add_user')
@login_required
def add_user():
    return jsonify({})

@app.route('/view_document2/<int:project_id>/<int:doc_id>', methods=['POST', 'GET'])
@login_required
def view_document2(project_id, doc_id):
    if not user_allowed_in_project(project_id):
        return redirect(url_for('home'))
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
        # print(the_tag)
        # print(the_doc.doc_tags )
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
        # print("new tag")
        the_tag_text = create_tag_form.tag_name.data.strip().lower()
        the_tag_text = the_tag_text.replace(" ", "_")
        new_tag = models.Tag(text=the_tag_text, project_id=project_id)
        # print(tag_names)
        if the_tag_text not in tag_names:
            db.session.add(new_tag)
            db.session.commit()
        create_tag_form.tag_name.data = ''
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    if request.method == 'POST' and 'submit_comment' in request.form.to_dict():
        the_comment = add_comment_form.text.data
        new_comment = models.Comment(text=the_comment, project_id = project_id, doc_id=the_doc.id, user_id = current_user.id)
        db.session.add(new_comment)
        db.session.commit()
        add_comment_form.text.data = ""
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    doc_data['comments'] = [(models.User.query.get(c.user_id).name, c.text) for c in the_doc.doc_comments]
    return render_template('view_document.html', project_id = project_id, document=the_doc, comment_form = add_comment_form, add_tag_form=add_tag_form, create_tag_form=create_tag_form, doc_data=doc_data)


@app.route('/try_filters2/<int:collection>', methods=["POST", "GET"])
@login_required
def try_filters2(collection):
    c = models.Collection.query.get(collection)
    if c.documents.count() != 0:
        new_collection = models.Collection(parent_filters=c.filters, parent_id = c.id, project_id = c.project_id, headings=c.headings)
        db.session.add(new_collection)
        db.session.commit()
        return redirect(url_for('try_filters2', collection=new_collection.id))
    existing_filters = c.filters
    filters_list = []
    filters_string = ""
    arg_filters = request.args.to_dict().get('filters', "")
    if len(arg_filters) > 0:
        filter_tokens = arg_filters.split(",")
        filters_list = [filter_tokens[n:n+3] for n in range(0, len(filter_tokens), 3)]
        # filters_string = ",".join(w for sl in filters_list for w in sl )

    filter_form = FilterForm2()
    filter_form.field_name.choices = [( str(fieldname), str(fieldname) ) for fieldname in c.headings]
    operations = ['contains text', 'does not contain text', 'greater than', 'less than', 'equals']#, 'document has this field', 'document does not have this field']
    # operations = ['contains text', 'does not contain text', 'greater than', 'less than', 'equals', 'document has this field', 'document does not have this field']
    filter_form.operator.choices = [( str(op), str(op) ) for op in operations]
    # print(request.form.to_dict())
    if request.method == 'POST':
        post_dict = request.form.to_dict()
        # print(post_dict)
        if 'add_filter' in post_dict:
            new_filter = [post_dict['field_name'], post_dict['operator'], post_dict['filter_data']]
            new_filters = ",".join(w for w in new_filter)
            filters_string = filters_string+new_filters
            filters_dict = c.filters
            field_filter = filters_dict.get(post_dict['field_name'], [])
            field_filter.append([post_dict['operator'], post_dict['filter_data']])
            filters_dict[post_dict['field_name']] = field_filter
            flag_modified(c, "filters") 
            db.session.add(c)
            db.session.merge(c)
            db.session.flush()
            db.session.commit()
            # arg_filters.append(new_filter)
            return redirect(url_for('try_filters2', collection = c.id, filters=filters_string))
        if 'apply_filter' in post_dict:
            parent_collection = models.Collection.query.get(c.parent_id)
            query = parent_collection.documents
            for field_name, filterdata in c.filters.items():
                for f in filterdata:
                    operator = f[0]
                    operand = f[1]
                    if operator == 'contains text':
                        ## we want to be able to do OR
                        if "," in operand:
                            or_words = operand.split(",")
                            or_words = [word.strip().lower() for word in or_words]
                            query_filters = [models.Document.data[field_name].contains(word)  for word in or_words]
                            query = query.filter(or_(*query_filters))
                        else:
                            query = query.filter(models.Document.data[field_name].contains(operand))
                    if operator == 'does not contain text':
                        query = query.filter(not_(models.Document.data[field_name].contains(operand)))
            ## because casting to int doesnt work, ,we do these by creating a list and just filtring through each of them.
            new_collection_docs = []
            for d in query.all():
                doc_data = d.data
                include_doc = True
                for field_name, filterdata in c.filters.items():
                    if field_name not in doc_data:
                        include_doc = False
                    if include_doc:
                        for f in filterdata:
                            operator = f[0]
                            ## we only want key value pairs that relate to mathematical operations here. 
                            if operator in ['greater than', 'less than', 'equals']:
                                operand = float(f[1])
                                field_value = doc_data[field_name]
                                try:
                                    field_value = float(field_value)
                                    if operator == 'greater than' and field_value < operand:
                                        include_doc = False
                                    if operator == 'less than' and field_value > operand:
                                        include_doc = False
                                    if operator == 'equals' and field_value != operand:
                                        include_doc = False
                                except:
                                    include_doc = False
                if include_doc:
                    # print(operand, field_value, d.id, len(new_collection_docs))
                    new_collection_docs.append(d)
            c.documents = new_collection_docs
            c.filters.update(parent_collection.filters)
            # get name from form
            c.name = post_dict['name_of_new_collection']
            flag_modified(c, "filters") 
            db.session.add(c)
            db.session.merge(c)
            db.session.flush()
            db.session.commit()
            return redirect(url_for('view_collection', collection=c.id, page_start = 1))


    # {'image': [['document has this field', '']], 'reviewText': [['contains', 'iphone'], ['contains', 'screen'], ['contains text', 'samsung']], 
    # 'overall': [['equals', '5']], 'asin': [['document has this field', ''], ['contains text', ''], ['contains text', ''], ['contains text', '']], 'summary': [['contains text', 'great']]}

    # c = models.Collection.query.get(collection)
    # contained_words = []
    # excluded_words = []
    # if contains == "0":
    #     contained_words = []
    # else:
    #     contained_words = contains.split(",")
    # if excludes == "0":
    #     excluded_words = []
    # else:
    #     excluded_words = excludes.split(",")
    # query = c.documents
    # if len(contained_words) > 0:
    #     for w in contained_words:
    #         print("including", w)
    #         query = query.filter(models.Document.data['reviewText'].contains(w))
    # if len(excluded_words) > 0:
    #     for w in excluded_words:
    #         print("excluding", w)
    #         query = query.filter(not_(models.Document.data['reviewText'].contains(w)))
    # docs = [d.data for d in query.paginate(page_start, 25).items]





    return render_template('try_filters2.html', filter_form=filter_form, collection=c)


@app.route('/try_filters/<int:collection>', methods=["POST", "GET"])
@login_required
def try_filters(collection):
    # print(request.args.to_dict())
    c = models.Collection.query.get(collection)
    existing_filters = c.filters
    filter_form = FilterForm()
    if request.method == 'POST':
        inc = filter_form.included_words.data.split(",")
        inc = [w.strip() for w in inc]
        inc = ",".join(w for w in inc)
        exc = filter_form.excluded_words.data.split(",")
        exc = [w.strip() for w in exc]
        exc = "".join(w for w in exc)
        inc = 0 if len(inc) < 1 else inc
        exc = 0 if len(exc) < 1 else exc
        # print(inc, exc)
        return redirect(url_for('filter_collection', collection = collection, contains=inc, excludes=exc, page_start=1))
    if 'contains' in existing_filters:
        inc_string = ",".join(w for w in existing_filters['contains'])
        inc_string = "" if inc_string == 0 else inc_string
        exc_string = ",".join(w for w in existing_filters['excludes'])
        exc_string = "" if exc_string == str(0) else exc_string
        filter_form.included_words.data = inc_string
        filter_form.excluded_words.data = exc_string
    return render_template('try_filters.html', filter_form=filter_form, collection=c)

@app.route('/filter_collection/<int:collection>/<string:contains>/<string:excludes>/<int:page_start>', methods=["POST", "GET"])
@login_required
def filter_collection(collection, contains, excludes, page_start):
    c = models.Collection.query.get(collection)
    contained_words = []
    excluded_words = []
    if contains == "0":
        contained_words = []
    else:
        contained_words = contains.split(",")
    if excludes == "0":
        excluded_words = []
    else:
        excluded_words = excludes.split(",")
    query = c.documents
    if len(contained_words) > 0:
        for w in contained_words:
            # print("including", w)
            query = query.filter(models.Document.data['reviewText'].contains(w))
    if len(excluded_words) > 0:
        for w in excluded_words:
            # print("excluding", w)
            query = query.filter(not_(models.Document.data['reviewText'].contains(w)))
    docs = [d.data for d in query.paginate(page_start, 25).items]
    doc_ids = [d.id for d in query.paginate(page_start, 25).items]
    for n, doc in enumerate(docs):
        doc['id'] = doc_ids[n]
    headings = sorted(list(set([key for doc in docs for key in doc.keys()])))
    create_filtered_collection_form = CreateFilteredCollectionForm()
    if request.method == 'POST' and 'create_new_collection' in request.form.to_dict():
        filters = {'contains' : contained_words, 'excludes' : excluded_words}
        new_collection = models.Collection(documents=query.all(), name = create_filtered_collection_form.collection_name.data, project_id = c.project_id, filters=filters)
        db.session.add(new_collection)
        db.session.commit()
        return redirect(url_for('project', project_id=c.project_id))
    view_data = {}
    view_data['collection_count'] = c.documents.count()
    view_data['contains'] = contains
    view_data['excludes'] = excludes
    view_data['included'] = contained_words
    view_data['excluded'] = excluded_words
    view_data['collection_name'] = c.name
    view_data['original_filters'] = c.filters
    view_data['collection_id'] = c.id
    view_data['current_page'] = page_start
    view_data['total'] = query.count()
    # print(view_data)
    return render_template('filter_collection.html', create_filtered_collection_form=create_filtered_collection_form, table = docs, table_name = 'documents', headings=headings, project_id=c.project_id, view_data=view_data)


@app.route('/view_tag/<int:tag_id>/<int:page_start>', methods=["POST", "GET"])
@login_required
def view_tag(tag_id, page_start):
    tag = models.Tag.query.get(tag_id)
    docs = [d.data for d in tag.tag_docs.paginate(page_start, 25).items]
    doc_ids = [d.id for d in tag.tag_docs.paginate(page_start, 25).items]
    for n, doc in enumerate(docs):
        doc['id'] = doc_ids[n]
    headings = sorted(list(set([key for doc in docs for key in doc.keys()])))
    return render_template('view_tag.html', tag_id=tag_id, current_page=page_start, table = docs, table_name = 'documents', headings=headings, project_id=tag.project_id, tag_name=tag.text)

@app.route('/view_collection/<int:collection>/<int:page_start>', methods=["POST", "GET"])
@login_required
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
    return render_template('view_collection.html', table = docs, current_page = page_start, table_name = 'documents', headings=headings, project_id=p.id, collection=c.id)

@app.route('/project/<int:project_id>', methods=['POST', 'GET'])
@login_required
def project(project_id):
    p = models.Project.query.get(project_id)
    # docs_with_comments = list(set([c.document]))
    #collections_data = [{'collection_id' : c.id, 'collection_name' : c.name, 'filters' : c.filters} for c in p.collections]
    collections_data = [{'collection_id' : c.id, 'counts' : c.documents.count(), 'collection_name' : c.name, 'filters' : c.filters} for c in p.collections]
    return render_template('project.html', project=p, collections_data=collections_data)


app.route("/login", methods=['GET', 'POST'])
@login_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    form.student_group.choices = [( str(g.id), g.name ) for g in models.Group.query.all()]
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = models.User(name=form.username.data, email=form.email.data, password=hashed_password, group_id = form.student_group.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


def user_allowed_in_project(project_id):
    if current_user.admin:
        return True
    p = models.Project.query.get(project_id)
    g = models.Group.query.get(p.group_id)
    if current_user in g.users:
        return True
    return False


def user_projects():
    # print(current_user.admin)
    if current_user.admin:
        return models.Project.query.all()
    
    # print(current_user.email)
    # print(current_user.group_id)
    user_group = models.Group.query.get(current_user.group_id)
    return user_group.projects.all()
