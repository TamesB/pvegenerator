# Introduction
A Django web-application for generating, sharing and editing PvE's.\
A PvE in this context is a set of rules that govern the requirements for construction of buildings in the Netherlands. This application was built for the VBR Groep, ultimately for SAREF, with the intention of creating a central platform to help clients to create projects, edit and discuss PvE requirements with each other, and generate the ending PvE PDF file with all its attachments in a quick and easy way, without the hassle of e-mailing Excel worksheets around.

# Initiating for Windows
Requires Python and pip installed.
- Run `pip install -r requirements.txt` to install all of the required packages.
- Create a superuser to access all of the features by running `python manage.py createsuperuser`, this account can be used to log in to the main application.
- The database is set locally in the `db.sqlite3` file, generated on the `manage.py` level. Generate the database by running `python manage.py makemigrations` and `python manage.py migrate`.
- Static files are served by the `whitenoise` package. Collect the staticfiles by running `python manage.py collectstatic`.
- Run `python manage.py runserver` to run the server locally.
- Log in with your superuser credentials.
