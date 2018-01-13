from .mixins import CRUDMixin, NamingMixin, inflect_engine



def log(msg):
    ''' print a message '''
    print(msg)


def get_base_model(db):

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
                kwargs['backref'] = db.backref(rev_name,
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
            x_names = x_names or (inflect_engine.plural(names[1]), inflect_engine.plural(names[0]))

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

    BaseModel.db = db

    return BaseModel
