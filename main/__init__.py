import logging

from flask import Flask, g, session, request
from flask_talisman import Talisman
from flask_babel import Babel
from celery import Celery

from main.views import pages, pages_arquivopt, pages_tlscovid

from settings import config

babel = Babel()


class YourFlask(Flask):
    def create_jinja_environment(self):
        self.config['TEMPLATES_AUTO_RELOAD'] = True
        return Flask.create_jinja_environment(self)


def create_app(config_filename):

    app = YourFlask(__name__)
    app.url_map.strict_slashes = False

    app.config.from_object(config[config_filename])
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    app.logger.setLevel(logging.NOTSET)

    app.register_blueprint(pages.blueprint)
    app.register_blueprint(pages_arquivopt.blueprint, url_prefix='/arquivopt')
    # app.register_blueprint(pages_tlscovid.blueprint, url_prefix='/tls-covid19')

    # Talisman(app, content_security_policy={
    #     'style-src': [
    #         'https://fonts.googleapis.com',
    #         '\'unsafe-inline\'',
    #         '\'self\'',
    #     ]
    # })
    Talisman(app, content_security_policy={})

    babel.init_app(app)

    @app.after_request
    def log_response(resp):
        app.logger.info("{} {} {}\n{}".format(
            request.method, request.url, request.data, resp)
        )
        return resp

    # If someone navigates to the site domain without the lang code
    # we append the lang code to the request url and redirect
    @app.context_processor
    def inject_lang():
        print("---- inject_lang ----")
        print("session", session)
        print("session.keys()", session.keys())

        if(not 'lang' in session.keys() or session['lang'] == None or session['lang'] == "None"):
            return dict(sess_lang="pt")

        if not("lang" in session.keys()):
            return dict(sess_lang="pt")
        else:
            return dict(sess_lang=session['lang'])

    @babel.localeselector
    def get_locale():
        g.lang = session['lang']
        return g.get('lang', 'pt')

    return app


# https://stackoverflow.com/a/59672617
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'],
        include=['main.celery_tasks.app_tasks']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
