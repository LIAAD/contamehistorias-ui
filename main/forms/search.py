from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField
from flask import Blueprint

search_form = Blueprint('SearchForm', __name__)


class SearchForm(FlaskForm):
    query = StringField('Search', [])
    date_from = StringField('from', [])
    date_to = StringField('to', [])
    last_years = StringField('last_years', [])
    news_sources = StringField('news_sources', [])
    lang = HiddenField('lang', [], default="pt")
