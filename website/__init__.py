from flask import Flask

def create_web():
    web = Flask(__name__)
    web.config['SECRET_KEY'] = 'MINI_IT_02'

    from .views import views
    from .auth import auth

    web.register_blueprint(views, url_prefix='/')
    web.register_blueprint(auth, url_prefix='/')

    return web