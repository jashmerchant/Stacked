import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/userhome", methods=['GET', 'POST'])
def userhome():
    if "user" in session:
        user = session["user"]     
        return render_template("userhome.html", user=user)
    else:
        return redirect(url_for("login"))
    

@app.route("/userhomepost", methods=['POST'])
def userhomepost():
    bookquery = request.form["bookquery"]
    books = db.execute("SELECT * FROM books WHERE isbn LIKE :bookquery OR title LIKE :bookquery OR author LIKE :bookquery OR year LIKE :bookquery", {"bookquery": '%'+bookquery+'%'}).fetchall()
    return render_template("userhomepost.html", bookquery=bookquery, books=books) 

@app.route("/book/<string:title>")
def book(title):
        abook = db.execute("SELECT * FROM books WHERE title = :title", {"title": title}).fetchone()
        isbn = abook.isbn
        reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": abook.isbn}).fetchall()
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "6kIZ5ttIXxHvb0h9DIIuCg", "isbns": isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json() 
        avgrating = data["books"][0]["average_rating"]
        rcount = data["books"][0]["work_ratings_count"]
        return render_template("book.html", abook=abook, avgrating=avgrating, rcount=rcount, reviews=reviews)

@app.route("/book/<string:isbn>", methods=['POST'])
def bookisbn(isbn):
    rating = request.form["gridRadios"]
    review = request.form["review"]
    user = session["user"]
    reviewisbn = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    theBoook = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    for reviews in reviewisbn:
        if reviews.isbn == isbn and reviews.user == user:
            flash("You have submitted a review already!")
            return redirect(url_for("book", title=theBoook.title))

    areview = Review(isbn=isbn, user=user, rating=rating, review=review)
    db.add(areview)
    db.commit()
    return redirect(url_for("book", title=theBoook.title))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if "user" in session:
        return redirect(url_for("userhome"))
    else:
        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
            {"username": name, "email": email, "password": password})
            db.commit()
            session["user"] = name
            return redirect(url_for("userhome", user=name))
        else:
            return render_template("signup.html")
            

@app.route("/login", methods=['GET', 'POST'])
def login():
    # If user is already logged in
    if "user" in session:
        return redirect(url_for("userhome"))
    else:
        # If user submits credentials for logging in
        if request.method == "POST":
            name = request.form["name"]
            password = request.form["password"]
            theuser = db.execute("SELECT * FROM users WHERE username = :username", {"username": name}).fetchone()
            if theuser != None:
                if theuser.password == password:
                    session["user"] = name
                    return redirect(url_for("userhome", user=name))
                else:
                    flash('Invalid username or password')
                    return redirect(url_for("login"))      
            else: 
                flash("The account doesn't exist.")
                return redirect(url_for("login"))
        else:
            return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


# API route
@app.route("/api/<isbn>")
def books_api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid Book ISBN"}), 404

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "6kIZ5ttIXxHvb0h9DIIuCg", "isbns": isbn})
    data = res.json() 
    avgrating = data["books"][0]["average_rating"]
    rcount = data["books"][0]["work_ratings_count"]
    return  jsonify({
              "title": book.title,
              "author": book.author,
              "isbn": book.isbn,
              "year": book.year,
              "review_count": rcount,
              "average_score": avgrating
            })
    


