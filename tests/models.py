# coding=utf8
import flask
from sqlangelo import SQLAngelo, mixins, decorators, types


app = flask.Flask('SQL Angelo Test')
db = SQLAngelo(app, 'sqlite:///db.sqlite3', True)

########################################


class BaseModel(db.BaseModel, mixins.CRUDMixin):
    __abstract__ = True

########################################


class Group(BaseModel):
    abbr = db.Column(db.Unicode(6), nullable=False)

    def __str__(self):
        return self.abbr


@decorators.add_cross_reference(Group)
@decorators.make_polymorphic_top(BaseModel, 'User Employee')
class User(object):
    email = db.Column(db.Unicode(30), nullable=False)

    def __str__(self):
        return '%s (%s)' % (self.email, ', '.join([str(g) for g in self.groups]))


class Company(BaseModel):
    name = db.Column(db.Unicode(30), nullable=False)

    def __str__(self):
        return '%s: %s' % (self.name, ', '.join([str(e) for e in self.employees]))


@decorators.add_reference(Company)
@decorators.extend_model(User)
class Employee(object):
    salary = types.MoneyType()
