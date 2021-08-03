# Library Server <sup><sup>v0.0.1</sup></sup>
University Central Library Backend


[![Code style: black](https://img.shields.io/badge/language-Python3.8-00AA00.svg)](https://docs.python.org/3.8/)
[![Code style: black](https://img.shields.io/badge/framework-Django%203.2-008800.svg)](https://docs.djangoproject.com/en/3.2/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Perquisites
### Install Dependencies
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install dependencies.

```bash
pip install -r requirements.txt
```

### Setup Database
Create an empty database and set its configuration params in *library/settings.py* (default is sqlite):

```python
# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': '?',
        'NAME': '?',
        'USER': '?',
        'PASSWORD': '?',
        ...
    }
}
```

Then run the following command to let django create tables for you:

```bash
python manage.py migrate
```

You can add sample data provided in fixtures folder of each app via:
```bash
python manage.py loaddata <filename>
```

## Usage
### Run Project
```bash
python manage.py runserver
```

## Contributing
For each issue, fork master into a new branch and push codes there. When ready, submit a merge request for review.
For major changes, please open an issue first to discuss what you would like to change.


---
Copyright © 2020 [Zeynab Amini](mailto:zeynab0amini@gmail.com)
