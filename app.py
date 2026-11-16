from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
)
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from ml_model import predict_health_risk

import os
import uuid
from datetime import datetime


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)
app.secret_key = "healthcare-secret-key-change-this"

MONGO_URI = "mongodb://127.0.0.1:27017/"
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["moon"]

users_collection = db["users"]
health_records_collection = db["health_records"]
health_predictions_collection = db["health_predictions"]

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

RECORD_TYPES = [
    "Medical Report",
    "Lab Report",
    "Diagnostic Report",
    "Doctor Visit",
    "Prescription",
    "Vaccination",
    "Other",
]


# =========================================================
# HELPERS
# =========================================================

def allowed_file(filename):
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_logged_in_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.clear()
        return None

    try:
        return users_collection.find_one({"_id": object_id})
    except Exception as exc:
        print("User lookup error:", exc)
        return None


def login_required():
    user = get_logged_in_user()
    if not user:
        session.clear()
        flash("Please login first.", "error")
        return None
    return user


def save_uploaded_file(file):
    """Save an uploaded document and return (original_name, stored_name)."""
    if not file or not file.filename:
        return "", ""

    if not allowed_file(file.filename):
        raise ValueError("Only PDF, JPG, JPEG and PNG files are allowed.")

    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{extension}"

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_name))
    return original_name, stored_name


def delete_stored_file(filename):
    if not filename:
        return
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as exc:
            print("File delete error:", exc)


def get_record_for_user(record_id, user):
    try:
        object_id = ObjectId(record_id)
    except Exception:
        return None

    try:
        return health_records_collection.find_one({
            "_id": object_id,
            "user_id": user["_id"],
        })
    except Exception as exc:
        print("Record lookup error:", exc)
        return None


# =========================================================
# MONGODB CONNECTION TEST
# =========================================================

try:
    client.admin.command("ping")
    print("MongoDB Connected Successfully!")
except Exception as exc:
    print("MongoDB Connection Failed:", exc)


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter email and password.", "error")
            return redirect(url_for("login"))

        try:
            user = users_collection.find_one({"email": email})
        except Exception as exc:
            print("Login MongoDB Error:", exc)
            flash("Database connection error. Please try again.", "error")
            return redirect(url_for("login"))

        if not user or not check_password_hash(user.get("password", ""), password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        session["user_id"] = str(user["_id"])
        session["user_name"] = user.get("name", "")
        session["user_email"] = user.get("email", "")

        flash("Welcome back!", "success")
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("Please fill all fields.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))

        try:
            if users_collection.find_one({"email": email}):
                flash("Email is already registered.", "error")
                return redirect(url_for("register"))

            users_collection.insert_one({
                "name": name,
                "email": email,
                "password": generate_password_hash(password),
            })

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        except DuplicateKeyError:
            flash("Email is already registered.", "error")
            return redirect(url_for("register"))
        except Exception as exc:
            print("Registration Error:", exc)
            flash("Something went wrong. Please try again.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    try:
        total_records = health_records_collection.count_documents({"user_id": user["_id"]})
        total_reports = health_records_collection.count_documents({
            "user_id": user["_id"],
            "record_type": {"$in": ["Medical Report", "Lab Report", "Diagnostic Report"]},
        })
        total_doctor_visits = health_records_collection.count_documents({
            "user_id": user["_id"],
            "record_type": "Doctor Visit",
        })
        total_documents = health_records_collection.count_documents({
            "user_id": user["_id"],
            "stored_filename": {"$exists": True, "$ne": ""},
        })
    except Exception as exc:
        print("Dashboard database error:", exc)
        total_records = total_reports = total_doctor_visits = total_documents = 0

    return render_template(
        "dashboard.html",
        user=user,
        total_records=total_records,
        total_reports=total_reports,
        total_doctor_visits=total_doctor_visits,
        total_documents=total_documents,
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name or not email:
            flash("Name and email cannot be empty.", "error")
            return redirect(url_for("profile"))

        try:
            existing = users_collection.find_one({
                "email": email,
                "_id": {"$ne": user["_id"]},
            })
            if existing:
                flash("This email is already registered.", "error")
                return redirect(url_for("profile"))

            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"name": name, "email": email}},
            )

            session["user_name"] = name
            session["user_email"] = email
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))
        except Exception as exc:
            print("Profile update error:", exc)
            flash("Unable to update profile right now.", "error")
            return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/profile/change-password", methods=["POST"])
def change_password():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        flash("Please fill all password fields.", "error")
        return redirect(url_for("profile"))

    if not check_password_hash(user.get("password", ""), current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("profile"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("profile"))

    if new_password == current_password:
        flash("New password must be different from the current password.", "error")
        return redirect(url_for("profile"))

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": generate_password_hash(new_password)}},
    )

    flash("Password changed successfully.", "success")
    return redirect(url_for("profile"))


# =========================================================
# HEALTH RECORDS
# =========================================================

@app.route("/health-records")
def health_records():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    try:
        records = list(
            health_records_collection.find({"user_id": user["_id"]})
            .sort("record_date", -1)
        )
    except Exception as exc:
        print("Health records error:", exc)
        records = []
        flash("Unable to load health records.", "error")

    document_count = sum(1 for record in records if record.get("stored_filename"))

    return render_template(
        "health_records.html",
        user=user,
        records=records,
        document_count=document_count,
    )


@app.route("/health-records/add", methods=["GET", "POST"])
def add_health_record():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        record_type = request.form.get("record_type", "").strip()
        record_date = request.form.get("record_date", "").strip()
        doctor = request.form.get("doctor", "").strip()
        hospital = request.form.get("hospital", "").strip()
        notes = request.form.get("notes", "").strip()

        if not record_type or not record_date:
            flash("Record type and date are required.", "error")
            return redirect(url_for("add_health_record"))

        if record_type not in RECORD_TYPES:
            flash("Please select a valid record type.", "error")
            return redirect(url_for("add_health_record"))

        document_name = ""
        stored_filename = ""

        try:
            document_name, stored_filename = save_uploaded_file(request.files.get("document"))

            health_records_collection.insert_one({
                "user_id": user["_id"],
                "record_type": record_type,
                "record_date": record_date,
                "doctor": doctor,
                "hospital": hospital,
                "notes": notes,
                "document_name": document_name,
                "stored_filename": stored_filename,
            })

            flash("Health record added successfully.", "success")
            return redirect(url_for("health_records"))
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("add_health_record"))
        except Exception as exc:
            if stored_filename:
                delete_stored_file(stored_filename)
            print("Add health record error:", exc)
            flash("Unable to save the health record.", "error")
            return redirect(url_for("add_health_record"))

    return render_template(
        "add_health_record.html",
        user=user,
        record_types=RECORD_TYPES,
    )


@app.route("/health-records/view/<record_id>")
def view_health_record(record_id):
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    record = get_record_for_user(record_id, user)
    if not record:
        flash("Health record not found.", "error")
        return redirect(url_for("health_records"))

    return render_template("view_health_records.html", user=user, record=record)


@app.route("/health-records/edit/<record_id>", methods=["GET", "POST"])
def edit_health_record(record_id):
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    record = get_record_for_user(record_id, user)
    if not record:
        flash("Health record not found.", "error")
        return redirect(url_for("health_records"))

    if request.method == "POST":
        record_type = request.form.get("record_type", "").strip()
        record_date = request.form.get("record_date", "").strip()
        doctor = request.form.get("doctor", "").strip()
        hospital = request.form.get("hospital", "").strip()
        notes = request.form.get("notes", "").strip()

        if not record_type or not record_date:
            flash("Record type and date are required.", "error")
            return redirect(url_for("edit_health_record", record_id=record_id))

        if record_type not in RECORD_TYPES:
            flash("Please select a valid record type.", "error")
            return redirect(url_for("edit_health_record", record_id=record_id))

        update_data = {
            "record_type": record_type,
            "record_date": record_date,
            "doctor": doctor,
            "hospital": hospital,
            "notes": notes,
        }

        new_stored_filename = ""

        try:
            uploaded = request.files.get("document")
            if uploaded and uploaded.filename:
                new_document_name, new_stored_filename = save_uploaded_file(uploaded)
                update_data["document_name"] = new_document_name
                update_data["stored_filename"] = new_stored_filename

            health_records_collection.update_one(
                {"_id": record["_id"], "user_id": user["_id"]},
                {"$set": update_data},
            )

            if new_stored_filename:
                delete_stored_file(record.get("stored_filename", ""))

            flash("Health record updated successfully.", "success")
            return redirect(url_for("health_records"))
        except ValueError as exc:
            if new_stored_filename:
                delete_stored_file(new_stored_filename)
            flash(str(exc), "error")
            return redirect(url_for("edit_health_record", record_id=record_id))
        except Exception as exc:
            if new_stored_filename:
                delete_stored_file(new_stored_filename)
            print("Edit health record error:", exc)
            flash("Unable to update the health record.", "error")
            return redirect(url_for("edit_health_record", record_id=record_id))

    return render_template(
        "edit_health_record.html",
        user=user,
        record=record,
        record_types=RECORD_TYPES,
    )


@app.route("/health-records/delete/<record_id>", methods=["POST"])
def delete_health_record(record_id):
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    record = get_record_for_user(record_id, user)
    if not record:
        flash("Health record not found.", "error")
        return redirect(url_for("health_records"))

    try:
        health_records_collection.delete_one({
            "_id": record["_id"],
            "user_id": user["_id"],
        })
        delete_stored_file(record.get("stored_filename", ""))
        flash("Health record deleted successfully.", "success")
    except Exception as exc:
        print("Delete health record error:", exc)
        flash("Unable to delete the health record.", "error")

    return redirect(url_for("health_records"))


# =========================================================
# DOCUMENT VIEW / DOWNLOAD
# =========================================================

@app.route("/health-records/document/<record_id>")
def health_record_document(record_id):
    """Open a document using the record ID.

    This intentionally accepts record_id because the templates pass record_id.
    It fixes the old BuildError where the endpoint expected filename.
    """
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    record = get_record_for_user(record_id, user)
    if not record or not record.get("stored_filename"):
        flash("Document not found for this health record.", "error")
        return redirect(url_for("health_records"))

    filename = record["stored_filename"]
    full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(full_path):
        flash("The saved document file is missing.", "error")
        return redirect(url_for("health_records"))

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    try:
        records = list(
            health_records_collection.find({"user_id": user["_id"]})
            .sort("record_date", -1)
        )
    except Exception as exc:
        print("Reports error:", exc)
        records = []
        flash("Unable to load reports.", "error")

    counts = {record_type: 0 for record_type in RECORD_TYPES}
    for record in records:
        record_type = record.get("record_type")
        if record_type in counts:
            counts[record_type] += 1

    return render_template(
        "reports.html",
        user=user,
        records=records,
        total_records=len(records),
        prescriptions=counts["Prescription"],
        lab_reports=counts["Lab Report"],
        medical_reports=counts["Medical Report"],
        doctor_visits=counts["Doctor Visit"],
        diagnostic_reports=counts["Diagnostic Report"],
        vaccination_records=counts["Vaccination"],
    )



# =========================================================
# MACHINE LEARNING: HEALTH RISK PREDICTION
# =========================================================

@app.route("/health-risk-prediction", methods=["GET", "POST"])
def health_risk_prediction():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    form_data = {
        "age": "",
        "bmi": "",
        "systolic_bp": "",
        "glucose": "",
        "exercise_days": "3",
        "smoking": "0",
    }
    result = None

    if request.method == "POST":
        form_data = {
            "age": request.form.get("age", "").strip(),
            "bmi": request.form.get("bmi", "").strip(),
            "systolic_bp": request.form.get("systolic_bp", "").strip(),
            "glucose": request.form.get("glucose", "").strip(),
            "exercise_days": request.form.get("exercise_days", "").strip(),
            "smoking": request.form.get("smoking", "").strip(),
        }

        try:
            if any(value == "" for value in form_data.values()):
                raise ValueError("Please fill in all fields.")

            age = int(form_data["age"])
            bmi = float(form_data["bmi"])
            systolic_bp = int(form_data["systolic_bp"])
            glucose = int(form_data["glucose"])
            exercise_days = int(form_data["exercise_days"])
            smoking = int(form_data["smoking"])

            result = predict_health_risk(
                age=age,
                bmi=bmi,
                systolic_bp=systolic_bp,
                glucose=glucose,
                exercise_days=exercise_days,
                smoking=smoking,
            )

            # Save a copy of the demonstration prediction for the logged-in user.
            try:
                health_predictions_collection.insert_one({
                    "user_id": user["_id"],
                    "age": age,
                    "bmi": bmi,
                    "systolic_bp": systolic_bp,
                    "glucose": glucose,
                    "exercise_days": exercise_days,
                    "smoking": smoking,
                    "risk": result["risk"],
                    "confidence": result["confidence"],
                    "model_accuracy": result["model_accuracy"],
                    "created_at": datetime.utcnow(),
                })
            except Exception as exc:
                print("Prediction history save error:", exc)
                flash("Prediction calculated, but its history could not be saved.", "warning")

        except (ValueError, TypeError) as exc:
            flash(str(exc) or "Please enter valid values.", "error")

    try:
        prediction_history = list(
            health_predictions_collection.find({"user_id": user["_id"]})
            .sort("created_at", -1)
            .limit(5)
        )
    except Exception as exc:
        print("Prediction history load error:", exc)
        prediction_history = []

    return render_template(
        "health_risk_prediction.html",
        user=user,
        form_data=form_data,
        result=result,
        prediction_history=prediction_history,
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
def settings():
    user = login_required()
    if not user:
        return redirect(url_for("login"))

    return render_template("settings.html", user=user)


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
