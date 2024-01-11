#!/bin/bash

set -eu
envsubst '80, *, /api, http://localhost:5000' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
service nginx status
service nginx start
uwsgi --ini uwsgi.ini
