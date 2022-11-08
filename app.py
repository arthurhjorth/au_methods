from operator import add
import matplotlib.pyplot as plt
import os
import numpy as np
import json, requests, copy
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from sqlalchemy.sql.expression import or_
from flask_sqlalchemy import SQLAlchemy
from forms import AddGroupForm, AddCommentForm, AddTagForm, ApplyFunctionForm, CreateFilteredCollectionForm, CreateTagForm, FilterForm, LoginForm, RegistrationForm, FilterForm2, LinearRegressionForm, LinearRegressionForm2, TTestForm, TTestForm2, HistogramForm2, AddGroupForm, AddProjectForm, AddCollectionForm
from flask_login import login_user, current_user, logout_user, login_required, LoginManager
from sqlalchemy import not_, and_
from flask_bcrypt import Bcrypt
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text
from flask_migrate import Migrate
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats

secrets = json.loads(open('secrets.json').read())

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets['secretkey']
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



@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    form = AddProjectForm()
    form.group.choices = [( str(g.id), g.name ) for g in models.Group.query.all()]
    form.dataset.choices = [( str(c.id), c.name ) for c in models.Collection.query.all()]
    if form.validate_on_submit():
        project_name = form.name.data
        group_id = form.group.data
        collection = models.Collection.query.get(int(form.dataset.data))
        project = models.Project(name=project_name, collections = [collection], group_id=group_id)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_project.html', form=form)

@app.route('/add_collection', methods=['GET', 'POST'])
@login_required
def add_collection():
    files = [f for f in os.listdir("input_data/") if '.json' in f or '.csv' in f]
    form = AddCollectionForm()
    form.filename.choices = [( f, f) for f in files]
    if form.validate_on_submit():
        add_collection_by_filename("input_data/"+form.filename.data, form.name.data)
        return redirect(url_for('home'))
    return render_template('add_collection.html', form=form)

@app.route('/add_group', methods=['GET', 'POST'])
@login_required
def add_group():
    form = AddGroupForm()
    if form.validate_on_submit():
        group_name = form.name.data
        g = models.Group(name=group_name, users=[])
        db.session.add(g)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_group.html', form=form)

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



@app.route('/apply_function_to_docs/<int:collection>', methods=["POST", "GET"])
@login_required
def apply_function(collection):
    project_id = 0
    function_form = ApplyFunctionForm()
    function_options = ["Word Count", "Sentence Count", "Reading difficulty (Lix)", "Total Sentiment", "Negative Sentiment", "Positive Sentiment"]
    function_form.function.choices = [(str(func), str(func)) for func in function_options]
    c = models.Collection.query.get(collection)
    project_id = c.project_id
    function_form.field_name.choices = [( str(fieldname), str(fieldname) ) for fieldname in c.headings]
    if request.method == 'POST':
        if function_form.function.data == "Total Sentiment":
            add_sentiment_analysis(c, function_form.field_name.data)
        if function_form.function.data == "Negative Sentiment":
            add_sentiment_analysis(c, function_form.field_name.data, positive=False)
        if function_form.function.data == "Positive Sentiment":
            add_sentiment_analysis(c, function_form.field_name.data, negative=False)
        if function_form.function.data == "Word Count":
            add_word_count(c, function_form.field_name.data)
        if function_form.function.data == "Sentence Count":
            add_sentence_count(c, function_form.field_name.data)
        if function_form.function.data == "Reading difficulty (Lix)":
            add_lix_rating(c, function_form.field_name.data)
        return redirect(url_for('view_collection', collection=c.id, page_start=1))
    return render_template('apply_function_to_doc.html', function_form = function_form, project_id=project_id, collection=c)

@app.route('/add_collection_from_tags/<int:p>/', methods=['POST','GET'])
@login_required
def add_collection_from_tags(p):
    project = models.Project.query.get(p)
    args = request.args.to_dict()

    included_tag_ids = [t for t in args.get('included', '').split(",")] if args.get('included', '') != '' else []
    excluded_tag_ids = [t for t in args.get('excluded', '').split(",")] if args.get('excluded', '') != '' else []
    included_tags = [models.Tag.query.get(t) for t in included_tag_ids]
    excluded_tags = [models.Tag.query.get(t) for t in excluded_tag_ids]
    inc_tags = [t.id for t in included_tags]
    exc_tags = [t.id for t in excluded_tags]
    print(args)
    if request.method == "POST":
        form = request.form.to_dict()
        print(form)
        docs = []
        headings = set()
        for t in included_tags:
            for d in t.tag_docs:
                docs.append(d)
                for k in d.data:
                    headings.add(k)
        for t in excluded_tags:
            for d in t.tag_docs:
                if d in docs:
                    docs.remove(d)
        headings = sorted(list(headings))
        new_collection = models.Collection(name=form['name'],parent_filters={}, project_id = p, headings=headings)
        for d in docs:
            new_collection.documents.append(d)
        new_collection.doc_count = new_collection.documents.count()
        db.session.add(new_collection)
        db.session.commit()
        return redirect(url_for('project', project_id=p))
        ## move to project id

        # implemnet change
    if request.method == "GET":
        # available_tags = [tag for tag in project.tags if tag not in included_tags and tag not in excluded_tags]
        print(inc_tags, exc_tags)
        return render_template('make_collection_from_tags.html', all_tags=project.tags, included_tags=inc_tags, excluded_tags=exc_tags, project_id=project.id)
        
    return jsonify({})
    


@app.route('/try_filters2/<int:collection>', methods=["POST", "GET"])
@login_required
def try_filters2(collection):
    c = models.Collection.query.get(collection)
    if c.doc_count != 0:
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
    operations = ['contains text', 'does not contain text', 'greater than', 'less than', 'equals', 'is tagged as', 'is not tagged as']#, 'document has this field', 'document does not have this field']
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
# #### start here
### i dont understand why but this takes an insane amount of time. Let's just special case this
### around line 308
#                     if operator == 'is tagged as':
#                         if "," in operand:
#                             or_tags = operand.split(",")
#                             or_tags = [w.strip() for w in or_tags]
#                             tags = app.models.Tag.query.filter(app.models.Tag.text.in_(or_tags)).all()
#                             query_filters = [models.Document.doc_tags.contains(tag) for tag in tags]
#                             query.filter(or_(*query_filters))
#                         # else:
#                         #     tag =
#                         #     query = query.filter(
#####
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
            for d in query:
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
            c.doc_count = len(new_collection_docs)
            for k,v in parent_collection.filters.items():
                if k in c.filters:
                    c.filters[k].append(v)
                else:
                    c.filters[k] = v
            c.headings = parent_collection.headings
            flag_modified(c, "headings")
            # get name from form
            c.name = post_dict['name_of_new_collection']
            if c.name == "":
                c.name == "Unnamed"
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

@app.route('/t-test/<int:project>', methods=["POST", "GET"])
@login_required
def t_test(project):
    p = models.Project.query.get(project)
    colls = p.collections
    ttest_form = TTestForm()
    ttest_form.collection1.choices = [(c.id, c.name) for c in colls if not c.hidden]
    ttest_form.collection2.choices = [(c.id, c.name) for c in colls if not c.hidden]
    if request.method == "POST":
        rq_form = request.form.to_dict()
        print(request.form.to_dict())
        return redirect(url_for('t_test2', collection1=rq_form['collection1'], collection2=rq_form['collection2']))
    return render_template('ttest1.html', ttest_form=ttest_form)



@app.route('/t-test2/<int:collection1>/<int:collection2>', methods=['POST', 'GET'])
@login_required
def t_test2(collection1, collection2):
    coll1 = models.Collection.query.get(collection1)
    coll2 = models.Collection.query.get(collection2)
    if request.method == "POST":
        rq_form = request.form.to_dict()
        print(rq_form['data1'])
        print(rq_form['data2'])
        data1 = np.array([d.data[rq_form['data1']] for d  in coll1.documents])
        data2 = np.array([d.data[rq_form['data2']] for d  in coll2.documents])
        test_result = stats.ttest_ind(data1, data2, equal_var=False)
        print(stats.tmean(data1))
        print(stats.tmean(data2))
        data = {}
        data['data1'] = rq_form['data1'] + " from collection " + coll1.name + "(ID " + str(coll1.id) + ")"
        data['data2'] = rq_form['data2'] + " from collection " + coll2.name + "(ID " + str(coll2.id) + ")"
        data['t-statistic'] = test_result[0]
        # data['p-value'] = test_result[1]
        data['data1-mean'] = stats.tmean(data1)
        data['data2-mean'] = stats.tmean(data2)
        data['data1-std'] = stats.tstd(data1)
        data['data2-std'] = stats.tstd(data2)
        data['data1-sample-size'] = len(data1)
        data['data2-sample-size'] = len(data2)
        data['type'] = "T-test"
        data['reflections'] = rq_form['reflections']

        new_analysis = models.Analysis()
        new_analysis.name = "T-test on " + data['data1'] + " " + data['data2']
        new_analysis.group_id = current_user.group_id
        new_analysis.project_id = coll1.project_id
        new_analysis.data = data
        db.session.add(new_analysis)
        db.session.commit()

        return redirect(url_for('project', project_id=coll1.project_id))
    ttest_form2 = TTestForm2()
    ttest_form2.data1.choices = [(str(h), str(h)) for h in coll1.headings]
    ttest_form2.data2.choices = [(str(h), str(h)) for h in coll2.headings]
    return render_template('ttest2.html', ttest_form2=ttest_form2, c1name = coll1.name, c2name = coll2.name)
    ttest_form_form2 = TTestForm2()
    ttest_form_form2.data1.choices = [(str(h), str(h)) for h in coll1.headings]
    ttest_form_form2.data2.choices = [(str(h), str(h)) for h in coll2.headings]
    return render_template('ttest2.html', ttest_form2=ttest_form_form2)


@app.route('/histogram1/<int:project>', methods=["post", "get"])
@login_required
def histogram(project):
    if request.method == "POST":
        rq_form = request.form.to_dict()
        return redirect(url_for('histogram2', collection=rq_form['collection']))
    p = models.Project.query.get(project)
    linear_regression_form = LinearRegressionForm()
    colls = [p for p in p.collections if not p.hidden]
    linear_regression_form.collection.choices = [(c.id, c.name) for c in colls]
    return render_template('histogram.html', linear_regression_form=linear_regression_form)

@app.route('/histogram2/<int:collection>', methods=["POST", "GET"])
@login_required
def histogram2(collection):
    coll = models.Collection.query.get(collection)
    if request.method == "POST":
        rq_form = request.form.to_dict()
        data = rq_form['data']
        in_data = [data_to_float(d.data[data]) for d in coll.documents if data in d.data]
        plt.xlim([min(in_data), max(in_data)])
        plt.hist(in_data)
        # plt.xscale(5))
        plt.xlabel = data

        name = "Histogram of " + data + " from collection " + coll.name + "(ID " + str(coll.id) + ")"
        fig_name = "Histogram of " + data + " from collection " + coll.name + "_ID " + str(coll.id) + "_"
        fig_name = fig_name.replace(" ", "_")
        plt.savefig('static/images/' + fig_name)
        plt.clf()

        new_analysis = models.Analysis()
        new_analysis.name = name
        new_analysis.group_id = current_user.group_id
        new_analysis.project_id = coll.project_id
        data = {}
        data['image'] = fig_name
        data['Total documents'] = len(in_data)
        # mean = sum(in_data) / len(in_data)
        data['Mean of value'] = stats.tmean(in_data)
        data['STD of value'] = stats.tstd(in_data)
        data['reflections'] = rq_form['reflections']
        new_analysis.data = data

        db.session.add(new_analysis)
        db.session.commit()
        return redirect(url_for('project', project_id=coll.project_id))

    histogram_form2 = HistogramForm2()
    histogram_form2.data.choices = [(str(h), str(h)) for h in coll.headings]
    return render_template('histogram2.html', histogram_form2=histogram_form2)

@app.route('/linear_regression1/<int:project>', methods=["post", "get"])
@login_required
def linear_regression(project):
    if request.method == "POST":
        rq_form = request.form.to_dict()
        print(request.form.to_dict())
        return redirect(url_for('linear_regression2', collection=rq_form['collection']))
    p = models.Project.query.get(project)
    linear_regression_form = LinearRegressionForm()
    colls = [p for p in p.collections if not p.hidden]
    linear_regression_form.collection.choices = [(c.id, c.name) for c in colls]
    return render_template('linear_regression1.html', linear_regression_form=linear_regression_form)

def data_to_float(astr):
    if type(astr) == int:
        return float(astr)
    if type(astr) == str:
        astr = astr.replace(",", "")
        return float(astr)
    return astr

@app.route('/linear_regression2/<int:collection>', methods=["POST", "GET"])
@login_required
def linear_regression2(collection):
    coll = models.Collection.query.get(collection)
    if request.method == "POST":
        plt.figure().clear()
        plt.close()
        plt.cla()
        plt.clf()



        rq_form = request.form.to_dict()
        x_heading = rq_form['x_heading']
        y_heading = rq_form['y_heading']
        xy = [(d.data[x_heading], d.data[y_heading]) for d in coll.documents if x_heading in d.data and y_heading in d.data]

        sample = int(coll.doc_count / 5)
        x = np.array(([np.array(data_to_float(t[0])) for t in xy]))
        x = x.reshape(-1, 1)
        y = np.array([data_to_float(t[1]) for t in xy])
        # Split the data into training/testing sets
        # take half here, REMOVE the hard coding
        x_train = x[:-sample]
        x_test = x[-sample:]

        # Split the targets into training/testing sets
        y_train = y[:-sample]
        y_test = y[-sample:]


        # Create linear regression object
        regr = linear_model.LinearRegression()

        # Train the model using the training sets
        regr.fit(x_train, y_train)

        # Make predictions using the testing set
        y_pred = regr.predict(x_test)

        # The coefficients
        print("Coefficients: \n", regr.coef_)
        # The mean squared error
        print("Mean squared error: %.2f" % mean_squared_error(y_test, y_pred))
        # The coefficient of determination: 1 is perfect prediction
        print("Coefficient of determination: %.2f" % r2_score(y_test, y_pred))

        fig_name = "Linear regression on " + x_heading + " and " + y_heading + " on " + coll.name

        fig_name = fig_name.replace(" ", "_")
        data = {}
        data['Coefficients'] = regr.coef_[0]
        data['MSE'] = mean_squared_error(y_test, y_pred)
        data['Coefficients of determination (R2)'] = r2_score(y_test, y_pred)
        data['image'] = fig_name
        data['type'] = 'LinearRegression'
        data['reflections'] = rq_form['reflections']


        # Plot outputs
        plt.scatter(x_test, y_test, color="black")
        plt.plot(x_test, y_pred, color="blue", linewidth=2)
        # plt.ylabel(y_heading)
        # plt.xlabel(x_heading)

        plt.savefig('static/images/'+fig_name)
        plt.clf()

        # now save the analysis databse object
        new_analysis = models.Analysis()
        new_analysis.name = fig_name[:250]
        new_analysis.group_id = current_user.group_id
        new_analysis.project_id = coll.project_id
        new_analysis.data = data

        db.session.add(new_analysis)
        db.session.commit()

        return redirect(url_for('project', project_id=coll.project_id))
    linear_regression_form2 = LinearRegressionForm2()
    linear_regression_form2.x_heading.choices = [(str(h), str(h)) for h in coll.headings]
    linear_regression_form2.y_heading.choices = [(str(h), str(h)) for h in coll.headings]
    return render_template('linear_regression2.html', linear_regression_form=linear_regression_form2)


@app.route('/view_analysis/<int:analysis_id>')
def view_analysis(analysis_id):
    analysis = models.Analysis.query.get(analysis_id)
    return render_template('view_analysis.html', analysis=analysis)

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

    collections_data = [{'collection_id' : c.id, 'entries' : c.doc_count, 'collection_name' : c.name} for c in p.collections]
    headings = sorted(list(set([key for doc in docs for key in doc.keys()])))
    return render_template('view_collection.html', table = docs, current_page = page_start, table_name = 'documents', headings=headings, project_id=p.id, collection=c.id)

@app.route('/project/<int:project_id>', methods=['POST', 'GET'])
@login_required
def project(project_id):
    view = request.args.to_dict().get('view', 0)
    p = models.Project.query.get(project_id)
    collections_data = [{'collection_id' : c.id, 'counts' : c.doc_count, 'collection_name' : c.name, 'filters' : c.filters, 'analysis_results' : c.analysis_results, 'hidden' : c.hidden} for c in p.collections]
    if request.method == 'POST':
        if 'hide-collection' in request.form.to_dict():
            collection_id = request.form.to_dict()['hide-collection']
            col = models.Collection.query.get(collection_id)
            col.hidden = True
            db.session.add(col)
            db.session.commit()
            return redirect(url_for('project', project_id = project_id))
        if 'show-collection' in request.form.to_dict():
            collection_id = request.form.to_dict()['show-collection']
            col = models.Collection.query.get(collection_id)
            col.hidden = False
            db.session.add(col)
            db.session.commit()
            return redirect(url_for('project', project_id = project_id, view='1'))
    return render_template('project.html', project=p, collections_data=collections_data, view=view)

app.route("/add_group", methods=['GET', 'POST'])
def add_group():
    form = AddGroupForm()
    return render_template('add_group.html', form=form)

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



def add_sentiment_analysis(collection, fieldname, positive = True, negative = True):
    positive_words = set([l.strip() for l in open('positive-words.webarchive').readlines()])
    negative_words = set([l.strip() for l in open('negative-words.webarchive').readlines()])
    count = 0
    dict_heading = ""
    average = 0
    standard_deviation = 0
    scores = []
    if positive and negative:
        dict_heading  = 'total_sentiment_'+fieldname
    if positive and not negative:
        dict_heading  = 'positive_sentiment_'+fieldname
    if not positive and negative:
        dict_heading  = 'negative_sentiment_'+fieldname
    for d in collection.documents:
        if fieldname in d.data:
            count = count + 1
            total_sentiment = 0
            doc_words = str(d.data[fieldname]).split()
            for word in doc_words:
                if positive:
                    if word in positive_words:
                        total_sentiment = total_sentiment + 1
                if negative:
                    if word in negative_words:
                        total_sentiment = total_sentiment - 1
            scores.append(total_sentiment)
            d.data.update({dict_heading : total_sentiment})
            flag_modified(d, 'data')
            db.session.add(d)
            db.session.merge(d)
            db.session.flush()
            if count % 50000 == 0:
                db.session.commit()
    collection.headings.append(dict_heading)
    flag_modified(collection, 'headings')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()
    standard_deviation = np.std(scores)
    average = np.mean(scores)
    collection.analysis_results[dict_heading] = {'average' : average, 'standard deviation' : standard_deviation}
    flag_modified(collection, 'analysis_results')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()




def add_sentence_count(collection, fieldname):
    dict_heading = 'sentence_count_'+fieldname
    average = 0
    standard_deviation = 0
    sentence_counts = []
    count = 0
    for d in collection.documents:
        if fieldname in d.data:
            count = count + 1
            text = str(d.data[fieldname])
            text.replace("...", ".")
            text.replace("!", ".")
            text.replace("?", ".")
            sentence_count = len(text.split("."))
            d.data.update({dict_heading : sentence_count})
            sentence_counts.append(sentence_count)
            flag_modified(d, 'data')
            db.session.add(d)
            db.session.merge(d)
            db.session.flush()
            if count % 50000 == 0:
                db.session.commit()
    collection.headings.append(dict_heading)
    flag_modified(collection, 'headings')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()
    standard_deviation = np.std(sentence_counts)
    average = np.mean(sentence_counts)
    collection.analysis_results[dict_heading] = {'average' : average, 'standard deviation' : standard_deviation}
    flag_modified(collection, 'analysis_results')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()



def add_word_count(collection, fieldname):
    dict_heading = 'word_count_'+fieldname
    average = 0
    standard_deviation = 0
    word_counts = []
    count = 0
    for d in collection.documents:
        if fieldname in d.data:
            count = count + 1
            word_count = len(str(d.data[fieldname]).split())
            word_counts.append(word_count)
            d.data.update({dict_heading : word_count})
            flag_modified(d, 'data')
            db.session.add(d)
            db.session.merge(d)
            db.session.flush()
            if count % 50000 == 0:
                db.session.commit()
    collection.headings.append(dict_heading)
    flag_modified(collection, 'headings')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()
    standard_deviation = np.std(word_counts)
    average = np.mean(word_counts)
    collection.analysis_results[dict_heading] = {'average' : average, 'standard deviation' : standard_deviation}
    flag_modified(collection, 'analysis_results')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()


def add_lix_rating(collection, fieldname):
    dict_heading = 'lix_rating'+fieldname
    average = 0
    standard_deviation = 0
    lix_scores = []
    count = 0
    for d in collection.documents:
        if fieldname in d.data:
            count = count + 1
            text = str(d.data[fieldname])
            words = [w for w in text.split() if 'http' not in w and '@' not in w]
            text = " ".join([w for w in words])
            text = text.replace("...", ".")
            text = text.replace("!", ".")
            text = text.replace("?", ".")
            text = text.replace(":", " ")
            sentence_count = len(text.split("."))
            word_count = len(words)
            words_longer_than_6 = len([word for word in words if len(word) > 6])
            lix_score = (word_count / sentence_count)
            if words_longer_than_6 > 0:
                lix_score = lix_score + words_longer_than_6 * 100 / word_count
            lix_scores.append(lix_score)
            d.data.update({dict_heading : lix_score})
            flag_modified(d, 'data')
            db.session.add(d)
            db.session.merge(d)
            db.session.flush()
            if count % 50000 == 0:
                db.session.commit()
    collection.headings.append(dict_heading)
    flag_modified(collection, 'headings')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()
    standard_deviation = np.std(lix_scores)
    average = np.mean(lix_scores)
    collection.analysis_results[dict_heading] = {'average' : average, 'standard deviation' : standard_deviation}
    flag_modified(collection, 'analysis_results')
    db.session.add(collection)
    db.session.merge(collection)
    db.session.flush()
    db.session.commit()


def add_json_file_to_collection(filename, collection_id):
    with open(filename) as inf:
        counter = 0 # counter for commiting
        coll = models.Collection.query.get(collection_id)
        headings = set(coll.headings)
        for line in inf.readlines():
            counter = counter + 1
            d = json.loads(line)
            for key in d:
                headings.add(key)
            new_doc = models.Document(data=d, collection_id = collection_id)
            db.session.add(new_doc)
            coll.documents.append(new_doc)
            if counter % 10000 == 0:
                db.session.commit()
                print(counter)
        coll.headings = sorted(list(headings))
        db.session.commit()
        coll.doc_count = coll.documents.count()
        db.session.add(coll)
        db.session.commit()


def add_collection_by_filename(filename, collection_name, first_n=999999999999999999999):
    with open(filename) as inf:
        new_coll = models.Collection(name=collection_name)
        db.session.add(new_coll)
        db.session.commit()
        print(new_coll.id)
        counter = 0
        headings = set()
        for line in inf.readlines()[:first_n]:
            counter = counter + 1
            d = json.loads(line)
            for key in d:
                headings.add(key)
            new_doc = models.Document(data=d, collection_id=new_coll.id)
            db.session.add(new_doc)
            new_coll.documents.append(new_doc)
            if counter % 10000 == 0:
                db.session.commit()
                print(counter)
        new_coll.headings = sorted(list(headings))
        db.session.commit()
        new_coll.doc_count = new_coll.documents.count()
        db.session.add(new_coll)
        db.session.commit()
