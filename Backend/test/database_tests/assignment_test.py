from uuid import uuid4
from db.assignments import Assignment
from db.classes import Class
from db.users import User


def test_create_assignment(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)

    result = Assignment.create(class_id=math.id, created_by=owner.id, title="HW1", db=db)
    assert result == True


def test_create_assignment_with_all_fields(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)

    result = Assignment.create(
        class_id=math.id, created_by=owner.id, title="HW1", db=db,
        text_content="Solve problems 1-10",
        rubric_text_content="10 points each",
        assignment_file_url="s3://bucket/hw1.pdf",
        rubric_file_url="s3://bucket/rubric.pdf",
        total_grade=100
    )
    assert result == True


def test_get_assignment_by_id(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)
    Assignment.create(class_id=math.id, created_by=owner.id, title="HW1", db=db)

    assignments = Assignment.get_assignments_by_class_id(class_id=math.id, db=db)
    assignment = Assignment.get_assignment_by_id(assignment_id=assignments[0].id, db=db)

    assert assignment is not None
    assert assignment.title == "HW1"


def test_get_assignment_by_id_not_found(db):
    result = Assignment.get_assignment_by_id(assignment_id=uuid4(), db=db)
    assert result is None


def test_get_assignments_by_class_id(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)

    Assignment.create(class_id=math.id, created_by=owner.id, title="HW1", db=db)
    Assignment.create(class_id=math.id, created_by=owner.id, title="HW2", db=db)
    Assignment.create(class_id=math.id, created_by=owner.id, title="HW3", db=db)

    assignments = Assignment.get_assignments_by_class_id(class_id=math.id, db=db)
    assert len(assignments) == 3


def test_get_assignments_by_class_id_empty(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)

    assignments = Assignment.get_assignments_by_class_id(class_id=math.id, db=db)
    assert assignments == []


def test_update_assignment(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)
    Assignment.create(class_id=math.id, created_by=owner.id, title="HW1", db=db)

    assignments = Assignment.get_assignments_by_class_id(class_id=math.id, db=db)
    assignment_id = assignments[0].id

    result = Assignment.update_assignment(assignment_id=assignment_id, db=db, title="HW1 Updated", total_grade=50)
    updated = Assignment.get_assignment_by_id(assignment_id=assignment_id, db=db)

    assert result == True
    assert updated.title == "HW1 Updated"
    assert updated.total_grade == 50


def test_update_assignment_not_found(db):
    result = Assignment.update_assignment(assignment_id=uuid4(), db=db, title="Ghost")
    assert result == False


def test_delete_assignment(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)
    Assignment.create(class_id=math.id, created_by=owner.id, title="HW1", db=db)

    assignments = Assignment.get_assignments_by_class_id(class_id=math.id, db=db)
    assignment_id = assignments[0].id

    assert Assignment.delete_assignment(assignment_id=assignment_id, db=db) == True
    assert Assignment.get_assignment_by_id(assignment_id=assignment_id, db=db) is None


def test_delete_assignment_not_found(db):
    result = Assignment.delete_assignment(assignment_id=uuid4(), db=db)
    assert result == False


def test_delete_assignment_twice(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    owner = User.get_user_by_email(email="g@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=owner.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)
    Assignment.create(class_id=math.id, created_by=owner.id, title="HW1", db=db)

    assignments = Assignment.get_assignments_by_class_id(class_id=math.id, db=db)
    assignment_id = assignments[0].id

    assert Assignment.delete_assignment(assignment_id=assignment_id, db=db) == True
    assert Assignment.delete_assignment(assignment_id=assignment_id, db=db) == False