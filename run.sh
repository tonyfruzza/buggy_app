#!/bin/sh
export PATH=$PATH:/usr/local/bin
pipenv install
pipenv run pip3 install -r requirements.txt
FLASK_ENV=development pipenv run flask run
