import os
import json
from models import Document, Collection
from app import db


def add(filename, collection_name):
    with open(filename) as inf:
        new_coll = Collection(name=collection_name)
        db.session.add(new_coll)
        db.session.commit()
        counter = 0
        for line in inf.readlines()[:500000]:
            counter = counter + 1
            d = json.loads(line)
            new_doc = Document(data=d, collection_id=new_coll.id)
            db.session.add(new_doc)
            if counter % 100000 == 0:
                print(counter)

db.session.commit()
