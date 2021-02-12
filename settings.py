import os
import inspect


class Config(object):

    ADMINS = ['arianpasquali', 'alexandreribeiro']
    APPNAME = 'contamehistorias'
    SUPPORT_EMAIL = 'contamehistorias@googlegroups.com'
    VERSION = '1.0.0'

    if os.environ.get('SECRET_KEY'):
        SECRET_KEY = os.environ.get('SECRET_KEY')
    else:
        SECRET_KEY = 'SECRET_KEY_ENV_VAR_NOT_SET'
        print('SECRET KEY ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION')


    STATIC_FOLDER = os.path.dirname(os.path.abspath(inspect.stack()[0][1])) + '/main/static'
    BABEL_DEFAULT_LOCALE = "pt"


class DevelopmentConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    FLASK_ENV = 'testing'
    DEBUG = False
    TESTING = True


class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig(),
    'testing': TestingConfig(),
    'production': ProductionConfig(),
    'default': DevelopmentConfig()
}
