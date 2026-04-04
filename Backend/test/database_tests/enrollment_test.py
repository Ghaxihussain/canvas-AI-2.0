from db.classes import Class
from db.users import User
from db.enrollment import Enrollment
from uuid import uuid4

def test_create_enrollment(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)

    result = Enrollment.create(class_id=class_.id, user_id=owner.id, role="teacher", db=db)
    result2 = Enrollment.create(class_id=class_.id, user_id=owner.id, role="teacher", db=db) 

    assert result == True
    assert result2 == False

def test_create_enrollment_invalid_role(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)

    result = Enrollment.create(class_id=class_.id, user_id=owner.id, role="admin", db=db)
    assert result == False

def test_create_enrollment_multiple_users(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    User.create(name="Ali", email="a@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    student = User.get_user_by_email(email="a@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)

    r1 = Enrollment.create(class_id=class_.id, user_id=owner.id, role="teacher", db=db)
    r2 = Enrollment.create(class_id=class_.id, user_id=student.id, role="student", db=db)

    assert r1 == True
    assert r2 == True

def test_update_enrollment_role(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)
    Enrollment.create(class_id=class_.id, user_id=owner.id, role="student", db=db)

    result = Enrollment.update_role(class_id=class_.id, user_id=owner.id, new_role="teacher", db=db)
    assert result == True

def test_update_enrollment_invalid_role(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)
    Enrollment.create(class_id=class_.id, user_id=owner.id, role="student", db=db)

    result = Enrollment.update_role(class_id=class_.id, user_id=owner.id, new_role="admin", db=db)
    assert result == False

def test_update_enrollment_not_found(db):
    result = Enrollment.update_role(class_id=uuid4(), user_id=uuid4(), new_role="teacher", db=db)
    assert result == False

def test_delete_enrollment(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)
    Enrollment.create(class_id=class_.id, user_id=owner.id, role="teacher", db=db)

    result = Enrollment.delete(class_id=class_.id, user_id=owner.id, db=db)
    assert result == True

def test_delete_enrollment_not_found(db):
    result = Enrollment.delete(class_id=uuid4(), user_id=uuid4(), db=db)
    assert result == False

def test_delete_enrollment_twice(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    class_ = Class.get_class_by_code(class_code="MATH101", db=db)
    Enrollment.create(class_id=class_.id, user_id=owner.id, role="teacher", db=db)

    assert Enrollment.delete(class_id=class_.id, user_id=owner.id, db=db) == True
    assert Enrollment.delete(class_id=class_.id, user_id=owner.id, db=db) == False 