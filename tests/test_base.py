from tests import models
import unittest


class TestBase(unittest.TestCase):

    def test_basemodel(self):
        self.assertTrue(models.BaseModel.__abstract__)
        self.assertTrue(hasattr(models.BaseModel, 'id'))
