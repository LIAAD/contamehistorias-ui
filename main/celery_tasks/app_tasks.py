from celery import shared_task
import requests

API_ARQUIVOPT_ENDPOINT = 'http://localhost:5001/api/arquivopt/'


@shared_task(name='celery_tasks.execute_engine', bind=True)
def execute_engine(self, query, last_years):

    payload = {'query': query, 'last_years': last_years}

    r = requests.get(API_ARQUIVOPT_ENDPOINT +
                     'execute-engine', json=payload)

    return {'status': 'Task completed', 'query': query, 'last_years': last_years, 'result': r.json()}
