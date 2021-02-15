<div align="center">
    <a href="http://contamehistorias.pt/arquivopt/" target="_blank">
	    <img width="300" height="250" src="main/static/img/contamehistorias-logo.png" alt="Conta-me Histórias">
    </a>
    <br>
    <b> This repository contains the source code of the user interface of <a href="http://contamehistorias.pt/arquivopt/" target="_blank">conta-me historias</a>. </b>

</div>


## Web application

[![Python](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-blue.svg)](https://www.python.org/)


The [conta-me historias](http://contamehistorias.pt/arquivopt/) web application depends on:
    
- the front-end user interface (this repository)
- the [back-end API](https://github.com/LIAAD/contamehistorias-api) to retrieve data

The user interface **will not work properly** without the back-end API. See [API](https://github.com/LIAAD/contamehistorias-api) for instructions on how to run the back-end server.


### Setup

It is recommended to setup a [virtual environment](https://docs.python.org/3.8/library/venv.html).

#### Install requirements

```shell
$ pip install -r requirements.txt
```

#### Run server

Directly from python

```shell
$ python run.py
```

or through Gunicorn

```shell
$ sh run.sh
```

#### Run celery worker

```shell
$ celery -A run:celery worker --loglevel=info
```
