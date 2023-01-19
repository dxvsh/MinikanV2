# MinikanV2
Minikan is a simple and minimal Kanban webapp for managing and organizing your tasks. It helps to increase productivity by letting you visualizing your workflow.
Check out a video demo on [YouTube](https://www.youtube.com/watch?v=SXlGlq8kYJw)

## Features
* CRUD operations on user lists and cards (create, update and delete cards and lists)
* RESTful API for interacting with resources
* Ability to set deadlines and update the status of cards
* Summary page for viewing statistics about lists
* Proper login/signup system (implemented using flask-login)
* Password Hashing for security (implemented using flask-bcrypt)
* Import/Export data as CSV
* Periodic email reminders to users (implemented using redmail)
* Monthly stats reports(pdfs) delivered to the users inbox via email
* Custom error pages for when things go wrong

## Technologies Used

Minikan is created using:

+ Flask (for APIs/backend), VueJS (as the frontend framework)
+ Flask-SQLAlchemy (for managing databases)
+ Flask-login (for setting up a login/signup system)
+ Flask-Bcrypt (for hashing passwords)
+ Flask-Caching (for caching certain api responses)
+ Matplotlib (for creating pie charts)
+ Celery (as the task queue)
+ Redis (for caching and as a message broker)
+ Redmail (used for sending emails)
+ Pdfkit (for generating pdfs from html)

## Project structure
This app consists of the following files:

```
requirements.txt			# required packages for running the application
README.md				# contains info and setup instructions for the app
run.py					# runs the app
flask_app/				# application package
	__init__.py			# initializes the app, creates a Flask instance
	api.py				# REST API for the application
	views.py			# contains all the views for the app
	models.py			# database models for the application
	tasks.py			# code for periodic/scheduled tasks
	helper_funcs.py			# helper funcs for generating stats, pie charts, pdfs etc
	kanban.sqlite3			# sqlite database for the app
	.env				# environment variables
	static/				# static files like css, js, images
	templates/			# contains the html templates
	user_uploads/			# stores the files uploaded by the user (eg. csv files)
	user_reports/			# stores the pdf reports for users
```



## Instructions for getting started:
Follow the instructions below to run the app on your local machine:

1. The following dependencies must be installed for the application to work:

   `redis` (Tested with v7.0.5)

   `wkhtmltopdf` (Tested with v0.12.6)

   You can use your distribution's package manager to install them.

   For example, on fedora you can run:

   ```
   $ dnf install redis wkhtmltopdf
   ```

2. Now you need to create a virtual environment. Unzip the project file and inside the root of the project directory, execute:

   ```
   $ pip3 install virtualenv
   ```

   ```
   $ python3 -m venv venv
   ```

2. Activate the Virtual Environment

   ```
   $ source venv/bin/activate (Linux)
   \venv\Scripts\activate     (Windows)
   ```

3. Install all the requirements

   ```
   (venv) $ pip3 install -r requirements.txt
   ```

4. Before you go on, make sure to specify the appropriate values in the `.env` file. You need to substitute your own values for the username and password! This is the account from which reminder emails and pdf reports will be sent.

   Example values:

   ```
   'USERNAME' = 'example@example.com'
   'PASSWORD' = 'super-secret-password'
   'HOST' = 'smtp.gmail.com'
   'PORT' = '587'
   'TIMEZONE' = 'Europe/Amsterdam'
   ```

5. Now to actually start off the application, run the following:

   a. Start the redis server:

   ```
   (venv) $ redis-server
   ```

   b. Start the celery system:

   ```
   (venv) $ celery -A flask_app.tasks worker --loglevel=INFO
   ```

   c. Start celery beat (the task scheduler):

   ```
   (venv) $ celery -A flask_app.tasks beat --loglevel=INFO
   ```

   d. Run the application:

   ```
   (venv) $ python3 run.py
   ```

If everything went well, the app should now be running at: http://127.0.0.1:5000
You can visit this link in your browser to get started
