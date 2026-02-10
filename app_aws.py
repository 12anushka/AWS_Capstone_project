from flask import Flask, render_template, request, redirect, session, url_for
import boto3
import uuid
import os
from botocore.exceptions import ClientError

# =========================
# FLASK CONFIG
# =========================
app = Flask(__name__)
app.secret_key = "simplekey"

# =========================
# AWS CONFIG
# =========================
REGION = "us-east-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

# =========================
# TABLES (Must Exist in AWS)
# =========================
users_table = dynamodb.Table("Users")
donors_table = dynamodb.Table("Donors")
activity_table = dynamodb.Table("Activities")
stock_table = dynamodb.Table("BloodStock")

# =========================
# DEMO AUTH (Same as Local)
# =========================
def authenticate_user(email, password, role):

    demo_users = {
        "admin": {"email": "admin@bloodbridge.com", "password": "admin123"},
        "hospital": {"email": "hospital@bloodbridge.com", "password": "hospital123"},
        "donor": {"email": "donor@bloodbridge.com", "password": "donor123"},
    }

    user = demo_users.get(role)

    if user and user["email"] == email and user["password"] == password:
        return user

    return None


# =========================
# HELPERS
# =========================
def get_stock():

    items = stock_table.scan().get("Items", [])

    stock = {}

    for i in items:
        stock[i["blood_group"]] = int(i["units"])

    return stock


def add_activity(email, message):

    activity_table.put_item(
        Item={
            "id": str(uuid.uuid4()),
            "email": email,
            "message": message
        }
    )


def get_activities(email):

    res = activity_table.scan()

    return [
        a for a in res.get("Items", [])
        if a["email"] == email
    ]


def add_donor(data):

    donors_table.put_item(Item=data)


def get_all_donors():

    return donors_table.scan().get("Items", [])


def is_critical(bg, units):

    stock = get_stock()

    return stock.get(bg, 0) < units


# =========================
# ROUTES
# =========================

@app.route("/")
def home():

    if not session.get("logged_in"):
        return redirect("/login")

    return render_template("landing.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if not session.get("logged_in"):
        return redirect("/login")

    return render_template("dashboard.html", stock=get_stock())


# ---------------- DONOR ----------------
@app.route("/donor", methods=["GET", "POST"])
def donor():

    if not session.get("logged_in"):
        return redirect("/login")

    email = session.get("email")

    if request.method == "POST":

        donor_data = {
            "email": email,
            "name": request.form["name"],
            "blood_group": request.form["blood_group"],
            "location": request.form["location"],
            "phone": request.form["phone"]
        }

        add_donor(donor_data)

        add_activity(email, "🩸 Donor profile updated")

        return redirect("/donor")

    activities = get_activities(email)

    return render_template("donor.html", activities=activities)


# ---------------- HOSPITAL ----------------
@app.route("/hospital", methods=["GET", "POST"])
def hospital():

    if not session.get("logged_in"):
        return redirect("/login")

    stock = get_stock()
    message = None
    level = None

    if request.method == "POST":

        bg = request.form["blood_group"]
        units = int(request.form["units"])
        priority = request.form["priority"]

        if is_critical(bg, units):

            message = "🚨 Critical shortage! Emergency alert sent."
            level = "danger"

        else:

            message = "✅ Request recorded."
            level = "success"

        add_activity(
            session["email"],
            f"🚨 Emergency request for {bg} ({units})"
        )

    return render_template(
        "hospital.html",
        stock=stock,
        message=message,
        level=level
    )


# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():

    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect("/login")

    return render_template("admin.html", donors=get_all_donors())


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        user = authenticate_user(email, password, role)

        if user:

            session["logged_in"] = True
            session["role"] = role
            session["email"] = email

            if role == "admin":
                return redirect("/admin")

            elif role == "hospital":
                return redirect("/hospital")

            else:
                return redirect("/donor")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        return redirect("/login")

    return render_template("signup.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")


# =========================
# RUN
# =========================
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
