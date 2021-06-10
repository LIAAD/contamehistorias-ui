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
    if current_app.url_map.is_endpoint_expecting(endpoint, 'lang'):
        values['lang'] = session.get('lang', "pt")
        g.lang = session.get('lang', "pt")

    try:
        values.setdefault('lang', g.lang)
    except:
        values.setdefault('lang', session.get('lang', "pt"))


@blueprint.url_value_preprocessor
def pull_lang_code(endpoint, values):
    lang = request.args.get('lang')
    session['lang'] = lang
    g.lang = session.get('lang', "pt")


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
    selected_sources = request.args.getlist('selected_sources')
    use_headline = request.args.get('use_headline', type=str)

    return render_template('pages/tlscovid/searching.html', query=query, index=index, selected_sources=selected_sources, use_headline=use_headline)


@blueprint.route('/longtask', methods=['GET'])
def long_task():

    query = request.args.get('query', type=str)
    index = request.args.get('index', default='pt', type=str)
    selected_sources = request.args.getlist('selected_sources')
    use_headline = request.args.get('use_headline', type=str)

    task_id = current_app.celery.send_task(
        'celery_tasks.execute_engine_tlscovid', args=[query, index, selected_sources, use_headline])

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
                'pages_tlscovid.search', query=task.info['query'], index=task.info['index'], selected_sources=task.info['selected_sources'], use_headline=task.info['use_headline'])
        else:
            response['url_for'] = url_for(
                'pages_tlscovid.search', query=task.info['query'], timeout=True)
    else:
        # something went wrong in the background job
        response = {
            'task_id': task_id,
            'state': task.state,
            'status': str(task.info),  # this is the exception raised,
            'url_for': url_for('pages_tlscovid.search', query=task.info['query'], timeout=True)
        }
    return jsonify(response)
#####################################################################################


@blueprint.route('/')
def home():

    form = SearchForm(request.form)

    lang = session.get("lang", "pt")

    if(lang == None):
        lang = "pt"

    r = requests.get(API_TLSCOVID_ENDPOINT + 'get-examples')
    examples = r.json()

    stories_examples = {
        "topics_pt": examples['pt'],
        "topics_en": examples['en'],
    }

    return render_template('pages/tlscovid/home.html', stories_examples=stories_examples, form=form, lang=lang)


@blueprint.route('/team')
def team():
    return render_template('pages/common/team.html')


@blueprint.route('/press')
def press():
    return render_template('pages/common/press.html')


@blueprint.route('/about')
def about():
    return render_template('pages/tlscovid/about.html')


@blueprint.route('/change/<new_lang_code>')
def change(new_lang_code):

    if not(new_lang_code in LANGUAGES):
        new_lang_code = "pt"

    session['lang'] = new_lang_code

    # Redirect to same page with changed lang
    redirect_url = furl(request.referrer)
    redirect_url.args['lang'] = new_lang_code

    return redirect(redirect_url)


@blueprint.route('/search', methods=['GET'])
def search():

    # Default parameters
    has_narrative = False

    # Lang Code
    lang = session.get("lang", "pt")
    if(lang == None or lang not in LANGUAGES):
        lang = "pt"
    try:
        if(lang == "pt"):
            locale.setlocale(locale.LC_TIME, 'pt_PT.utf8')
        else:
            locale.setlocale(locale.LC_TIME, 'en_US.utf8')
    except:
        print("No time locale")

    # Handle request parameters
    form = SearchForm(request.form)

    query = request.args.get('query', type=str)
    form.query.data = query

    # Get type of content to process
    # If user selected in form
    if 'form_content_type' in request.args:
        use_headline = request.args.get('form_content_type', type=str)

        if use_headline == 'contents':
            use_headline = True
        else:
            use_headline = False
    # Parameter passed in url
    elif 'use_headline' in request.args:
        use_headline = request.args.get('use_headline', type=str)

        if use_headline == 'True':
            use_headline = True
        else:
            use_headline = False
    # Defaults to False and use titles
    else:
        use_headline = False

    if 'form_index' in request.args:
        index = request.args.get('form_index', type=str)
    else:
        index = request.args.get('index', default=lang, type=str)

    selected_sources = request.args.getlist('selected_sources')

    print('Query:', query)
    print('Index:', index)
    print('Lang code:', lang)

    # Call API to available indices
    r = requests.get(API_TLSCOVID_ENDPOINT +
                        'get-indices')
    available_indices = r.json()

    # Call API to available domains
    r = requests.get(API_TLSCOVID_ENDPOINT +
                        'get-domains')
    domains = r.json()
    available_domains = {k:[] for k in available_indices}
    for d in domains:
        available_domains[d['lang']].append(d['name'])

    # Insert sources if not in query string
    if not selected_sources:
        selected_sources = available_domains[index]

    if 'timeout' in request.args:
        return render_template('pages/tlscovid/search.html', lang=lang, form=SearchForm(), related_terms=[], result=None, query=query, has_narrative=has_narrative, available_indices=available_indices, available_domains=available_domains, timeout=True)

    # Task already processed
    if 'id' in request.args:

        task_id = request.args.get('id')
        task = current_app.celery.AsyncResult(task_id)

        # Check if task exists
        try:
            result = task.info['result']
        except TypeError:
            print('Invalid task')
            return render_template('pages/tlscovid/search.html', lang=lang, form=SearchForm(), related_terms=[], result=None, query=None, has_narrative=has_narrative, available_indices=available_indices, available_domains=available_domains)
        
        if not result:
            print('Invalid result')
            return render_template('pages/tlscovid/search.html', lang=lang, form=form, related_terms=[], result=None, query=query, has_narrative=has_narrative, available_indices=available_indices, available_domains=available_domains)

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

            # List of lists. Each inner list is [term, tf, h]
            relevant_terms = result['most_relevant_terms']

            if(result["status"] != "OK"):
                return render_template('pages/tlscovid/search.html', lang=lang, form=form, related_terms=[], result=None, result_header=result_header, has_narrative=has_narrative, available_indices=available_indices, available_domains=available_domains)

            if(int(result["stats"]["n_unique_docs"]) == 0):
                return render_template('pages/tlscovid/search.html', lang=lang, form=form, related_terms=[], result=None, result_header=result_header, has_narrative=has_narrative, available_indices=available_indices, available_domains=available_domains)

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

            print("---------------------------------------")
            print("Check if there is more than one interval and if there are news")
            print("Number of news to present:", len(all_titles))
            print("Number of intervals:", len(res_events))

            if(len(all_titles) > 0 and len(res_events) >= 2):
                has_narrative = True

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

            # Check if query is topic and has key moments
            r = requests.get(API_TLSCOVID_ENDPOINT + 'get-examples')
            topics = r.json()
            index_topics = [topic for sublist in topics[index].values() for topic in sublist]
            is_topic = query in index_topics

            return render_template('pages/tlscovid/search.html', form=form,
                                   result=result,
                                   events=res_events,
                                   result_header=result_header,
                                   related_terms=related_terms,
                                   domains=domains,
                                   sources_overall=sources_overall,
                                   overall_timeseries=overall_timeseries,
                                   first_date=news_timeseries_rs["first_date"],
                                   last_date=news_timeseries_rs["last_date"],
                                   entity_terms=entity_terms,
                                   has_narrative=has_narrative,
                                   query=query,
                                   lang=lang,
                                   index=index,
                                   is_topic=is_topic,
                                   selected_sources=selected_sources,
                                   available_indices=available_indices,
                                   available_domains=available_domains,
                                   relevant_terms=relevant_terms,
                                   use_headline=use_headline)
    
    else:
        # If request does not contain id

        # If request contains query, redirect to searching and process for the first time
        if 'query' in request.args:
            return redirect(url_for('pages_tlscovid.searching', query=query, index=index, selected_sources=selected_sources, use_headline=use_headline))

        # If request doesn't contain neither id nor query, redirect to search page to perform new search
        else:
            return render_template('pages/tlscovid/search.html', lang=lang, form=SearchForm(), related_terms=[], result=None, query=None, index=index, has_narrative=has_narrative, available_indices=available_indices, available_domains=available_domains)
        