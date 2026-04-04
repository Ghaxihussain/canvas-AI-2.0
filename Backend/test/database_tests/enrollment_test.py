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






def test_get_user_enrollments(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    User.create(name="Ali", email="a@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    student = User.get_user_by_email(email="a@gmail.com", db=db)

    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    Class.create(name="Science", description="Science class", class_code="SCI101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)
    science = Class.get_class_by_code(class_code="SCI101", db=db)

    Enrollment.create(class_id=math.id, user_id=student.id, role="student", db=db)
    Enrollment.create(class_id=science.id, user_id=student.id, role="student", db=db)

    enrollments = Enrollment.get_user_enrollments(user_id=student.id, db=db)

    assert len(enrollments) == 2
    assert all(e["user_id"] == student.id for e in enrollments)
    assert any(e["class_id"] == math.id for e in enrollments)
    assert any(e["class_id"] == science.id for e in enrollments)

def test_get_user_enrollments_empty(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)

    enrollments = Enrollment.get_user_enrollments(user_id=owner.id, db=db)
    assert enrollments == []

def test_get_user_enrollments_not_mixed(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    User.create(name="Ali", email="a@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    other = User.get_user_by_email(email="a@gmail.com", db=db)

    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)

    Enrollment.create(class_id=math.id, user_id=owner.id, role="teacher", db=db)

    enrollments = Enrollment.get_user_enrollments(user_id=other.id, db=db)
    assert enrollments == [] 




def test_get_class_enrollments(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    User.create(name="Ali", email="a@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    student = User.get_user_by_email(email="a@gmail.com", db=db)

    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)

    Enrollment.create(class_id=math.id, user_id=owner.id, role="teacher", db=db)
    Enrollment.create(class_id=math.id, user_id=student.id, role="student", db=db)

    enrollments = Enrollment.get_class_enrollments(class_id=math.id, db=db)

    assert len(enrollments) == 2
    assert any(e["name"] == "Ghazi" and e["role"] == "teacher" for e in enrollments)
    assert any(e["name"] == "Ali" and e["role"] == "student" for e in enrollments)




def test_get_class_enrollments_empty(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)

    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)

    enrollments = Enrollment.get_class_enrollments(class_id=math.id, db=db)
    assert enrollments == []