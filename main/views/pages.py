from flask import Blueprint, session, redirect, url_for, request, current_app, g

from furl import furl


blueprint = Blueprint('pages', __name__)

LANGUAGES = ['en', 'pt']


@blueprint.url_defaults
def add_language_code(endpoint, values):
    if current_app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
        values['lang_code'] = session.get('lang_code', "pt")
        g.lang_code = session.get('lang_code', "pt")

    try:
        values.setdefault('lang_code', g.lang_code)
    except:
        values.setdefault('lang_code', session.get('lang_code', "pt"))


@blueprint.route('/change/<new_lang_code>')
def change(new_lang_code):

    if not(new_lang_code in LANGUAGES):
        new_lang_code = "pt"

    session['lang_code'] = new_lang_code

    # Redirect to same page with changed lang_code
    redirect_url = furl(request.referrer)
    redirect_url.args['lang_code'] = new_lang_code

    return redirect(redirect_url)


@blueprint.route('/')
def home():
    if session['dataset'] == 'arquivopt':
        return redirect(url_for('pages_arquivopt.home'))
    elif session['dataset'] == 'tls-covid19':
        return redirect(url_for('pages_tlscovid.home'))
