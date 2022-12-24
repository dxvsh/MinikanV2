from flask import render_template, request, redirect, url_for, send_file
from flask_app import app, db
from flask_app.models import User, List, Card
from flask_login import login_user, login_required, logout_user, current_user
from flask_app.tasks import generate_csv, generate_list_csv
from datetime import datetime
import csv
from flask import Blueprint

views = Blueprint('views', __name__)

# the main landing page of the site
@views.route('/')
def landing():
    return render_template('landing.html')

@views.route('/register')
def register():
    return render_template('register.html') #display the registration form

@views.route('/login')
def login():
    return render_template('login.html') #display the login form

# the main user dashboard
@views.route('/<username>/dashboard')
@login_required
def dashboard(username):
    return render_template('dashboard.html', user=current_user)

@views.route('/<username>/create-list')
@login_required
def create_list(username):
    return render_template('create_list.html', user=current_user) #display the list creation form

@views.route('/<username>/edit-list/<list_id>')
@login_required
def edit_list(username, list_id):
    return render_template('edit_list.html', user = current_user, list_id = list_id) #display the list edit form

@views.route('/<username>/create-card/inside-list/<list_id>')
@login_required
def create_card(username, list_id):
    return render_template('create_card.html', user = current_user, list_id = list_id) # display the card creation form

@views.route('/<username>/edit-card/<card_id>/inside-list/<list_id>')
@login_required
def edit_card(username, card_id, list_id):
    return render_template('edit_card.html', user = current_user, card_id=card_id, list_id=list_id) #display the edit card form

@views.route('/<username>/stats')
@login_required
def stats(username):
    #stats and summary page for the user
    return render_template('stats.html', user=current_user)

@views.route('/<username>/export')
@login_required
def export_all(username):
    # export all user data, give user the option to choose a file destination
    # here we call the celery task for generating a csv and wait for it to complete
    # once its done we send generated csv to the user.
    # do note that the celery server should be running for this export to work!
    generate_csv.delay(username).wait()
    path = 'exported_content.csv'
    return send_file(path, as_attachment=True)

@views.route('/<username>/export-list/<list_id>')
@login_required
def export_list(username, list_id):
    # similar to the above function but only for lists, it exports all the data
    # about the given list and the cards inside it.
    generate_list_csv.delay(list_id).wait()
    path = 'exported_content.csv'
    return send_file(path, as_attachment=True)

@views.route('/<username>/import', methods=['GET', 'POST'])
@login_required
def import_csv(username):
    user = User.query.filter_by(username=username).first()
    if request.method == 'GET':
        return render_template('import.html')
    else:
        f = request.files['file']
        f.filename = 'user_import.csv' #set a name for this file
        f.save(app.config['UPLOAD_FOLDER']+f.filename) #save the file in the upload_folder

        g = open('./flask_app/user_uploads/user_import.csv', 'r')
        g.readline() #skip the header line
        reader = csv.reader(g)
        
        prev_list_id = 0
        for line in reader:
            current_list_id = int(line[0])
            list_title = line[1].strip()
            card_title = line[3].strip()
            card_content = line[4].strip()
            card_status = line[5].strip()
            card_deadline = line[6].strip()

            #this deadline date is a string, need to convert to datetype, can use the strptime method for this:
            proper_date = datetime.strptime(card_deadline, '%Y-%m-%d').date()

            if prev_list_id != current_list_id:
                list_obj = List(list_title=list_title, user_id=user.id)
                db.session.add(list_obj)
                db.session.commit()
                card_obj = Card(card_title=card_title, card_content=card_content, status=card_status, deadline=proper_date, list_id=list_obj.list_id)
                db.session.add(card_obj)
                db.session.commit()
                prev_list_id = current_list_id #update the previous list id
            else:
                card_obj = Card(card_title=card_title, card_content=card_content, status=card_status, deadline=proper_date, list_id=list_obj.list_id)
                db.session.add(card_obj)
                db.session.commit()        

        return redirect(f'/{username}/dashboard')

@views.route('/logout')
@login_required
def logout():
    logout_user()
    # display a message to the user: "You've been successfully logged out"
    return render_template('logged_out.html')

@views.route('/about')
def about():
    return render_template('about.html')

################## creating some custom error pages
# can create a 404 page like this, anytime a 404 happens this page will show up
@app.errorhandler(404)
def err(e):
    return render_template('404_page.html'), 404

# a page for handling 401 "Unauthorized" errors, if someone attempts to access a 
# resource that requires auth/login and doesn't provide it, this page will show up.
@app.errorhandler(401)
def err(e):
    return render_template('401_unauthorized.html'), 401