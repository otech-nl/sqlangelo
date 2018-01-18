from tests import models


def test_basemodel():
    assert models.BaseModel.__abstract__
    assert hasattr(models.BaseModel, 'id')
