import os
from flask_cors import CORS

from flask import Flask

app = Flask(__name__)
CORS(app)

app.debug = True
app.config['SECRET_KEY'] = os.urandom(24)

from app import routes