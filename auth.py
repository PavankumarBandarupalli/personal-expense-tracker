
import sqlite3

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app
)
from flask_login import UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


auth = Blueprint("auth", __name__)


class AuthUser(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = str(user_id)
        self.username = username
        self.email = email


def get_auth_connection():
    conn = sqlite3.connect(current_app.config["DB_FILE"])
    conn.row_factory = sqlite3.Row
    return conn


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 8:
            flash("Fill in all fields and use a password of at least 8 characters.")
            return redirect(url_for("auth.register"))

        try:
            with get_auth_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (username, email, generate_password_hash(password))
                )

            flash("Account created successfully. Please log in.")
            return redirect(url_for("auth.login"))

        except sqlite3.IntegrityError:
            flash("That username or email is already registered.")

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_auth_connection() as conn:
            user = conn.execute(
                """
                SELECT id, username, email, password_hash
                FROM users
                WHERE email = ?
                """,
                (email,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            login_user(
                AuthUser(user["id"], user["username"], user["email"])
            )
            return redirect(url_for("index"))

        flash("Invalid email or password.")

    return render_template("login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()

    return redirect(url_for("auth.login"))
