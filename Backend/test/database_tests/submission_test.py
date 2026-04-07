from uuid import uuid4
from db.submissions import Submission
from db.assignments import Assignment
from db.classes import Class
from db.users import User


def setup(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    User.create(name="Ali", email="a@gmail.com", password="123", db=db)
    teacher = User.get_user_by_email(email="g@gmail.com", db=db)
    student = User.get_user_by_email(email="a@gmail.com", db=db)
    Class.create(name="Math", description="Math class", class_code="MATH101", owner_id=teacher.id, db=db)
    math = Class.get_class_by_code(class_code="MATH101", db=db)
    Assignment.create(class_id=math.id, created_by=teacher.id, title="HW1", db=db)
    assignments = Assignment.get_assignments_by_class_id(class_id=math.id, db=db)
    return teacher, student, assignments[0]


def test_create_submission(db):
    teacher, student, assignment = setup(db)

    result = Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)
    assert result == True


def test_create_submission_with_content(db):
    teacher, student, assignment = setup(db)

    result = Submission.create(
        assignment_id=assignment.id,
        user_id=student.id,
        db=db,
        text_content="My answer is 42",
        file_url="s3://bucket/submission.pdf"
    )
    assert result == True


def test_create_submission_duplicate(db):
    teacher, student, assignment = setup(db)

    Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)
    result = Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)
    assert result == False


def test_get_submission_by_id(db):
    teacher, student, assignment = setup(db)
    Submission.create(assignment_id=assignment.id, user_id=student.id, text_content="answer", db=db)

    submission = Submission.get_submission_by_assignment_and_user(
        assignment_id=assignment.id, user_id=student.id, db=db
    )
    found = Submission.get_submission_by_id(submission_id=submission.id, db=db)

    assert found is not None
    assert found.id == submission.id


def test_get_submission_by_id_not_found(db):
    result = Submission.get_submission_by_id(submission_id=uuid4(), db=db)
    assert result is None


def test_get_submission_by_assignment_and_user(db):
    teacher, student, assignment = setup(db)
    Submission.create(assignment_id=assignment.id, user_id=student.id, text_content="answer", db=db)

    submission = Submission.get_submission_by_assignment_and_user(
        assignment_id=assignment.id, user_id=student.id, db=db
    )
    assert submission is not None
    assert submission.user_id == student.id
    assert submission.assignment_id == assignment.id


def test_get_submission_by_assignment_and_user_not_found(db):
    result = Submission.get_submission_by_assignment_and_user(
        assignment_id=uuid4(), user_id=uuid4(), db=db
    )
    assert result is None


def test_get_submissions_by_assignment(db):
    teacher, student, assignment = setup(db)
    User.create(name="Sara", email="s@gmail.com", password="123", db=db)
    sara = User.get_user_by_email(email="s@gmail.com", db=db)

    Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)
    Submission.create(assignment_id=assignment.id, user_id=sara.id, db=db)

    submissions = Submission.get_submissions_by_assignment(assignment_id=assignment.id, db=db)
    assert len(submissions) == 2


def test_get_submissions_by_assignment_empty(db):
    teacher, student, assignment = setup(db)

    submissions = Submission.get_submissions_by_assignment(assignment_id=assignment.id, db=db)
    assert submissions == []


def test_get_submissions_by_user(db):
    teacher, student, assignment = setup(db)

    Assignment.create(class_id=assignment.class_id, created_by=teacher.id, title="HW2", db=db)
    all_assignments = Assignment.get_assignments_by_class_id(class_id=assignment.class_id, db=db)
    hw2 = next(a for a in all_assignments if a.title == "HW2")

    Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)
    Submission.create(assignment_id=hw2.id, user_id=student.id, db=db)

    submissions = Submission.get_submissions_by_user(user_id=student.id, db=db)
    assert len(submissions) == 2


def test_get_submissions_by_user_empty(db):
    teacher, student, assignment = setup(db)

    submissions = Submission.get_submissions_by_user(user_id=student.id, db=db)
    assert submissions == []


def test_update_submission(db):
    teacher, student, assignment = setup(db)
    Submission.create(assignment_id=assignment.id, user_id=student.id, text_content="old answer", db=db)

    result = Submission.update_submission(
        assignment_id=assignment.id, user_id=student.id, db=db,
        text_content="updated answer"
    )
    updated = Submission.get_submission_by_assignment_and_user(
        assignment_id=assignment.id, user_id=student.id, db=db
    )

    assert result == True
    assert updated.text_content == "updated answer"


def test_update_submission_not_found(db):
    result = Submission.update_submission(
        assignment_id=uuid4(), user_id=uuid4(), db=db, text_content="answer"
    )
    assert result == False


def test_grade_submission(db):
    teacher, student, assignment = setup(db)
    Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)

    result = Submission.grade_submission(
        assignment_id=assignment.id, user_id=student.id,
        grade=90, feedback="Good work!", db=db
    )
    graded = Submission.get_submission_by_assignment_and_user(
        assignment_id=assignment.id, user_id=student.id, db=db
    )

    assert result == True
    assert graded.graded == True
    assert graded.grade == 90
    assert graded.feedback == "Good work!"


def test_grade_submission_without_feedback(db):
    teacher, student, assignment = setup(db)
    Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)

    result = Submission.grade_submission(
        assignment_id=assignment.id, user_id=student.id, grade=75, db=db
    )
    graded = Submission.get_submission_by_assignment_and_user(
        assignment_id=assignment.id, user_id=student.id, db=db
    )

    assert result == True
    assert graded.graded == True
    assert graded.grade == 75


def test_grade_submission_not_found(db):
    result = Submission.grade_submission(
        assignment_id=uuid4(), user_id=uuid4(), grade=100, db=db
    )
    assert result == False


def test_delete_submission(db):
    teacher, student, assignment = setup(db)
    Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)

    result = Submission.delete_submission(assignment_id=assignment.id, user_id=student.id, db=db)
    assert result == True

    gone = Submission.get_submission_by_assignment_and_user(
        assignment_id=assignment.id, user_id=student.id, db=db
    )
    assert gone is None


def test_delete_submission_not_found(db):
    result = Submission.delete_submission(assignment_id=uuid4(), user_id=uuid4(), db=db)
    assert result == False


def test_delete_submission_twice(db):
    teacher, student, assignment = setup(db)
    Submission.create(assignment_id=assignment.id, user_id=student.id, db=db)

    assert Submission.delete_submission(assignment_id=assignment.id, user_id=student.id, db=db) == True
    assert Submission.delete_submission(assignment_id=assignment.id, user_id=student.id, db=db) == False