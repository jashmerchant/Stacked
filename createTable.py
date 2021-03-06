import os

from flask import Flask, render_template, request

from models import *

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def main():
      # Create tables based on each table definition in `models`
      db.create_all()

if __name__ == "__main__":
      # Allows for command line interaction with Flask application
      with app.app_context():
          main()