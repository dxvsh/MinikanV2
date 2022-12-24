from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_caching import Cache

app = Flask(__name__) #creating a flask instance

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#flask-login needs a secret key to work
app.config['SECRET_KEY'] = 'a_very_secret_key'
app.config['UPLOAD_FOLDER'] = "./flask_app/user_uploads/" # folder where the user uploaded files will be saved

db = SQLAlchemy(app) #creating a SQLAlchemy instance
login_manager = LoginManager()
login_manager.init_app(app) #creating a login_manager instance
bcrypt = Bcrypt(app) #creating a bcrypt instance
cache = Cache() #creating an instance of flask_caching
# set up the config for flask_caching, and instruct it to use Redis as the cache type
cache.init_app(app, config={'CACHE_TYPE': 'RedisCache', 'CACHE_REDIS_HOST': 'localhost', 'CACHE_REDIS_PORT': 6379})

from flask_app.views import views
from flask_app.api import api

app.register_blueprint(views)
app.register_blueprint(api)