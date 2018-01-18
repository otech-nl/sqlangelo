from tests import models


def test_inheritance():
    assert hasattr(models.User, 'identities')
    for cls in [models.User, models.Employee]:
        assert hasattr(cls, '_identity')
        assert cls.__mapper_args__['polymorphic_identity'] == cls.__name__


def test_reference():
    assert hasattr(models.Employee, 'company')


def test_crossreference():
    assert hasattr(models.Group, 'users')
    assert hasattr(models.User, 'groups')
