from flask import Blueprint, session, redirect, url_for


blueprint = Blueprint('pages', __name__)


@blueprint.route('/')
def home():
    if session['dataset'] == 'arquivopt':
        return redirect(url_for('pages_arquivopt.home'))
