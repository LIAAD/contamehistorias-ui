# -*- coding:utf-8 -*-
import os
import locale
import logging

from flask import render_template

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from werkzeug.serving import WSGIRequestHandler

from main import create_app, make_celery

locale.setlocale(locale.LC_TIME, 'pt_PT.utf8')

# Create and config Flask app
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Create and config Celery
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)
app.celery = celery

sentry_sdk.init(
    dsn="https://b71a8736242e4d07ac3c4d5e4bc665ff@o519487.ingest.sentry.io/5630277",
    integrations=[FlaskIntegration(), RedisIntegration()],
    traces_sample_rate=1.0
)

WSGIRequestHandler.protocol_version = "HTTP/1.1"

@app.context_processor
def add_session_config():
    """Add current_app.permanent_session_lifetime converted to milliseconds
    to context. The config variable PERMANENT_SESSION_LIFETIME is not
    used because it could be either a timedelta object or an integer
    representing seconds.
    """
    return {
        'PERMANENT_SESSION_LIFETIME_MS': (
            app.permanent_session_lifetime.seconds * 60000),
}

@app.errorhandler(404)
def page_not_found(error):
   app.logger.error('Page not found:')
   return render_template('pages/errors/404.html'), 404

#@app.errorhandler(500)
#def page_internal_server_error(error):
#   app.logger.error('Internal server error:')
#   return render_template('pages/errors/500.html'), 500

@app.errorhandler(Exception)
def page_globalerror(error):
   #app.logger.error('Global error handler:')
   if  app.config['DEBUG']:
       app.logger.error(error, exc_info=True)
   else:
       raise error
   
   return render_template('pages/errors/500.html'), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5000")
    # app.run(host="0.0.0.0", port="5000", ssl_context='adhoc')
