from flask_wtf import FlaskForm
from wtforms import TextField, HiddenField
from flask import Blueprint

search_form = Blueprint('SearchForm', __name__)

class SearchForm(FlaskForm):
    query = TextField('Search', [])
    date_from = TextField('from', [])
    date_to = TextField('to', [])
    last_years = TextField('last_years', [])
    news_sources = TextField('news_sources', [])
    lang_code = HiddenField('lang_code',[],default="pt")
