web: gunicorn ceibs_management.wsgi --log-file -

worker: celery -A ceibs_management worker --loglevel=INFO

