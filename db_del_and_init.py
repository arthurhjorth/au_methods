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

hp = app.bcrypt.generate_password_hash("DigitalmethodsF2021")
u = models.User(name='Arthur Hjorth Admin', admin=True, password=hp, email="arthur@mgmt.au.dk", roles= list(models.Role.query.filter_by(name='admin')))
app.db.session.add(u)
app.db.session.commit()
hp = app.bcrypt.generate_password_hash("DigitalMethodsF2021")
u = models.User(name='Michela Beretta', admin=True, password=hp, email="micbe@mgmt.au.dk", roles= list(models.Role.query.filter_by(name='admin')))
app.db.session.add(u)
app.db.session.commit()
u = models.User(name='Arthur Hjorth student', password=hp, email="arthur@stx.oxon.org", roles= list(models.Role.query.filter_by(name='student')))
app.db.session.add(u)
app.db.session.commit()

add('input_data/Electronics_5.json', 'Electronics Reviews, 1.5M', 1500000)
add('input_data/Electronics_5.json', 'Electronics Reviews, tiny', 200000)

g = models.Group(name='admin group', users=[u])
app.db.session.add(g)
app.db.session.commit()
for n in range(13):
    student_group = models.group(name='Group ' + str(n), users = [])
    app.db.session.add(student_group)
    app.db.session.commit()
c = models.Collection.query.get(1)
p = models.Project(name='Arthurs Demo Project', collections = [c], group_id = g.id)
app.db.session.add(p)
app.db.session.commit()
print(p.id)
c2 = models.Collection.query.get(2)
p2 = models.Project(name='Arthurs Demo project 2 for students', collections = [c2], group_id = g2.id)
app.db.session.add(p2)
app.db.session.commit()
print(p2.id)

## import all documents here.