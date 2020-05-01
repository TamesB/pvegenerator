# Introduction
A Django web-application for generating, sharing and editing PvE's.\
A PvE in this context is a set of rules that govern the requirements for construction of buildings in the Netherlands. This application was built for the VBR Groep, ultimately for SAREF, with the intention of creating a central platform to help clients to create projects, edit and discuss PvE requirements with each other, and generate the ending PvE PDF file with all its attachments in a quick and easy way, without the hassle of e-mailing Excel worksheets around.

# Installation for Windows
This application was written in `Django 3.0.5` with `Python 3.8.3rc1`.\
Requires `pip` installed.\
Instructions:
- Run `pip install -r requirements.txt` to install all of the required packages.
- Add your Database URI by setting the `DATABASE_URL` environment variable in `PVE/.env`. The database can also be chosen to be local in the `db.sqlite3` file generated on the `manage.py` level. See `PVE/settings.py` for the options, both choices are in the `DATABASES` variable, choose your default.
- Set environment variables `DEBUG=True` or `DEBUG=False` for debugging mode and `SECRET_KEY = random_long_char_string` for CSRF token encryption / form data encryption / XSS protection, in the `PVE/.env` file.
- Generate the database by running `python manage.py makemigrations` and `python manage.py migrate`.
- Create a superuser to access all of the features by running `python manage.py createsuperuser`, this account can be used to log in to the main application.
- Static files are served by the `whitenoise` package. Collect the staticfiles by running `python manage.py collectstatic`.
- Run `python manage.py runserver` to run the server locally.

# Heroku
This application is also readymade for Heroku. It can be ran almost right away.\
Instructions:
- Activate the heroku settings at the bottom of `PVE/settings.py`, choose the default database as the environment variable in the `DATABASES` section of the settings.
- Fork this project, use that git for deployment in your Heroku app.
- Add the environment variables `DATABASE_URL`, `DEBUG` and `SECRET_KEY` in the Config Vars in app Settings.
- Deploy.