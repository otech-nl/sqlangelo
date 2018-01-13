from pprint import pformat
from sqlalchemy.inspection import inspect
import inflect

inflect_engine = inflect.engine()


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


class CRUDMixin(object):
    """ provide Create, Read, Update and Delete (CRUD) methods

    Available as app.db.CRUDmixin.
    """
    delay_save = False  # only commit when explicitely instructed

    @classmethod
    def report(cls, msg):
        print(msg)

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
            cls.report('Creating %s: %s' % (cls.__name__, pformat(kwargs)))
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
            self.report('Updating %s "%s": %s' % (self.__class__.__name__,
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
            self.report('Deleting %s "%s"' % (self.__class__.__name__, self))
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


class OperationsMixin(object):

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
