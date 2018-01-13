""" Wrapper around Flask-SQLAlchemy and friends """
from flask_sqlalchemy import SQLAlchemy
from pprint import pformat
from sqlalchemy.orm import backref
from sqlalchemy.inspection import inspect
import sqlalchemy.types as types
import inflect
import sqlalchemy


def log(msg):
    pass

inflect_engine = inflect.engine()

########################################


class MoneyType(types.TypeDecorator):
    """ SQLAlchemy column type to store money values """

    impl = sqlalchemy.Numeric

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('scale', 2)
        types.TypeDecorator.__init__(self, *args, **kwargs)


class PercentageType(sqlalchemy.Numeric):
    """ SQLAlchemy column type to store percentage values """

    def __init__(self, **kwargs):
        kwargs.setdefault('scale', 2)
        super(PercentageType, self).__init__(**kwargs)

########################################


class NamingMixin(object):
    """ Provide some convenient names for models. """

    @classmethod
    def get_api(cls):
        """ return the name of the API

        Returns:
            Table name by default, but may be overridden.
        """
        return cls.__tablename__

    @classmethod
    def get_plural(cls):
        """ return the plural form of the API name """
        return inflect_engine.plural(cls.get_api())


class IntrospectionMixin(object):
    """ access to meta data about a model

    Available as app.db.Introspectionmixin
    """

    @classmethod
    def columns(cls, skip_pk=True, remove=''):
        """ get column names

        Args:
            skip_pk (boolean): if True, ignore primary key columns
            remove (string): names of columns to ignore
        Returns:
            list of column names (strings)
        """
        remove = remove.split()
        insp = inspect(cls)
        if skip_pk:
            pk = [p.key for p in insp.primary_key]
            remove += pk
        cols = set(insp.columns.keys()) - set(remove)
        return cols

    @classmethod
    def relationships(cls, remove=''):
        """ get relationship names

        Args:
            remove (string): names of relationships to ignore
        Returns:
            list of relationship names (strings)
        """
        remove = remove.split()
        cols = set(inspect(cls).relationships) - set(remove)
        return cols

    def to_dict(self, remove=''):
        """ convert model to dictionary

        Only basic columns are included (relationships are ignored),
        so you get `relation_id` and *not* `relation`/

        Args:
            remove (string): names of columns to ignore
        Returns:
            dict of column values
        """
        return {c: getattr(self, c) for c in self.columns(remove=remove)}


class __DBMixin(object):
    db = None


class CRUDMixin(__DBMixin):
    """ provide Create, Read, Update and Delete (CRUD) methods

    Available as app.db.CRUDmixin.
    """
    delay_save = False  # only commit when explicitely instructed
    logger = None

    @classmethod
    def __clean_kwargs(cls, kwargs):
        """ remove all keyword arguments that are not valid CRUD arguments"""
        cols = cls.__dict__
        rem = [k for k in kwargs
               if k not in cols and '_%s' % k not in cols and '%s_id' % k not in cols]
        for r in rem:
            del kwargs[r]

    @classmethod
    def create(cls, commit=True, report=True, **kwargs):
        """ create an object of this class

        Calls before_create and after_create just before and after committing the new object.
        Override these to change create behavior.

        Args:
            commit (boolean): write to database
            report (boolean): log creation
            kwargs: keyword arguments to be forwarded to class constructor after cleaning
        Returns:
            created object
        """
        cls.__clean_kwargs(kwargs)
        if report:
            cls.logger.report('Creating %s: %s' % (cls.__name__, pformat(kwargs)))
        obj = cls(**kwargs)
        obj.before_create(kwargs)
        cls.db.session.add(obj)
        obj.save(commit)
        obj.after_create(kwargs)
        return obj

    def update(self, commit=True, report=True, **kwargs):
        """ update an object

        Calls before_update just before updating the object and after_update just after
        committing the object. Override these to change update behavior.

        Args:
            commit (boolean): write to database
            report (boolean): log update
            kwargs: keyword arguments to be updated after cleaning
        Returns:
            updated object
        """
        self.__clean_kwargs(kwargs)
        if report:
            self.logger.report('Updating %s "%s": %s' % (self.__class__.__name__,
                                                        self,
                                                        pformat(kwargs)))
        log('UPDATE %s' % self)
        log('   %s' % kwargs)
        self.before_update(kwargs)
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.save(commit)
        self.after_update(kwargs)
        return self

    def save(self, really=True):
        """ commit session if delay_save is False

        Args:
            really (boolean): only commit if really is True
        Returns:
            object
        """
        if really and not self.delay_save:
            self.db.session.commit()
        return self

    def delete(self, commit=True, report=True):
        """ delete an object

        Calls after_delete just after deleting the object and just before committing the session.
        Override these to change update behavior.

        Args:
            commit (boolean): write to database
            report (boolean): log deletion
        Returns:
            True is committing, False otherwise.
        """
        if report:
            self.logger.report('Deleting %s "%s"' % (self.__class__.__name__, self))
        self.db.session.delete(self)
        self.after_delete()
        return commit and self.db.session.commit()

    def before_create(self, values):
        """ called just before creation """
        pass

    def after_create(self, values):
        """ called just after creation """
        pass

    def before_update(self, values):
        """ called just before update """
        pass

    def after_update(self, values):
        """ called just after update """
        pass

    def after_delete(self):
        """ called just after delete """
        pass

    @classmethod
    def bulk_insert(cls, new_records):
        """ efficiently create a batch of objects
        Args:
            new_records (list of dicts): values for new objects
        """
        print('Bulk insert of %s: %s' % (cls.__name__, new_records))
        max_id = cls.get_max_id()
        for rec in new_records:
            if id not in rec:
                max_id += 1
                rec['id'] = max_id
        cls.db.engine.execute(cls.__table__.insert(), new_records)
        cls.commit()


class OperationsMixin(__DBMixin):

    @classmethod
    def get(cls, id):
        return cls.db.session.query(cls).get(id)

    @classmethod
    def get_by(cls, key, val, one=True, or_none=True):
        rec = cls.db.session.query(cls).filter(getattr(cls, key) == val)
        if one:
            if or_none:
                return rec.one_or_none()
            else:
                return rec.one()
        else:
            return rec.all()

    @classmethod
    def get_or_404(cls, id):
        return cls.db.session.query(cls).get_or_404(id)

    @classmethod
    def from_form(cls, form):
        obj = cls()
        form.populate_obj(obj)
        return obj

    @classmethod
    def get_max_id(cls):
        return cls.db.session.query(cls.db.func.max(cls.id)).scalar() or 0

    @classmethod
    def commit(cls):
        log('DIRTY: %s' % cls.db.session.dirty)
        log('NEW: %s' % cls.db.session.new)
        log('DELETED: %s' % cls.db.session.deleted)
        cls.db.session.commit()

    @classmethod
    def rollback(cls):
        cls.db.session.rollback()

    @classmethod
    def others(cls, id):
        return cls.query.filter(cls.id != id)


def enable(app, debug=False):  # noqa: C901
    """ Enable this Flask-SQLAlchemy.

    Available through app.db.
    Provides app.db.BaseModel with should be used as superclass for all models.

    Args:
        app (Flask app)
        debug (boolean): if true, logs extra debugging information
    """
    if app.config['SQLALCHEMY_DATABASE_URI'] == 'default':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s.db' % app.name
    app.logger.info('Enabling DB with %s' % app.config['SQLALCHEMY_DATABASE_URI'])


    app.db = SQLAlchemy(app)  # session_options={'autocommit': False, 'autoflush': False}
    app.db.NamingMixin = NamingMixin
    app.db.IntrospectionMixin = IntrospectionMixin
    app.db.MoneyType = MoneyType
    app.db.PercentageType = PercentageType

    app.inflect = inflect_engine
    db = app.db

    db.echo = app.config['DEBUG']

    # for debugging
    # log = app.logger.report

    __DBMixin.db = db
    CRUDMixin.logger = app.logger
    db.CRUDMixin = CRUDMixin
    db.OperationsMixin = OperationsMixin

    class BaseModel(db.Model, CRUDMixin, NamingMixin):
        """ used as super model for all other models

        :var id: every model should have a unique id
        """
        __abstract__ = True

        id = db.Column(db.Integer, primary_key=True)

        @classmethod
        def make_polymorphic_top(basemodel, cls, identities):
            """ returns a polymorphic subclass of cls and basemodel """
            log('Making polymorphic %s from %s: %s'
                % (cls.__name__, basemodel.__name__, identities))
            identities_list = identities.split()

            # make cls polymorphic
            class Polymorphic(cls):
                identities = identities_list
                _identity = db.Column(db.Enum(*identities_list))
                __mapper_args__ = dict(
                    polymorphic_identity=identities_list[0],
                    polymorphic_on=_identity,
                    with_polymorphic='*'
                )

            # now create the actual subclass with basemodel so we can preserve the cls name
            return type(cls.__name__, (Polymorphic, basemodel), {})

        @classmethod
        def derive_model(cls, derived_cls, identity=None, single_table=True):
            log('Derive model %s < %s' % (derived_cls.__name__, cls.__name__))
            attrs = dict(__mapper_args__={'polymorphic_identity': identity or derived_cls.__name__})
            if single_table:  # as opposed to joined table
                log('   single table: %s.id' % cls.__tablename__)
                attrs['id'] = db.Column(db.Integer,
                                        db.ForeignKey('%s.id' % cls.__tablename__),
                                        primary_key=True)
            derived_cls = type(derived_cls.__name__, (derived_cls, cls), attrs)
            return derived_cls

        @classmethod
        def _add_foreign_key(cls, peer_cls, name, nullable=False, default=None):
            foreign_key = '%s_id' % name
            setattr(cls,
                    foreign_key,
                    db.Column(db.Integer,
                              db.ForeignKey('%s.id' % peer_cls.__tablename__),
                              default=default,
                              nullable=nullable))
            return foreign_key

        @classmethod
        def _add_relationship(cls, peer_cls, name, foreign_key, **kwargs):
            log('Referencing %s.%s -> %s'
                % (cls.__name__, name, peer_cls.__name__))
            setattr(cls, name, db.relationship(peer_cls.__name__,
                                               foreign_keys=[getattr(cls, foreign_key)],
                                               remote_side=peer_cls.id,
                                               **kwargs))

        @classmethod
        def add_reference(cls, peer_cls, name=None, rev_name='', nullable=False, default=None,
                          rev_cascade='save-update, merge, delete', add_backref=True):
            """ create 1:n relation """
            name = name or peer_cls.__tablename__
            foreign_key = cls._add_foreign_key(peer_cls, name, nullable, default)

            # prepare optional relation kwarg
            kwargs = dict()
            if add_backref:
                rev_name = rev_name or cls.get_plural()
                kwargs['backref'] = backref(rev_name,
                                            lazy='dynamic',
                                            cascade=rev_cascade)
            # create relationship
            cls._add_relationship(peer_cls, name, foreign_key, **kwargs)

        @classmethod
        def add_single_reference(cls, peer_cls, name=None, rev_name='', nullable=False, default=None,
                                 rev_cascade='save-update, merge, delete', add_backref=True):
            """ create 1:1 relation """
            name = name or peer_cls.__tablename__
            foreign_key = cls._add_foreign_key(peer_cls, name, nullable, default)

            # prepare optional relation kwarg
            kwargs = dict()
            if add_backref:
                rev_name = rev_name or cls.get_api()
                kwargs['backref'] = backref(rev_name,
                                            cascade=rev_cascade,
                                            uselist=False)
            cls._add_relationship(peer_cls, name, foreign_key, **kwargs)

        @classmethod
        def add_cross_reference(cls, peer_cls, names=None, x_names=None, x_cls=None):
            """ adds an m:n relation between this class and peer_cls """
            names = names or (cls.__tablename__, peer_cls.__tablename__)
            x_names = x_names or (app.inflect.plural(names[1]), app.inflect.plural(names[0]))

            # create cross reference table
            x_cls = x_cls or type(cls.__name__ + peer_cls.__name__, (db.BaseModel,), {})
            x_cls.add_reference(cls, name=names[0], add_backref=False)
            x_cls.add_reference(peer_cls, name=names[1], add_backref=False)

            log('   cross reference: %s.%s <-> %s.%s' %
                (cls.__name__, x_names[0], peer_cls.__name__, x_names[1]))

            # create relationship
            kwargs = dict()
            if cls == peer_cls:
                # self-referential
                # setattr(cls, x_names[0], association_proxy(x_names[1], names[0]))
                # setattr(cls, x_names[1], association_proxy(x_names[0], names[1]))
                kwargs['primaryjoin'] = '%s.id==%s.c.%s_id' % (cls.__name__, x_cls.__tablename__, names[0])
                kwargs['secondaryjoin'] = '%s.id==%s.c.%s_id' % (cls.__name__, x_cls.__tablename__, names[1])
            setattr(cls, x_names[0],
                    db.relationship(
                        peer_cls.__name__,
                        secondary=x_cls.__tablename__,
                        backref=db.backref(x_names[1], lazy='dynamic'),
                        **kwargs))

            return x_cls

        @classmethod
        def add_enum_reference(cls, peer_cls, **kwargs):
            kwargs.setdefault('nullable', True)
            kwargs.setdefault('name', peer_cls.__tablename__[5:])
            return cls.add_reference(peer_cls, **kwargs)

    db.BaseModel = BaseModel

    return db

########################################


def make_polymorphic_top(basemodel, identities):
    """ class decorator that makes the model polymorhphic (suitable for inheritance)

    Args:
        basemodel (SQLAlchemy model): added as supermodel
        identities (string): names of all possible identities of derived models
    """
    def class_decorator(cls):
        return basemodel.make_polymorphic_top(cls, identities)
    return class_decorator


def extend_model(super_cls, identity=None, single_table=True):
    """ class decorator that identifies this model as derived

    Args:
        super_cls (polymorphic SQLalchemy model): super model to derive from
        identity (string): identity of this model (class name by default)
        single_table (boolean): use single table inheritance (as opposed to joined table)
    """
    def class_decorator(cls):
        return super_cls.derive_model(cls, identity, single_table)
    return class_decorator


def add_reference(peer_cls, **kwargs):
    """ class decorator that adds a reference to another model

    Adds a foreign key and a n:1 relationship.

    Args:
        peer_cls: model class to refer to
        kwargs: keyword arguments

            * name (string): name of reference (API name of peer_cls by default)
            * rev_name (string): name of reverse relationship (plural of peer_cls by default)
            * nullable (boolean): if True, may be null
            * default (int): default value of foreign key
            * rev_cascade (string): cascade directive for back reference ('save-update, merge, delete' by default)
            * add_backref: if True add a back reference to peer_cls
    """
    def class_decorator(cls):
        cls.add_reference(peer_cls, **kwargs)
        return cls
    return class_decorator


def add_single_reference(peer_cls, **kwargs):
    """ class decorator to add 1:1 reference to a model

    Adds a foreign key and a n:1 relationship.

    Args:
        peer_cls: model class to refer to
        kwargs: keyword arguments

            * name (string): name of reference (API name of peer_cls by default)
            * rev_name (string): name of reverse relationship (plural of peer_cls by default)
            * nullable (boolean): if True, may be null
            * default (int): default value of foreign key
            * rev_cascade (string): cascade directive for back reference ('save-update, merge, delete' by default)
            * add_backref: if True add a back reference to peer_cls
     """
    def class_decorator(cls):
        cls.add_single_reference(peer_cls, **kwargs)
        return cls
    return class_decorator


def add_cross_reference(peer_cls=None, **kwargs):
    """ class decorator that adds a cross-reference to a model

    This results in a m:n relationship through Object Association.

    Args:
        peer_cls (model): model to cross-reference with (class by default: self-reference)
        names (tuple of strings): names for reference from class to peer_cls and vice versa
        x_cls (model): model to hold references to class and peer_cls (if None, a new model is defined and named after class and peer_cls)
        x_names (tuple of strings): names for references from x_cls to class and peer_cls
    """
    def class_decorator(cls):
        cls.add_cross_reference(peer_cls or cls, **kwargs)
        return cls
    return class_decorator


def cross_reference(cls, peer_cls, **kwargs):
    """ class decorator that adds references to cls and peer_cls to a model """
    def class_decorator(x_cls):
        cls.add_cross_reference(peer_cls, x_cls=x_cls, **kwargs)
        return x_cls
    return class_decorator


def add_enum_reference(peer_cls, **kwargs):
    """ decorator for to cls.add_enum_reference """
    def class_decorator(cls):
        cls.add_enum_reference(peer_cls, **kwargs)
        return cls
    return class_decorator

########################################


def init(app):
    app.logger.info('Initializing DB %s' % app.db)
    app.db.drop_all()
    app.db.create_all()
