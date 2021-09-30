import os
import json, requests, copy
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy


# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://au_methods_postgres:Hermes_2014@localhost:5432/au_methods_postgres" ## THIS WORKS FOR POSTGRES

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

@app.route('/home')
def crops_vs_creatures(group):
    return jsonfiy({})

@app.route('/add_collection')
def add_collection():
    return jsonfiy({})


@app.route('/add_user')
def add_user():
    return jsonfiy({})


