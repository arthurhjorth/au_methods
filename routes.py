import app
import models
import pandas as pd

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
@app.route('/home')
@login_required
@login_required
def home():
    projects = models.Project.query.all()
    print(projects)
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
        new_tag = models.Tag(text=the_tag_text, project_id=project_id)
        print(tag_names)
        if the_tag_text not in tag_names:
            db.session.add(new_tag)
            db.session.commit()
        create_tag_form.tag_name.data = ''
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    if request.method == 'POST' and 'submit_comment' in request.form.to_dict():
        the_comment = add_comment_form.text.data
        new_comment = models.Comment(text=the_comment, project_id = project_id, doc_id=the_doc.id)
        db.session.add(new_comment)
        db.session.commit()
        add_comment_form.text.data = ""
        return redirect(url_for('view_document2', project_id=project.id, doc_id=doc_id ))
    return render_template('view_document.html', document=the_doc, comment_form = add_comment_form, add_tag_form=add_tag_form, create_tag_form=create_tag_form, doc_data=doc_data)


@app.route('/filter_collection/<int:collection>/<string:contains>/<string:excludes>/<int:page_start>', methods=["POST", "GET"])
@login_required
def filter_collection(collection, contains, excludes, page_start):
    print(request.args.to_dict())
    contained_words = contains.split(",") if len(contains) > 1 else []
    excluded_words = excludes.split(",") if len(excludes) > 1 else []
    c = models.Collection.query.get(collection)
    query = c.documents
    filter_form = FilterForm()
    create_filtered_collection_form = CreateFilteredCollectionForm()
    if request.method == 'POST' and 'create_new_collection' in request.form.to_dict():
        print("making new")
        redirect(url_for('filter_collection', contains = contains, excludes=excludes, page_start=page_start, collection=collection))
    if request.method == 'POST' and 'test_filter' in request.form.to_dict():
        words_to_include = [word.strip() for word in  filter_form.included_words.data.split(",")]
        words_to_exclude = [word.strip() for word in  filter_form.excluded_words.data.split(",")]
        words_to_include = ",".join(w for w in words_to_include)
        words_to_exclude = ",".join(w for w in words_to_exclude)
        print(words_to_include)
        print(words_to_exclude)
        # print(url_for('filter_collection'))
        # redirect(url_for('filter_coll'))
        # render_template('filter_collection2.html', contains = words_to_include, excludes=words_to_exclude, page_start=1, collection=collection)
        redirect(url_for('filter_collection', contains = words_to_include, excludes=words_to_exclude, page_start=1, collection=collection))
    filter_form.included_words.data = contains
    filter_form.excluded_words.data = excludes
    if len(contained_words) > 0:
        for w in contained_words:
            query = query.filter(models.Document.data['reviewText'].contains(w))
    if len(excluded_words) > 0:
        for w in excluded_words:
            query = query.filter(not_(models.Document.data['reviewText'].contains(w)))
    docs = [d.data for d in query.paginate(page_start, 25).items]
    doc_ids = [d.id for d in query.paginate(page_start, 25).items]
    for n, doc in enumerate(docs):
        doc['id'] = doc_ids[n]
    headings = sorted(list(set([key for doc in docs for key in doc.keys()])))
    view_data = {}
    view_data['collection_count'] = c.documents.count()
    view_data['included'] = contained_words
    view_data['excluded'] = excluded_words
    view_data['collection_name'] = c.name
    view_data['total'] = query.count()
    return render_template('filter_collection2.html', create_filtered_collection_form=create_filtered_collection_form, filter_form=filter_form, table = docs, table_name = 'documents', headings=headings, project_id=c.project_id, view_data=view_data)

@app.route('/view_tag/<int:tag_id>/<int:page_start>', methods=["POST", "GET"])
@login_required
def view_tag(tag_id, page_start):
    tag = models.Tag.query.get(tag_id)
    docs = [d.data for d in tag.tag_docs.paginate(page_start, 25).items]
    doc_ids = [d.id for d in tag.tag_docs.paginate(page_start, 25).items]
    for n, doc in enumerate(docs):
        doc['id'] = doc_ids[n]
    headings = sorted(list(set([key for doc in docs for key in doc.keys()])))
    return render_template('view_tag.html', table = docs, table_name = 'documents', headings=headings, project_id=tag.project_id, tag_name=tag.text)

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
    return render_template('view_collection.html', table = docs, table_name = 'documents', headings=headings, project_id=p.id)

@app.route('/project/<int:project_id>', methods=['POST', 'GET'])
@login_required
def project(project_id):
    p = models.Project.query.get(project_id)
    collections_data = [{'collection_id' : c.id, 'entries' : c.documents.count(), 'collection_name' : c.name} for c in p.collections]
    return render_template('project.html', project=p, collections_data=collections_data)


app.route("/login", methods=['GET', 'POST'])
@login_required
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


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = mdoels.User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)