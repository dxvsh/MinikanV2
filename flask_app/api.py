from flask import request, redirect, jsonify
from flask_app import app, db, bcrypt, cache
from flask_app.models import User, List, Card
from flask_login import login_user, login_required, logout_user, current_user
from flask_app.helper_funcs import make_plot
from datetime import datetime
from flask import Blueprint

api = Blueprint('api', __name__)

# Endpoints for Users:

@api.route('/api/users', methods = ['GET'])
def get_users():
    # get all the users currently in the database
    users = [{"id" : user.id, "username" : user.username, "email" : user.email} for user in User.query.all()]
    return jsonify({"users" : users}), 200

@api.route('/api/users/<username>', methods = ['GET'])
@cache.memoize(timeout=30)
def get_user_by_username(username):
    # get a specific user by username
    usr_obj = User.query.filter_by(username=username).first()
    # only do the following if there actually is a user with the given id, send a 404 response if the user doesn't exist.
    if usr_obj:
        return jsonify({"id" : usr_obj.id, "username" : usr_obj.username, "email" : usr_obj.email})
    else:
        return jsonify(f"No user exists with the username '{username}'."), 404

@api.route('/api/register', methods = ['POST'])
def create_user():
    # a route for creating a new user
    # check if the username is already taken, handle that case
    # only allow creation if username chosen is unique
    # handle password hashing, properly store the password in a hashed format in the db

    username = request.json['username'].strip() # extract the username from the recieved data, strip off any trailing/leading whitespace
    email = request.json['email'].strip()
    password = request.json['password'].strip()

    # check if the username already exists, if it does, return a message like : "username already taken"
    # also check whether the email is already in use or not and if so forbid account creation
    usr = User.query.filter_by(username=username).first()
    usrmail = User.query.filter_by(email=email).first()
    if usr:
        return jsonify(f"A user with username '{username}' already exists. Please choose a different username."), 400
    elif usrmail:
        return jsonify(f"This email is already in use! Please log in if you have an account."), 400 # 400 HTTP status code signifies "Bad Request"
    else:
        # a unique user is being created, so lets add him to the db and hash his password
        hashed_password = bcrypt.generate_password_hash(password) #this generates a hash of the user's password

        usr_obj = User(username=username, email=email, password=hashed_password)
        db.session.add(usr_obj)
        db.session.commit()
        # now the account has been created successfully
        return jsonify(f"User '{username}' successfully created.")

@api.route('/api/login', methods = ['POST'])
def log_the_user_in():
    username = request.json['username']
    password = request.json['password']

    #check if a user with this username exists or not, if it does log him in, if it doesn't display a message "Account doesn't exist"
    user = User.query.filter_by(username=username).first()
    if user: #if user exists, check if the entered password matches the hashed password
        if bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return jsonify("Logged in successfuly.")
        else:
            # if the passwords dont match, send a message "Incorrect Password"
            return jsonify("Incorrect password entered."), 401 # 401 HTTP status code signifies unauthorized access.
    else:
        #display a message, "account doesn't exist"
        return jsonify(f"No user exists with the username '{username}'. Invalid credentials entered."), 401

@api.route('/api/logout')
@login_required
def log_the_user_out():
    logout_user()
    # display a message to the user: "You've been successfully logged out"
    return jsonify("Logged out successfully.")

## Endpoints for Lists:

@api.route('/api/users/<username>/lists', methods = ['GET'])
@login_required
def get_user_lists(username):
    # get all the lists of the given user along with all the cards inside them
    usr_obj = User.query.filter_by(username=username).first()
    if usr_obj:
        usr_lists = []
        for usr_list in usr_obj.lists:
            #card_list will hold all the cards in a list
            card_list = [{"card_id" : card.card_id, "card_title" : card.card_title, "card_content" : card.card_content, 
                        "status" : card.status, "deadline" : card.deadline} for card in usr_list.cards] 
            usr_lists.append({"list_id" : usr_list.list_id, "list_title" : usr_list.list_title, "cards" : card_list})

        return jsonify({"username" : usr_obj.username, "lists" : usr_lists})
    else:
        return jsonify(f"No user exists with the username '{username}'."), 404

@api.route('/api/users/<username>/lists_min', methods = ['GET'])
@login_required
def get_user_lists_minimal(username):
    # get some quick and minimal information about a users lists (without any card info)
    usr_obj = User.query.filter_by(username=username).first()
    if usr_obj:
        usr_lists = [{"list_id" : usr_list.list_id, "list_title" : usr_list.list_title} for usr_list in usr_obj.lists]
        return jsonify({"username" : usr_obj.username, "lists" : usr_lists})
    else:
        return jsonify(f"No user exists with the username '{username}'."), 404


@api.route('/api/users/<username>/lists', methods = ['POST'])
@login_required
def create_user_list(username):
    # create a list for this user
    usr_obj = User.query.filter_by(username=username).first()
    if usr_obj:
        list_title = request.json['list_title']
        list_obj = List(list_title=list_title, user_id = usr_obj.id) #create a new list with given title
        db.session.add(list_obj)
        db.session.commit()
        # list creation was successful
        return jsonify(f"List with title : '{list_title}' successfully created.")
    else:
        return jsonify(f"No user exists with the username '{username}'."), 404

@api.route('/api/users/<username>/lists/<list_id>', methods = ['PUT'])
@login_required
def edit_user_list(username, list_id):
    # edit a given list for this user
    usr_obj = User.query.filter_by(username=username).first()
    list_obj = List.query.get(list_id)
    if usr_obj is None:
        return jsonify(f"No user exists with the username '{username}'."), 404
    elif list_obj is None:
        return jsonify(f"List with ID {list_id} does not exist. List update not possible."), 404
    elif list_obj not in usr_obj.lists:
        # if the list does not belong to the user, then he can't modify it. 
        # the 403 HTTP status code signifies Forbidden access, i.e the person doesn't have the required permission/privilege
        #  to perform the action. we're sending this error here because someone is trying to modify a resource which they don't have access to.
        return jsonify(f"List with ID {list_id} does not belong to to the user '{username}'. Only the list's owner can edit the list."), 403
    else:
        list_title = request.json['list_title']
        list_obj.list_title = list_title
        db.session.commit()
        return jsonify(f"List with ID {list_id} successfully updated. The new title is : '{list_title}'")

@api.route('/api/users/<username>/lists/<list_id>', methods = ['DELETE'])
@login_required
def delete_user_list(username, list_id):
    # delete user list
    usr_obj = User.query.filter_by(username=username).first()
    list_obj = List.query.get(list_id)
    if usr_obj is None:
        return jsonify(f"No user exists with the username '{username}'."), 404
    elif list_obj is None:
        return jsonify(f"List with ID {list_id} does not exist. List deletion not posible."), 404
    elif list_obj not in usr_obj.lists:
        return jsonify(f"List with ID {list_id} does not belong to to the user '{username}'. Only the list's owner can delete the list."), 403
    else:
        db.session.delete(list_obj)
        db.session.commit()
        return jsonify(f"List with ID {list_id} successfully deleted.")

## Endpoints for Cards:

@api.route('/api/users/<username>/lists/<list_id>/cards', methods=['GET'])
@login_required
def get_cards_in_list(username, list_id):
    # get all the cards in this list
    usr_obj = User.query.filter_by(username=username).first()
    list_obj = List.query.get(list_id)
    if usr_obj is None: 
        return jsonify(f"No user exists with the username '{username}'."), 404
    elif list_obj is None:
        return jsonify(f"List with ID {list_id} does not exist."), 404
    elif list_obj not in usr_obj.lists:
        return jsonify(f"List with ID {list_id} does not belong to to the user '{username}'. Only the list's owner can access the contents of the list."), 403
    else:
        card_list = [{"card_id" : card.card_id, "card_title" : card.card_title, "card_content" : card.card_content, 
                        "status" : card.status, "deadline" : card.deadline} for card in list_obj.cards]
        return jsonify({"list_id" : list_id, "list_title" : list_obj.list_title, "cards" : card_list})

@api.route('/api/users/<username>/lists/<list_id>/cards/<card_id>', methods=['GET'])
@login_required
def get_specific_card(username, list_id, card_id):
    # get a specific card by its id
    usr_obj = User.query.filter_by(username=username).first()
    list_obj = List.query.get(list_id)
    card_obj = Card.query.get(card_id)
    if usr_obj is None: 
        return jsonify(f"No user exists with the username '{username}'."), 404
    elif list_obj is None:
        return jsonify(f"List with ID {list_id} does not exist."), 404
    elif list_obj not in usr_obj.lists:
        return jsonify(f"List with ID {list_id} does not belong to to the user '{username}'. Only the list's owner can access the contents of the list."), 403
    elif card_obj is None:
        return jsonify(f"Card with ID {card_id} does not exist. Cannot get card."), 404
    elif card_obj not in list_obj.cards:
        return jsonify(f"Card with ID {card_id} does not belong to to the list with ID '{list_id}'. Cannot get card."), 403
    else:
        return jsonify({"card_info" : {"card_id" : card_obj.card_id, "card_title" : card_obj.card_title, "card_content" : card_obj.card_content, 
                        "status" : card_obj.status, "deadline" : card_obj.deadline, "list_id" : list_obj.list_id}})

@api.route('/api/users/<username>/lists/<list_id>/cards', methods=['POST'])
@login_required
def create_new_card(username, list_id):
    # create a new card in this list
    usr_obj = User.query.filter_by(username=username).first()
    list_obj = List.query.get(list_id)
    if usr_obj is None: 
        return jsonify(f"No user exists with the username '{username}'."), 404
    elif list_obj is None:
        return jsonify(f"List with ID {list_id} does not exist."), 404
    elif list_obj not in usr_obj.lists:
        return jsonify(f"List with ID {list_id} does not belong to to the user '{username}'. Only the list's owner can create cards in the list."), 403
    else:
        card_title = request.json['card_title']
        card_content = request.json['card_content']
        status = request.json['status']
        deadline = request.json['deadline']
        
        #this deadline date is a string, need to convert it to datetype, can use the strptime method for this:
        proper_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        # create a new card with these values
        card_obj = Card(card_title=card_title, card_content=card_content, status=status, deadline=proper_date, list_id=list_obj.list_id)
        
        db.session.add(card_obj)
        db.session.commit()

        return jsonify(f"Card with title : '{card_title}' successfully created.")


@api.route('/api/users/<username>/lists/<list_id>/cards/<card_id>', methods=['PUT'])
@login_required
def edit_user_card(username, list_id, card_id):
    # create a new card in this list
    usr_obj = User.query.filter_by(username = username).first()
    list_obj = List.query.get(list_id)
    card_obj = Card.query.get(card_id)
    if usr_obj is None: 
        return jsonify(f"No user exists with the username '{username}'."), 404
    elif list_obj is None:
        return jsonify(f"List with ID {list_id} does not exist."), 404
    elif list_obj not in usr_obj.lists:
        return jsonify(f"List with ID {list_id} does not belong to to the user '{username}'. Only the list's owner can edit cards in the list."), 403
    elif card_obj is None:
        return jsonify(f"Card with ID {card_id} does not exist. Cannot update card."), 404
    elif card_obj not in list_obj.cards:
        return jsonify(f"Card with ID {card_id} does not belong to to the list with ID '{list_id}'. Cannot edit card."), 403
    else:
        card_title = request.json['card_title']
        card_content = request.json['card_content']
        status = request.json['status']
        deadline = request.json['deadline']
        # we should be able to change the list a card belongs to
        list_id = int(request.json['list_id']) #this will be the list that the card belongs to from now on
        
        #change the values of the card using these new ones
        card_obj.card_title = card_title
        card_obj.card_content = card_content
        card_obj.status = status
        card_obj.list_id = list_id

        #this deadline date is a string, need to convert to datetype, can use the strptime method for this:
        proper_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        card_obj.deadline = proper_date
        
        db.session.commit()
        return jsonify(f"Card with ID {card_obj.card_id}, title : '{card_title}' successfully updated.")

@api.route('/api/users/<username>/lists/<list_id>/cards/<card_id>', methods=['DELETE'])
@login_required
def delete_user_card(username, list_id, card_id):
    # create a new card in this list
    usr_obj = User.query.filter_by(username=username).first()
    list_obj = List.query.get(list_id)
    card_obj = Card.query.get(card_id)
    if usr_obj is None: 
        return jsonify(f"No user exists with the username '{username}'."), 404
    elif list_obj is None:
        return jsonify(f"List with ID {list_id} does not exist."), 404
    elif list_obj not in usr_obj.lists:
        return jsonify(f"List with ID {list_id} does not belong to to the user '{username}'. Only the list's owner can delete cards in the list."), 403
    elif card_obj is None:
        return jsonify(f"Card with ID {card_id} does not exist. Card deletion not possible."), 404
    elif card_obj not in list_obj.cards:
        return jsonify(f"Card with ID {card_id} does not belong to to the list with ID '{list_id}'. Cannot delete card."), 403
    else:
        card_id = card_obj.card_id
        card_title = card_obj.card_title
        db.session.delete(card_obj)        
        db.session.commit()
        return jsonify(f"Card with ID {card_id}, title : '{card_title}' was successfully deleted.")

@api.route('/api/users/<username>/stats', methods=['GET'])
@cache.memoize(timeout=10)
@login_required
def generate_stats(username):
    usr_obj = User.query.filter_by(username=username).first()
    if usr_obj:
        stats = [] 
        for usr_list in usr_obj.lists:
            list_stats = make_plot(usr_list.list_id)
            stats.append(list_stats)
        return jsonify({"username" : usr_obj.username, "stats" : stats})
    else:
        return jsonify(f"User with username '{username}' does not exist."), 404