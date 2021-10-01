import os
import json, requests, copy
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://au_methods_postgres:Hermes_2014@localhost:5432/au_methods_postgres" ## THIS WORKS FOR POSTGRES
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


import models
import pandas as pd

@app.route('/')
@app.route('/home')
def home():
    return jsonify('<p>hi</p>')

@app.route('/add_collection')
def add_collection():
    return jsonify({})

@app.route('/view_collection/<int:collection>/<int:start>', methods=["POST", "GET"])
def view_collection(collection, start):
    c = models.Collection.query.get(collection)
    # docs = [d.data for d in c.documents[start:start+25]]
    docs_we_want = [n for n in range(start, start+26)]
    docs = [c.documents.filter_by(id=id).one() for id in docs_we_want]
    docs = [d.data for d in docs]
    df = pd.DataFrame(docs) 
    return render_template('show_collection.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)

@app.route('/add_user')
def add_user():
    return render_template('add_user.html')