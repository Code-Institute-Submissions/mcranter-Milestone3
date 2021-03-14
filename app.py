import os
import random
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_defs")
def get_defs():
    tasks = list(mongo.db.tasks.find())
    return render_template("home.html", tasks=tasks)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tasks = list(mongo.db.tasks.find({"$text": {"$search": query}}))
    return render_template("home.html", tasks=tasks)


@app.route("/random", methods=["GET", "POST"])
def randoms():
    # Get a single record using MongoDB's sample method
    task = list(mongo.db.tasks.aggregate([{'$sample': {'size': 1}}]))[0]
    return render_template("random.html", task=task)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into session cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful - Welcome Aboard!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure pswd matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # passwords don't match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username not found in db
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # gets session user username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    session.clear()
    flash("You're logged out, ye lubber")
    return redirect(url_for("login"))


@app.route("/add_word", methods=["GET", "POST"])
def add_word():
    if request.method == "POST":
        task = {
            "task_word": request.form.get("task_word"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "created_by": session["user"]
        }
        mongo.db.tasks.insert_one(task)
        flash("Word successfully Added!")
        return redirect(url_for("get_defs"))

    return render_template("add_word.html")


@app.route("/edit_word/<task_id>", methods=["GET", "POST"])
def edit_word(task_id):
    if request.method == "POST":
        submit = {
            "task_word": request.form.get("task_word"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "created_by": session["user"]
        }
        mongo.db.tasks.update({"_id": ObjectId(task_id)}, submit)
        flash("Word Successfully Edited!")
        return redirect(url_for("get_defs"))

    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_word.html", task=task, categories=categories)


@app.route("/delete_word/<task_id>")
def delete_word(task_id):
    mongo.db.tasks.remove({"_id": ObjectId(task_id)})
    flash("Word Deleted")
    return redirect(url_for("get_defs"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
