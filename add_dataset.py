import os
import json
from models import Document, Collection
from app import db


def add_to_existing(filename, collection_id, first_n=999999999999999999999):
    with open(filename) as inf:
        coll = Collection.query.get(collection_id) 
        counter = 0
        headings = set()
        for line in inf.readlines()[:first_n]:
            counter = counter + 1
            d = json.loads(line)
            for key in d:
                headings.add(key)
            new_doc = Document(data=d, collection_id=coll.id)
            db.session.add(new_doc)
            coll.documents.append(new_doc)
            if counter % 100000 == 0:
                print(counter)
        coll.headings = sorted(list(headings))
db.session.commit()



def add_collection(filename, collection_name, first_n=999999999999999999999):
    with open(filename) as inf:
        new_coll = Collection(name=collection_name)
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
            new_doc = Document(data=d, collection_id=new_coll.id)
            db.session.add(new_doc)
            new_coll.documents.append(new_doc)
            if counter % 100000 == 0:
                print(counter)
        new_coll.headings = sorted(list(headings))

db.session.commit()