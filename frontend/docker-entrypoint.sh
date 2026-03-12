#!/bin/sh

BACKEND_HOST=${BACKEND_HOST:-"localhost"}
BACKEND_PORT=${BACKEND_PORT:-"8000"}

envsubst '${BACKEND_HOST} ${BACKEND_PORT}' \
    < /etc/nginx/templates/default.conf.template \
    > /etc/nginx/conf.d/default.conf

exec "$@"