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

    Adds a foreign key and a 1:1 relationship.

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
