import os
import json
from models import Document, Collection
from app import db


def add(filename, collection_name, first_n=999999999999999999999):
    with open(filename) as inf:
        new_coll = Collection(name=collection_name)
        db.session.add(new_coll)
        db.session.commit()
        print(new_coll.id)
        counter = 0
        for line in inf.readlines()[:first_n]:
            counter = counter + 1
            d = json.loads(line)
            new_doc = Document(data=d, collection_id=new_coll.id)
            db.session.add(new_doc)
            new_coll.documents.append(new_doc)
            if counter % 100000 == 0:
                print(counter)

db.session.commit()
