""" Wrapper around Flask-SQLAlchemy and friends """
from flask_sqlalchemy import SQLAlchemy
from . import decorators, mixins, types

class SQLAngelo(SQLAlchemy):

    def __init__(self, app, db_uri, debug=False):  # noqa: C901
        """ Args:
        app (Flask app)
        db_uri: URI of database
        debug (boolean): if true, logs extra debugging information
        """

        # configure debug logging
        self.echo = debug
        from . import base
        if not debug:
            base.log = lambda msg: None
        base.log('Enabling DB with %s' % db_uri)

        # connect tot database
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # suppress warning
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        super(SQLAngelo, self).__init__(app, session_options={
            'expire_on_commit': False  # as per https://gist.github.com/krak3n/9fa1268ee0a92a67f71a
        })

        # create basemodel
        self.BaseModel = base.get_base_model(self)
        self.decorators = decorators
        self.mixins = mixins
        self.types = types

    def init(self):
        ''' (re)create the database '''
        self.drop_all()
        self.create_all()
