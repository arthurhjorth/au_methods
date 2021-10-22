import app, models

app.db.drop_all()
app.db.create_all()

r = models.Role(name="admin")
app.db.session.add(r)
app.db.session.commit()

u = models.User(name='arthur', roles = models.Role.query.all())
app.db.session.add(u)
app.db.session.commit()