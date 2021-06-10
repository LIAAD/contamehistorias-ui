from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import requests

API_ARQUIVOPT_ENDPOINT = 'http://localhost:5001/api/arquivopt/'
API_TLSCOVID_ENDPOINT = 'http://localhost:5001/api/tlscovid/'


@shared_task(name='celery_tasks.execute_engine_arquivopt', bind=True, soft_time_limit=60)
def execute_engine_arquivopt(self, query, last_years):

    payload = {'query': query, 'last_years': last_years}

    try:
        r = requests.get(API_ARQUIVOPT_ENDPOINT +
                        'execute-engine', json=payload)

        return {'status': 'Task completed', 'query': query, 'last_years': last_years, 'result': r.json()}
    except SoftTimeLimitExceeded:
        return {'status': 'Task timeout', 'query': query}


@shared_task(name='celery_tasks.execute_engine_tlscovid', bind=True, soft_time_limit=60)
def execute_engine_tlscovid(self, query, index, selected_sources, use_headline):

    payload = {'query': query, 'index': index, 'sources': selected_sources, 'use_headline': use_headline}

    try:
        r = requests.get(API_TLSCOVID_ENDPOINT +
                        'execute-engine', json=payload)

        return {'status': 'Task completed', 'query': query, 'index': index, 'selected_sources': selected_sources, 'use_headline': use_headline, 'result': r.json()}
    except SoftTimeLimitExceeded:
        return {'status': 'Task timeout', 'query': query}
