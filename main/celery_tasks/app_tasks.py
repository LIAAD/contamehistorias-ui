from celery import shared_task
import requests

API_ARQUIVOPT_ENDPOINT = 'http://localhost:5001/api/arquivopt/'
API_TLSCOVID_ENDPOINT = 'http://localhost:5001/api/tlscovid/'


@shared_task(name='celery_tasks.execute_engine_arquivopt', bind=True)
def execute_engine_arquivopt(self, query, last_years):

    payload = {'query': query, 'last_years': last_years}

    r = requests.get(API_ARQUIVOPT_ENDPOINT +
                     'execute-engine', json=payload)

    return {'status': 'Task completed', 'query': query, 'last_years': last_years, 'result': r.json()}


@shared_task(name='celery_tasks.execute_engine_tlscovid', bind=True)
def execute_engine_tlscovid(self, query, index):

    payload = {'query': query, 'index': index}

    r = requests.get(API_TLSCOVID_ENDPOINT +
                     'execute-engine', json=payload)

    return {'status': 'Task completed', 'query': query, 'index': index, 'result': r.json()}
