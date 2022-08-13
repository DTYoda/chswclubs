from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from datetime import datetime

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'CHSWClubs@gmail.com'
app.config['MAIL_PASSWORD'] = 'nbyybjtmfgagjcol'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

Session(app)

db = SQL("sqlite:///app.db")

@app.route("/")
@login_required
def index():
    name = db.execute("SELECT name FROM users WHERE id = ?", session["user_id"])[0]["name"]
    return render_template("index.html", name=name)

@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        if not request.form.get("name"):
            return render_template("login.html", error=True, errorMessage="Please enter a name")

        if not request.form.get("password"):
            return render_template("login.html", error=True, errorMessage="Please enter a password")

        user = db.execute("SELECT * FROM users WHERE name like ?", request.form.get("name"))

        if len(user) != 1 or not check_password_hash(user[0]["hash"], request.form.get("password")):
            return render_template("login.html", error=True, errorMessage="Incorrect name and/or password")

        if user[0]["verified"] == False:
            return render_template("login.html", error=True, errorMessage="Please verify email")

        session["user_id"] = user[0]["id"]

        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        if not request.form.get("name"):
            return render_template("register.html", error=True, errorMessage = "Please enter your name")

        if not request.form.get("grad"):
            return render_template("register.html", error=True, errorMessage = "Please enter your graduation year")

        if not request.form.get("email") or "@cpsed.net" not in request.form.get("email"):
            return render_template("register.html", error=True, errorMessage = "Please enter a valid cpsed.net email or email support for help")

        if not request.form.get("password"):
            return render_template("register.html", error=True, errorMessage = "Please enter a password")

        if not request.form.get("confirmation"):
            return render_template("register.html", error=True, errorMessage = "Please confirm your password")

        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", error=True, errorMessage = "Passwords do not match")

        if len(db.execute("SELECT * FROM users WHERE name like ?", request.form.get("name"))) != 0:
            return render_template("register.html", error=True, errorMessage="Name in use. Enter middle initial")

        if len(db.execute("SELECT * FROM users WHERE email like ?", request.form.get("email"))) != 0:
            return render_template("register.html", error=True, errorMessage="email in use. Contact support for help")

        try:
            if int(request.form.get("grad")) > 2030 or int(request.form.get("grad")) < 2020:
                return render_template("register.html", error=True, errorMessage = "Please enter a valid graduation year")
        except:
            return render_template("register.html", error=True, errorMessage = "Please enter a valid graduation year")

        db.execute("INSERT INTO users (name, hash, gradyear, email, verified) VALUES(?, ?, ?, ?, ?)", request.form.get("name"), generate_password_hash(request.form.get("password")), request.form.get("grad"), request.form.get("email"), False)
        msg = Message('Thank you for signing up! Please verify your email!', sender =   'CHSWClubs@gmail.com', recipients = [request.form.get("email")])
        msg.body = "Hello, " + request.form.get("name") + ", thank you for signing up for CHSW Clubs! We are glad to have you on board! Please verify your email with the following link. Did you not sign up for this website? Ignore! " + request.url + "/verify?h=" + generate_password_hash(request.form.get("email")) + "&id=" + str(db.execute("SELECT id FROM users WHERE name = ?", request.form.get("name"))[0]["id"])
        mail.send(msg)
        return redirect("/register")

    else:
        return render_template("register.html")

@app.route("/myclubs", methods=["POST", "GET"])
@login_required
def myclubs():

    clubs = db.execute("SELECT * FROM clubs WHERE club_id in (SELECT club_id FROM joined_clubs WHERE user_id = ?)", session["user_id"])

    for club in clubs:
        club["owner"] = db.execute("SELECT name FROM users WHERE id = ?", club["owner_id"])[0]["name"]
        club["date"] = db.execute("SELECT date FROM joined_clubs WHERE club_id = ? and user_id = ?", club["club_id"], session["user_id"])[0]["date"]

    return render_template("myclubs.html", clubs=clubs)

@app.route("/searchclubs")
@login_required
def searchclubs():
    return render_template("searchclubs.html")

@app.route("/searchclubs/search")
@login_required
def search():
    q = request.args.get("q")
    if q:
        clubs = db.execute("SELECT * FROM clubs WHERE name like ?", "%" + q + "%")
    else:
        clubs = []

    return jsonify(clubs)

@app.route("/createclub", methods=["POST", "GET"])
@login_required
def createclub():
    if request.method == "POST":
        clubInfo = {}
        clubInfo["name"] = request.form.get("name")
        if not clubInfo["name"]:
            return render_template("createclub.html", error=True, errorMessage = "Please fill out all fields")

        clubInfo["desc"] = request.form.get("desc")
        if not clubInfo["desc"]:
            return render_template("createclub.html", error=True, errorMessage = "Please fill out all fields")

        clubInfo["longDesc"] = request.form.get("longDesc")
        if not clubInfo["longDesc"]:
            return render_template("createclub.html", error=True, errorMessage = "Please fill out all fields")

        clubInfo["subject"] = request.form.get("subject")
        if not clubInfo["subject"]:
            return render_template("createclub.html", error=True, errorMessage = "Please fill out all fields")

        clubInfo["sun"] = request.form.get("sun")
        if not clubInfo["sun"]:
            clubInfo["sun"] = "None!"
        clubInfo["mon"] = request.form.get("mon")
        if not clubInfo["mon"]:
            clubInfo["mon"] = "None!"
        clubInfo["tue"] = request.form.get("tue")
        if not clubInfo["tue"]:
            clubInfo["tue"] = "None!"
        clubInfo["wed"] = request.form.get("wed")
        if not clubInfo["wed"]:
            clubInfo["wed"] = "None!"
        clubInfo["thu"] = request.form.get("thu")
        if not clubInfo["thu"]:
            clubInfo["thu"] = "None!"
        clubInfo["fri"] = request.form.get("fri")
        if not clubInfo["fri"]:
            clubInfo["fri"] = "None!"
        clubInfo["sat"] = request.form.get("sat")
        if not clubInfo["sat"]:
            clubInfo["sat"] = "None!"

        clubInfo["teacher"] = request.form.get("teacher")
        if not clubInfo["teacher"]:
            return render_template("createclub.html", error=True, errorMessage = "Please fill out all fields")

        clubInfo["clubIcon"] = request.form.get("clubIcon")

        clubInfo["clubRoom"] = request.form.get("clubRoom")
        if not clubInfo["clubRoom"]:
            return render_template("createclub.html", error=True, errorMessage = "Please fill out all fields")

        clubInfo["owner_id"] = session["user_id"]

        db.execute("INSERT INTO clubs (name, owner_id, subject, desc) VALUES(?, ?, ?, ?)", clubInfo["name"], session["user_id"], clubInfo["subject"], clubInfo["desc"])

        for info in clubInfo:
            db.execute("UPDATE clubs SET ? = ? WHERE name = ?", info, clubInfo[info], clubInfo["name"])

        db.execute("INSERT INTO joined_clubs (club_id, user_id, date) VALUES(?, ?, ?)", db.execute("SELECT club_id FROM clubs WHERE name = ?", clubInfo["name"])[0]["club_id"], session["user_id"], str(datetime.now().month) + "/" + str(datetime.now().day) + "/" + str(datetime.now().year))
        return redirect("/myclubs")

    else:
        return render_template("createclub.html")

@app.route("/clubs", methods=["GET", "POST"])
@login_required
def clubPage():
    joined = False
    clubName = request.args.get("name")
    if not clubName:
        return render_template("searchclubs.html")

    club = db.execute("SELECT * FROM clubs WHERE name = ?", clubName)[0]
    if not club:
        return render_template("searchclubs.html")

    club["owner"] = db.execute("SELECT name FROM users WHERE id = ?", club["owner_id"])[0]["name"]

    if db.execute("SELECT * FROM joined_clubs WHERE user_id = ? and club_id = ?", session["user_id"], club["club_id"]):
        joined = True
    return render_template("clubPage.html", club=club, joined=joined)

@app.route("/clubs/messages", methods=["GET", "POST"])
@login_required
def messages():
    clubName = request.args.get("name")
    if clubName:
        club = db.execute("SELECT * FROM clubs WHERE name = ?", clubName)[0]
        if request.method == "POST":
            message = request.form.get("message")
            if message:
                db.execute("INSERT INTO chat_messages (user_id, club_id, date, message, time) VALUES(?, ?, ?, ?, ?)", session["user_id"], club["club_id"], str(datetime.now().month) + "/" + str(datetime.now().day) + "/" + str(datetime.now().year), message, str(datetime.now().hour) + ":" + str(datetime.now().minute))
                return redirect("/clubs?name=" + clubName)
        else:
            messages = db.execute("SELECT * FROM chat_messages WHERE club_id = ? ORDER BY message_id DESC LIMIT 10", club["club_id"])
            messages.reverse()
            for message in messages:
                message["sender"] = db.execute("SELECT name FROM users WHERE id = ?", message["user_id"])[0]["name"]
            return jsonify(messages)
    return redirect("/searchclubs")

@app.route("/register/verify")
def verify():
    if request.method == "GET":
        h = request.args.get("h")
        if not h:
            return redirect("/")
        id = request.args.get("id")
        if not id:
            return redirect("/")

        email = db.execute("SELECT email FROM users WHERE id = ?", id)
        if not email:
            return redirect("/")

        if check_password_hash(h, email[0]["email"]):
            db.execute("UPDATE users SET verified = true WHERE id = ?", id)
        return redirect("/")
