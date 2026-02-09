from flask import Flask, render_template, request, redirect, url_for
import os
import boto3
import uuid
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError

# ==========================
# FLASK APP
# ==========================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aws_secret_key")

# ==========================
# FILE UPLOAD CONFIG
# ==========================
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================
# AWS CONFIG (IAM ROLE)
# ==========================
REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)

# ==========================
# DYNAMODB TABLES
# ==========================
users_table = dynamodb.Table("Users")
donors_table = dynamodb.Table("Donors")
hospitals_table = dynamodb.Table("Hospitals")
blood_stock_table = dynamodb.Table("BloodStock")
emergency_requests_table = dynamodb.Table("EmergencyRequests")
donor_activity_table = dynamodb.Table("DonorActivity")

# ==========================
# ROUTES
# ==========================

@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    role = request.form.get("role", "donor")

    try:
        users_table.put_item(
            Item={
                "email": email,            # Partition Key
                "username": username,
                "role": role,
                "created_at": str(uuid.uuid4())
            }
        )
        return redirect(url_for("index"))

    except ClientError as e:
        return str(e)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file selected"

    file = request.files["file"]
    if file.filename == "":
        return "No file selected"

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return "File uploaded successfully"


@app.route("/add-blood-stock", methods=["POST"])
def add_blood_stock():
    blood_group = request.form["blood_group"]
    units = int(request.form["units"])

    try:
        blood_stock_table.put_item(
            Item={
                "blood_group": blood_group,     # Partition Key
                "units_available": units,
                "updated_at": str(uuid.uuid4())
            }
        )
        return "Blood stock updated"

    except ClientError as e:
        return str(e)


@app.route("/raise-request", methods=["POST"])
def raise_emergency_request():
    request_id = str(uuid.uuid4())

    try:
        emergency_requests_table.put_item(
            Item={
                "request_id": request_id,       # Partition Key
                "hospital_id": request.form["hospital_id"],
                "blood_group": request.form["blood_group"],
                "units": int(request.form["units"]),
                "priority": request.form["priority"],
                "status": "OPEN"
            }
        )
        return "Emergency request created"

    except ClientError as e:
        return str(e)


# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0")

