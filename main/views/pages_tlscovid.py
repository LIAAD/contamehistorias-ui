# -*- coding:utf-8 -*-
import locale

from flask import render_template, Blueprint, request, jsonify
from flask import redirect, url_for, g, current_app, session

import requests

from furl import furl

from main.forms.search import SearchForm

blueprint = Blueprint('pages_tlscovid', __name__)


LANGUAGES = ['en', 'pt']

API_TLSCOVID_ENDPOINT = 'http://localhost:5001/api/tlscovid/'


@blueprint.before_request
def before_request():
    session['dataset'] = 'tls-covid19'
    print("------before_request----")
    print("request", request)
    print("request.full_path", request.full_path)
    print("session.keys", session.keys())


@blueprint.url_defaults
def add_language_code(endpoint, values):
    if current_app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
        values['lang_code'] = session.get('lang_code', "pt")
        g.lang_code = session.get('lang_code', "pt")

    try:
        values.setdefault('lang_code', g.lang_code)
    except:
        values.setdefault('lang_code', session.get('lang_code', "pt"))


@blueprint.url_value_preprocessor
def pull_lang_code(endpoint, values):
    lang_code = request.args.get('lang_code')
    session['lang_code'] = lang_code
    g.lang_code = session.get('lang_code', "pt")


################
#### Routes ####
################

#####################################################################################
# Celery stuff to handle long task (execute engine)
# https://blog.miguelgrinberg.com/post/using-celery-with-flask
#####################################################################################
@blueprint.route('/searching', methods=['GET'])
def searching():
    
    query = request.args.get('query', type=str)
    index = request.args.get('index', default='pt', type=str)

    return render_template('pages/tlscovid/searching.html', query=query, index=index)


@blueprint.route('/longtask', methods=['GET'])
def long_task():

    query = request.args.get('query', type=str)
    index = request.args.get('index', default='pt', type=str)

    task_id = current_app.celery.send_task(
        'celery_tasks.execute_engine_tlscovid', args=[query, index])

    return jsonify({}), 202, {'Location': url_for('pages_tlscovid.task_status',
                                                  task_id=task_id)}


@blueprint.route('/status/<task_id>')
def task_status(task_id):

    task = current_app.celery.AsyncResult(task_id)

    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': task.info['status']
        }
        if 'result' in task.info:
            response['task_id'] = task_id
            response['result'] = task.info['result']
            response['url_for'] = url_for(
                'pages_tlscovid.search', query=task.info['query'], index=task.info['index'])
    else:
        # something went wrong in the background job
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': str(task.info)  # this is the exception raised
        }
    return jsonify(response)
#####################################################################################


@blueprint.route('/')
def home():

    form = SearchForm(request.form)

    lang_code = session.get("lang_code", "pt")

    if(lang_code == None):
        lang_code = "pt"

    r = requests.get(API_TLSCOVID_ENDPOINT + 'get-examples')
    examples = r.json()

    stories_examples = {
        "topics_pt": examples['pt'],
        "topics_en": examples['en'],
    }

    return render_template('pages/tlscovid/home.html', stories_examples=stories_examples, form=form, lang_code=lang_code)


@blueprint.route('/team')
def team():
    return render_template('pages/common/team.html')


@blueprint.route('/press')
def press():
    return render_template('pages/common/press.html')


@blueprint.route('/about')
def about():
    return render_template('pages/common/about.html')


@blueprint.route('/change/<new_lang_code>')
def change(new_lang_code):

    if not(new_lang_code in LANGUAGES):
        new_lang_code = "pt"

    session['lang_code'] = new_lang_code

    # Redirect to same page with changed lang_code
    redirect_url = furl(request.referrer)
    redirect_url.args['lang_code'] = new_lang_code

    return redirect(redirect_url)


@blueprint.route('/search', methods=['GET'])
def search():

    # Default parameters
    hasNarrative = False
    index = 'pt'
    source_name = None

    # Lang Code
    lang_code = session.get("lang_code", "pt")
    if(lang_code == None):
        lang_code = "pt"
    try:
        if(lang_code == "pt"):
            locale.setlocale(locale.LC_TIME, 'pt_PT.utf8')
        else:
            locale.setlocale(locale.LC_TIME, 'en_US.utf8')
    except:
        print("No time locale")

    # Form data
    form = SearchForm(request.form)

    fquery = request.args.get('query', type=str)
    form.query.data = fquery

    if 'form_index' in request.args:
        index = request.args.get('form_index', type=str)
    else:
        index = request.args.get('index', default='pt', type=str)

    print('Query:', fquery)
    print('Index:', index)
    print('Lang code:', lang_code)

    # Task already processed
    if 'id' in request.args:

        task_id = request.args.get('id')
        task = current_app.celery.AsyncResult(task_id)

        # Check if task exists
        try:
            result = task.info['result']
        except TypeError:
            print('Invalid task')
            return render_template('pages/tlscovid/search.html', lang_code=lang_code, form=SearchForm(), related_terms=[], result=None, user_query=None, hasNarrative=hasNarrative)
        
        if not result:
            print('Invalid result')
            return render_template('pages/tlscovid/search.html', lang_code=lang_code, form=form, related_terms=[], result=None, user_query=fquery, hasNarrative=hasNarrative)

        else:
            print('Result ok')

            result["stats"]["time"] = float(result["stats"]["time"])

            result_header = {
                "query": result["query"],
                "status": result["status"],

                "time_total": result["stats"]["time"],

                "ndocs": result["stats"]["n_docs"],
                "nunique_docs": result["stats"]["n_unique_docs"],
                "ndomains": result["stats"]["n_domains"],
                "index": index
            }

            domains = result["domains"]

            if(result["status"] != "OK"):
                return render_template('pages/tlscovid/search.html', lang_code=lang_code, form=form, related_terms=[], result=None, result_header=result_header, hasNarrative=hasNarrative)

            if(int(result["stats"]["n_unique_docs"]) == 0):
                return render_template('pages/tlscovid/search.html', lang_code=lang_code, form=form, related_terms=[], result=None, result_header=result_header, hasNarrative=hasNarrative)

            # Call API to get events and end_intervals_dates
            r = requests.get(API_TLSCOVID_ENDPOINT +
                             'get-events', json=result)
            get_events_result = r.json()

            res_events = get_events_result['res_events']
            end_intervals_dates = get_events_result['end_intervals_dates']

            # Call API to get titles
            r = requests.get(API_TLSCOVID_ENDPOINT +
                             'get-titles', json=res_events)
            all_titles = r.json()

            # verifica se tem mais do que um intervalo e se possui noticias
            print("---------------------------------------")
            print("Check if there is more than one interval and if there are news")
            print("Number of news to present:", len(all_titles))
            print("Number of intervals:", len(res_events))

            if(len(all_titles) > 0 and len(res_events) >= 2):
                hasNarrative = True

            # Call API to get related entities and terms
            payload = {
                'all_titles': all_titles,
                'query_term_corr': result['query_term_corr']
            }
            r = requests.get(API_TLSCOVID_ENDPOINT +
                             'get-entities-terms', json=payload)
            get_entities_terms_result = r.json()

            related_terms = get_entities_terms_result['related_terms']
            entity_terms = get_entities_terms_result['entity_terms']

            # Call API to get timeseries
            payload = {
                'result': result,
                'end_intervals_dates': end_intervals_dates
            }
            r = requests.get(API_TLSCOVID_ENDPOINT +
                             'get-timeseries', json=payload)
            get_timeseries_result = r.json()

            news_timeseries_rs = get_timeseries_result['news_timeseries_rs']
            sources_overall = get_timeseries_result['sources_overall']
            overall_timeseries = get_timeseries_result['overall_timeseries']

            return render_template('pages/tlscovid/search.html', form=form,
                                   result=result,
                                   events=res_events,
                                   result_header=result_header,
                                   related_terms=related_terms,
                                   domains=domains,
                                   selected_provider=source_name,
                                   advanced_mode=True,
                                   sources_overall=sources_overall,
                                   overall_timeseries=overall_timeseries,
                                   first_date=news_timeseries_rs["first_date"],
                                   last_date=news_timeseries_rs["last_date"],
                                   entity_terms=entity_terms,
                                   hasNarrative=hasNarrative,
                                   user_query=fquery,
                                   lang_code=lang_code,
                                   index=index)
    
    else:
        # If request does not contain id

        # If request contains query, redirect to searching and process for the first time
        if 'query' in request.args:
            return redirect(url_for('pages_tlscovid.searching', query=fquery, index=index))

        # If request doesn't contain neither id nor query, redirect to search page to perform new search
        else:
            return render_template('pages/tlscovid/search.html', lang_code=lang_code, form=SearchForm(), related_terms=[], result=None, user_query=None, hasNarrative=hasNarrative)
        