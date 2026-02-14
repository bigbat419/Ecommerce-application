# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required
from extensions import mysql, login_manager
from MySQLdb.cursors import DictCursor
from utils import hash_password, verify_password
from flask_login import current_user

auth_bp = Blueprint("auth", __name__, template_folder="../templates")

# -----------------------------
# User class
# -----------------------------
class User(UserMixin):
    def __init__(self, id, name, email, is_admin=False):
        self.id = id
        self.name = name
        self.email = email
        self.is_admin = is_admin
        



# -----------------------------
# Load user (Flask-Login)
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT id, name, email, is_admin FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return User(row["id"], row["name"], row["email"], bool(row["is_admin"]))


# -----------------------------
# Register
# -----------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form.get("role", "user")
        role = role.lower() if isinstance(role, str) else "user"
        is_admin = 1 if role == "admin" else 0
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash("Email already registered", "warning")
            cur.close()
            return redirect(url_for("auth.register"))

        pw = hash_password(password)
        cur.execute(
            "INSERT INTO users (name, email, password, role, is_admin) VALUES (%s, %s, %s, %s, %s)",
            (name, email, pw, role, is_admin),
        )
        mysql.connection.commit()
        cur.close()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# -----------------------------
# Login
# -----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":    
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor(DictCursor)
        cur.execute(
            "SELECT id, name, email, password, is_admin FROM users WHERE email=%s",
            (email,),
        )
        user = cur.fetchone()
        cur.close()

        if not user or not verify_password(user["password"], password):
            flash("Invalid credentials", "danger")
            return redirect(url_for("auth.login"))

        user_obj = User(user["id"], user["name"], user["email"], bool(int(user["is_admin"])))
        login_user(user_obj)
        flash("Logged in successfully", "success")
        if int(user["is_admin"]) == 1:
            return redirect(url_for("admin.dashboard"))
        else:
            return redirect(url_for("admin.products"))

    return render_template("auth/login.html")


# -----------------------------
# Logout
# -----------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
