from db.classes import Class
from db.users import User


def test_create_class(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)

    result = Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    result2 = Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)

    assert result == True
    assert result2 == False  


def test_create_class_invalid_owner(db):
    result = Class.create(name="Math", description="Math class", class_code="MATH101", owner_id="xyz", db=db)
    assert result is None  


def test_get_class_by_id(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)

    class_ = Class.get_class_by_code(class_code="MATH101", db=db)
    assert class_ is not None

    found = Class.get_class_by_id(class_id=class_.id, db=db)
    assert found is not None
    assert found.id == class_.id


def test_get_class_by_code(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)

    class_ = Class.get_class_by_code(class_code="MATH101", db=db)
    assert class_ is not None
    assert class_.class_code == "MATH101"


def test_get_class_not_found(db):
    class_ = Class.get_class_by_code(class_code="NOTEXIST", db=db)
    assert class_ is None


def test_get_classes_by_owner(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)

    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    Class.create(name="Science", description="Science class", class_code="SCI101", owner_id=owner.id, db=db)
    Class.create(name="English", description="English class", class_code="ENG101", owner_id=owner.id, db=db)

    classes = Class.get_classes_by_owner(owner_id=owner.id, db=db)
    assert len(classes) == 3


def test_delete_class(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    User.create(name="Ali", email="a@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    other = User.get_user_by_email(email="a@gmail.com", db=db)

    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)

    assert Class.delete_class(class_id=class_.id, owner_id=other.id, db=db) == False


    assert Class.delete_class(class_id=class_.id, owner_id=owner.id, db=db) == True
    assert Class.get_class_by_id(class_id=class_.id, db=db) is None


def test_delete_class_not_found(db):

    result = Class.delete_class(class_id="xyz", owner_id="xyz", db=db)
    assert result == False