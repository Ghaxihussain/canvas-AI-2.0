
from db.users import User



def test_create_user(db):
    result = User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    result2 = User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)

    assert result == True
    assert result2 == False


def test_get_user_by_email(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    user = User.get_user_by_email(email ="g@gmail.com", db=db)
    assert user is not None
    assert user.email == "g@gmail.com"

def test_user_not_found(db):
    user = User.get_user_by_email(email="notfound@gmail.com", db=db)
    assert user is None


def test_verify_password(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    assert User.verify_user_password(email="g@gmail.com", password= "123", db = db) == True
    assert User.verify_user_password(email="g@gmail.com", password= "1232", db = db) == False


def test_delete_user(db):
    User.create(name="Ghazi", email="g@gmail.com", password="123", db=db)
    User.create(name="Ghazi", email="a@gmail.com", password="123", db=db)
    User.create(name="Ghazi", email="b@gmail.com", password="123", db=db)

    assert User.get_user_by_email(email="g@gmail.com", db = db) is not None
    User.delete_user(email = "g@gmail.com", password= "123", db = db)
    assert User.get_user_by_email(email="g@gmail.com", db = db).is_deleted == True
    assert User.delete_user(email = "a@gmail.com", password= "1234", db = db) == False
    assert User.get_user_by_email(email= "a@gmail.com", db = db)


    
