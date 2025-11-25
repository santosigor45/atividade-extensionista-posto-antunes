from flask import flash, redirect, url_for, request, render_template
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from flask_login import LoginManager
from models import User

login_manager = LoginManager()


# Function to load a user from the database using the user ID
@login_manager.user_loader
def get_user(user_id):
    return User.query.get(int(user_id))


# Handler for unauthorized access attempts
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('Você precisa estar logado para acessar esta página', 'error')
    return redirect(url_for('views.login'))


def login():
    # Check if the request method is POST for form submission
    if request.method == "POST":
        username = request.form["username"].lower().strip()
        password = request.form["password"]

        # Ensure username and password fields are filled
        if not username or not password:
            flash('Preencha os dados corretamente!', 'info')
            return redirect(url_for('views.login'))

        # Check if user exists in the database
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Usuário não encontrado!', 'info')
            return redirect(url_for('views.login'))

        # Validate the provided password
        if not check_password_hash(user.password, password):
            flash('Senha incorreta!', 'info')
            return redirect(url_for('views.login'))

        # Log in the user and redirect to the right page
        login_user(user, remember=True)

        if user.is_manager:
            return redirect(url_for('views.graficos'))
        return redirect(url_for('views.home'))

    # Redirect authenticated users directly to home
    if current_user.is_authenticated:
        return redirect(url_for("views.home"))
    else:
        # Show the login form to unauthenticated users
        return render_template("login.html")


def logout():
    logout_user()
    return redirect(url_for('views.login'))


def init_app(app):
    login_manager.init_app(app)
