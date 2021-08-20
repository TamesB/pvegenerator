# Introduction
A Django web-application for generating, sharing and editing PvE's.\
A PvE in this context is a set of rules that govern the requirements for construction of buildings in the Netherlands. This application was built for the VBR Groep, ultimately for SAREF, with the intention of creating a central platform to help clients to create projects, edit and discuss PvE requirements with each other, and generate the ending PvE PDF file with all its attachments in a quick and easy way, without the hassle of e-mailing Excel worksheets around.

# Installation
## Installing on Windows
Requires `pip` installed.
Requires PostGIS + GDAL + OSGeo4W installed. (https://docs.djangoproject.com/en/3.1/ref/contrib/gis/install/#windows)

### Instructions
- Set up your virtual environment
- Download this project into your venv
- Run `pipenv install -r requirements.txt` to install all of the required packages.
- Add your Database URI by setting the `DATABASE_URL` environment variable in `PVE/.env`. The database can also be chosen to be local in the `db.sqlite3` file generated on the `manage.py` level. See `PVE/settings.py` for the options, both choices are in the `DATABASES` variable, choose your default.
- Set environment variables `DEBUG=True` or `DEBUG=False` for debugging mode and `SECRET_KEY = random_long_char_string` for CSRF token encryption / form data encryption / XSS protection, in the `PVE/.env` file.
- In the same file, set up an email server (this app heavily depends on sending push notifications via email to employees), using the variables `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, and optionally set `EMAIL_USE_SSL` to `True`.
- Employees can upload attachments to their comments / rules in the PvE, these attachments are uploaded to an Amazon S3 Bucket, set the variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_STORAGE_BUCKET_NAME` in your `.env` file.
- Finally, set `PRODUCTION` to `False` when developing.
- Generate the database by running `python manage.py makemigrations` and `python manage.py migrate`.
- Create a superuser to access all of the features by running `python manage.py createsuperuser`, this account can be used to log in to the main application.
- Static files are served by the `whitenoise` package. Collect the staticfiles by running `python manage.py collectstatic`.
- Run `python manage.py runserver` to run the server locally.

## Heroku CI/CD
This application is also readymade for continuous integration/delivery on Heroku.

### Instructions
- Activate the heroku settings at the bottom of `PVE/settings.py`, choose the default database as the environment variable in the `DATABASES` section of the settings.
- Fork this project, use that git for deployment in your Heroku app.
- Requires `pgbouncer` and `Geo Packages (GDAL/GEOS/PROJ)` buildpacks for limiting database connections and using a spatial database used for the project locations, `https://buildpack-registry.s3.amazonaws.com/buildpacks/heroku/pgbouncer.tgz` and `https://github.com/heroku/heroku-geo-buildpack.git` respectively. Of course requires the `heroku/python` buildpack.
- Add the environment variables `DATABASE_URL`, `DEBUG` and `SECRET_KEY` in the Config Vars in app Settings in your Heroku App.
- Set `PRODUCTION` to `1` or `0` in the Config Vars.
- Add `DISABLE_COLLECTSTATIC` and `DEBUG_COLLECTSTATIC` to your Config Vars if needed, set both to `1`.
- Attachments to rulesets or comments on them are uploaded to an AWS S3 bucket. Add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_STORAGE_BUCKET_NAME` in your Config Vars.
- The application heavily relies on sending update emails to clients, add an email server by adding these to the Config Vars: `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, and set `EMAIL_USE_SSL` to `True` if wanted.
- Deploy.
- When pushing new code to your git repo, you can automatically deploy the new version on Heroku.
