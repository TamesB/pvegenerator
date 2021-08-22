# Introduction
A Django web-application for generating, sharing and editing PvE's.\
A PvE in this context is a set of rules that govern the requirements for construction of buildings in the Netherlands. This application was built for the VBR Groep, ultimately for SAREF, with the intention of creating a central platform to help clients to create projects, edit and discuss PvE requirements with each other, and generate the ending PvE PDF file with all its attachments in a quick and easy way, without the hassle of e-mailing Excel worksheets around.

# Features
## PvE Ruleset
The ruleset is composed of many individual rules. Each rule is connected to parameters; an object type (type of house, appartment, etc..), construction type (new construction, transformation, commercial, etc..) and target audience (starters, new families, etc...). A rule can be in multiple parameters. A rule can also be a BASIC rule, which is always in the ruleset regardless the parameter choices. When downloading a ruleset, one can choose the parameters (example; 0-50m2 appartments for starters, new construction), and a PDF rolls out with all the construction rules for this specific type of construction. This is the basic idea for the app.

## Project management
- In a closed off subwebsite, a subwebsite administrator (some construction company) can start a project, where the ruleset parameters are chosen at the start. A project page is created and the ruleset can be downloaded with one click. We invite the projectmanager, and we can add third-parties to view the project, which is done by email invitation.
- Now, the projectmanager and third parties can perform something called the 'ping-pong process'. Its a process of setting a status on each rule in the ruleset (accepted, not accepted, to be discussed, etc...) and place comments on each rule, add attachments, and add the cost for this rule. These comment sets are then saved, and can be sent with a single click to the opposing party, who then accepts the status, or comments on it further and sends it back, as if it's a game of ping-pong. This is done in intuitive sections (Section of 'rules yet to be commented on', 'rules commented on last time', 'rules accepted last time'. 
- On the dashboard it shows a list of each project that is to-do for each user, with a simple button that leads them to the commenting). Eventually there is an agreement for every rule, then the project is frozen, no one can comment on it anymore. The ruleset with their statuses and comments per rule, and the total costs of all rules, can then be downloaded as a single PDF, and the attachments with them are inside a .zip file.
- This way, construction companies and third parties can easily and safely discuss the ruleset, and keep it in one page, instead of multiple excel sheets running around through email, which has the chance of people accidentally (or intentionally) removing earlier comments.
- Each time a set of comments is sent through to the opposing party / someone is invited to a project / a project is finished, an email is sent to the person notifying they have to respond with a link to it. 

## Administrative Site
- Editing a ruleset, editing the parameters, creating new rulesets, setting the active ruleset version for the sub-website. They can edit each rule easily (breadcrumb structure with chapters and paragraphs), adding attachments to a rule and setting the parameters.
- Overview of all accounts, creating all types of users manually
- Heatmap of all project locations
- Generate test-rulesets (as PDF)
- Generate the rule difference between two parameters (as PDF)

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
- Edit extra `ALLOWED_HOSTS` with environment variables `HOST1` and `HOST2`, or edit them in `settings.py`.
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
- Edit extra `ALLOWED_HOSTS` with environment variables `HOST1` and `HOST2`, or edit them in `settings.py`. `HOST1` can be used for your herokuapp.com subwebsite. 
- Deploy.
- When pushing new code to your git repo, you can automatically deploy the new version on Heroku.
