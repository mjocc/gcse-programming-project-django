# gcse-programming-project-django

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

A django rewrite of [gcse-programming-project](https://www.github.com/mjocc/gcse-programming-project) (originally in Flask).

## Setup

First, install poetry if not already installed:
```bash
python -m pip install --user poetry
```

Then, run `poetry install` to create the virtualenv and install dependencies before activating the virtualenv with `poetry shell`:
```bash
python -m poetry install
python -m poetry shell
```

After that, navigate into the `gcse_programming_project` sub-directory before creating the database and collecting/processing static files:
```bash
python manage.py migrate
python manage.py collectstatic
```

All later commands in this README assume you have activated the virtualenv and in the top-level `gcse_programming_project` directory.

## Development

A Django development server can be run:
```bash
python manage.py runserver
```
This will serve the site on `localhost:8000` by default.

If any changes are made to `models.py`, make database migrations and then migrate your database:
```bash
python manage.py makemigrations
python manage.py migrate
```

To work with the site (specifically the database models) in an interactive shell:
```bash
python manage.py shell
```

To create a user for the admin site:
```bash
python manage.py createsuperuser
```
The admin site is served at `/admin/` and allows for easy manipulation of the database models

To import airport/aircraft data from csv files (with no headers):
```bash
python manage.py import {airport,aircraft} file
```
For more information, use the `--help` flag.

## Production

Poetry will install a different production server depending on the operating system - gunicorn for linux and waitress for windows. Static files are handled by whitenoise on both platforms. In production, it is strongly recommended that a load balancer, such as nginx, is used.

### Linux

Run the gunicorn server on `localhost:8000`:
```bash
gunicorn gcse_programming_project.wsgi:application
```

### Windows

Run the waitress server on `localhost:8080`:
```bash
waitress-serve gcse_programming_project.wsgi:application
```
