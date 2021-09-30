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
## import all documents here.