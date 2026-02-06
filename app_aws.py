from flask import Flask, render_template, request, redirect, url_for, session
import os
import boto3
import uuid
from werkzeug.utils import secure_filename
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aws_secret_key")

# ==========================
# FILE UPLOAD CONFIG
# ==========================
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================
# AWS CONFIG (IAM ROLE)
# ==========================
REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

users_table = dynamodb.Table("Users")
admin_users_table = dynamodb.Table("AdminUsers")
projects_table = dynamodb.Table("Projects")
enrollments_table = dynamodb.Table("Enrollments")

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:ACCOUNT_ID:BloodBridgeTopic"

# ==========================
# ROUTES
# ==========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]

    try:
        users_table.put_item(
            Item={
                "user_id": str(uuid.uuid4()),
                "username": username,
                "email": email
            }
        )

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"New user registered: {username}",
            Subject="BloodBridge Registration"
        )

        return redirect(url_for("index"))

    except ClientError as e:
        return str(e)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return "File uploaded successfully"
def check_blood_alert(blood_group, units):
    if units <= 5:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="🚨 Blood Shortage Alert",
            Message=(
                f"URGENT ALERT!\n\n"
                f"Blood Group: {blood_group}\n"
                f"Available Units: {units}\n\n"
                f"Immediate donor action required."
            )
        )

# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
