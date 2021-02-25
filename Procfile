web: python manage.py collectstatic --noinput;
web: bin/start-pgbouncer-stunnel gunicorn PVE.wsgi --log-file -
web: python manage.py runserver 0.0.0.0:$PORT;