from flask_app import db, login_manager
from flask_login import UserMixin

#This user_loader is used to reload the user object from the user ID stored in the session.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Need to inherit UserMixin in the User class for flask_login to work properly
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    email = db.Column(db.String, unique = True, nullable = False)
    password = db.Column(db.String(80), nullable = False)
    #Set up a one -> many relationship with List, because a User can have multiple lists
    lists = db.relationship('List', backref='user', cascade='all,delete')

class List(db.Model):
    list_id = db.Column(db.Integer, primary_key = True)
    list_title = db.Column(db.String(30), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    #set up a one -> many relationship with Card, because a list can contain multiple cards
    cards = db.relationship('Card', backref='list', cascade='all,delete')

class Card(db.Model):
    card_id = db.Column(db.Integer, primary_key = True)
    card_title = db.Column(db.String(30), nullable = False)
    card_content = db.Column(db.Text)
    status = db.Column(db.String, default = 'Pending') #completion status of the card: could be "completed" or "pending"
    deadline = db.Column(db.Date, nullable = False) #date when the card is due
    list_id = db.Column(db.Integer, db.ForeignKey('list.list_id'), nullable = False)