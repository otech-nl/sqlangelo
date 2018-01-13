import sqlalchemy


class MoneyType(sqlalchemy.types.TypeDecorator):
    """ SQLAlchemy column type to store money values """

    impl = sqlalchemy.Numeric

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('scale', 2)
        sqlalchemy.types.TypeDecorator.__init__(self, *args, **kwargs)


class PercentageType(sqlalchemy.Numeric):
    """ SQLAlchemy column type to store percentage values """

    def __init__(self, **kwargs):
        kwargs.setdefault('scale', 2)
        super(PercentageType, self).__init__(**kwargs)
