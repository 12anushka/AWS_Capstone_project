from flask import Flask, render_template, request, redirect, session
from services.donor_service import add_donor, get_all_donors
from services.hospital_service import get_stock, is_critical
from services.alert_service import send_alert
from services.donor_service import add_donor, get_all_donors, get_donor_by_email
from services.donor_service import (
    add_donor,
    get_all_donors,
    add_activity,
    get_activities
)
from services.donor_service import add_activity, get_activities



# ---------------- AUTH MOCK ----------------
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


app = Flask(__name__)
app.secret_key = "bloodbridge_secret_key"


# ---------------- HOME ----------------
@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect("/login")
    return render_template("landing.html")


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
            "name": request.form["name"],
            "blood_group": request.form["blood_group"],
            "location": request.form["location"],
            "phone": request.form["phone"],
            "email": email
        }

        add_donor(donor_data)

        # ✅ ADD ACTIVITY HERE
        add_activity(email, "🩸 Donor profile registered / updated")

        return redirect("/donor")

    # ✅ FETCH ACTIVITY HERE
    activities = get_activities(email)

    return render_template(
        "donor.html",
        activities=activities
    )




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
            send_alert(bg)
            message = "🚨 Critical shortage! Emergency alert sent."
            level = "danger"
        else:
            message = "✅ Request recorded successfully."
            level = "success"

    return render_template(
        "hospital.html",
        stock=stock,
        message=message,
        level=level
    )
    add_activity(
    "donor@bloodbridge.com",
    f"🚨 Emergency request raised for {bg} ({units} units)"
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


if __name__ == "__main__":
    app.run(debug=True)
