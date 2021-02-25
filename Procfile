web: bin/start-pgbouncer-stunnel gunicorn PVE/wsgi.py --log-file -
web: python manage.py collectstatic
web: python manage.py runserver 0.0.0.0:$PORT