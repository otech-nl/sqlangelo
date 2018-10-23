from tests import models
import unittest


class TestBase(unittest.TestCase):

    def test_inheritance(self):
        self.assertTrue(hasattr(models.User, 'identities'))
        for cls in [models.User, models.Employee]:
            self.assertTrue(hasattr(cls, '_identity'))
            self.assertTrue(cls.__mapper_args__['polymorphic_identity'] == cls.__name__)


    def test_reference(self):
        self.assertTrue(hasattr(models.Employee, 'company'))


    def test_crossreference(self):
        self.assertTrue(hasattr(models.Group, 'users'))
        self.assertTrue(hasattr(models.User, 'groups'))
