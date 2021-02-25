web: bin/start-pgbouncer-stunnel gunicorn PVE/wsgi.py --log-file -
web: python manage.py collectstatic --no-input; gunicorn myapp.wsgi --log-file - --log-level debug
web: python manage.py runserver 0.0.0.0:$PORT