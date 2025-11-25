import os

try:
    from dotenv import load_dotenv, find_dotenv
    if os.getenv('FLASK_ENV') == 'development':
        load_dotenv(find_dotenv(), override=False)
except ImportError:
    pass


# carrega variaveis de ambiente
def init_app(app):
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    app.config['PERMANENT_SESSION_LIFETIME'] = int(
        os.environ.get('PERMANENT_SESSION_LIFETIME', 86400)
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('MYSQL_URL')

