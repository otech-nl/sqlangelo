from tests.models import db


def test_basemodel():
    assert db.BaseModel.__abstract__
    assert hasattr(db.BaseModel, 'id')
