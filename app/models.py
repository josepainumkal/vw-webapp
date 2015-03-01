from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from . import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """
    Our User model. Users have biographical information, a user id, user name,
    and password.
    """
    __tablename__ = 'users'

    # columns with no special methods
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    affiliation = db.Column(db.String(64), index=True)
    state = db.Column(db.String(2), index=True)
    city = db.Column(db.String(20), index=True)
    email = db.Column(db.String(20), unique=True)

    # password/password_hash
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # account confirmation

    confirmed = db.Column(db.Boolean, default=False)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.secret_key, expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.secret_key)
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        db.session.commit()

        return True

    def __repr__(self):
        return '<User %r>' % self.name


class Resource(db.Model):
    """
    Model to represent a user-contributed resource. Now we'll need to
    set up relationship between the id in this table and the User
    model id, since this is how we can match users to their
    contributions.
    """
    # TODO figure out how to match this to the id from User
    resource_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), index=True, unique=True)
    uuid = db.Column(db.String(36), index=True, unique=True)
    description = db.Column(db.Text())
    keywords = db.Column(db.Text())
    url = db.Column(db.Text())


    def __repr__(self):
        print self.uuid
        return "<Resource %s:\n\tuser_id: %s,\n\ttitle: %s,\n\tuuid: %s,\n\tdescription: %s,\n\tkeywords: %s,\n\turl: %s>" % (self.resource_id, self.user_id,
                self.title, self.uuid, self.description,
                self.keywords, self.url)
