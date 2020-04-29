# Platform voor Programma van Eisen
A Django platform for generating, sharing and editing PvE's.

# Initiating for Windows
Requires Python and pip installed.
- Run `pip install -r requirements.txt` to install all of the required packages.
- The database is set locally in the `db.sqlite3` file, generated on the `manage.py` level. Generate the database by running `python manage.py makemigrations` and `python manage.py migrate`.
- Static files are served by the `whitenoise` package. Collect the staticfiles by running `python manage.py collectstatic`.
- Run `python manage.py runserver` to run the server locally.