export FLASK_CONFIG='production'
# Change secret key before launching in production!
export SECRET_KEY='1209876'

gunicorn -b 0.0.0.0:5000 run:app --timeout 180 --keep-alive 10000 --limit-request-line 40940 --workers 8
