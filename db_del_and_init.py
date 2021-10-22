from add_dataset import add
import app
import models


app.db.drop_all()
app.db.create_all()

for r in ['admin', 'instructor', 'student']:
    new_role = models.Role(name=r)
    app.db.session.add(new_role)

# r = models.Role(name='test')
# app.db.session.add(r)
app.db.session.commit()

u = models.User(name='arthur', roles= list(models.Role.query.filter_by(name='admin')))
app.db.session.add(u)
app.db.session.commit()

add('input_data/Electronics_5.json', 'Electronics Reviews, 500,000')

g = models.Group(name='admin group', users=[u])
app.db.session.add(g)
app.db.session.commit()
c = models.Collection.query.get(1)
p = models.Project(name='Arthurs test', collections = [c], group_id = g.id)
app.db.session.commit()
app.db.session.add(p)
app.db.session.commit()

## import all documents here.