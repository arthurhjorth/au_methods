import os
import json
from models import Document, Collection
from app import db


with open('input_data/Electronics_5.json') as inf:
    new_coll = Collection(name='Electronics')
    db.session.add(new_coll)
    counter = 0
    for line in inf.readlines()[:1500000]:
        counter = counter + 1
        d = json.loads(line)
        new_doc = Document(data=d, collection=new_coll)
        db.session.add(new_doc)
        if counter % 100000 == 0:
            print(counter)
            db.session.commit()

db.session.commit()
