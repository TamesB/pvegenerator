# Platform for PvE generation
A Django platform for generating, sharing and editing PvE's.
A PvE is a set of rules that govern the requirements of construction of buildings in the Netherlands. This application was built for SAREF with the help of the VBR Groep, with the intention of creating a central platform to help clients to create projects and generate PvE's in an easy way, without the hassle of e-mailing Excel worksheets around.

# Initiating for Windows
Requires Python and pip installed.
- Run `pip install -r requirements.txt` to install all of the required packages.
- Create a superuser to access all of the features (this account can be used to log in to the main application), by running `python manage.py createsuperuser`.
- The database is set locally in the `db.sqlite3` file, generated on the `manage.py` level. Generate the database by running `python manage.py makemigrations` and `python manage.py migrate`.
- Static files are served by the `whitenoise` package. Collect the staticfiles by running `python manage.py collectstatic`.
- Run `python manage.py runserver` to run the server locally.
- Log in with your superuser credentials.
