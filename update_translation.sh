# https://flask-babel.tkte.ch/#translating-applications
pybabel extract main -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d main/translations
pybabel compile -d main/translations
