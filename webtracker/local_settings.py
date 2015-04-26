# -*- coding: utf-8 -*-

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'webtracker',  # Or path to database file if using sqlite3.
        'USER': 'admin',  # Not used with sqlite3.
        'PASSWORD': 'admin',  # Not used with sqlite3.
        'HOST': '127.0.0.1',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {"init_command": "SET storage_engine=INNODB", },
        # DATABASE_OPTIONS = { "init_command": "SET storage_engine=INNODB, SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED", }
    }
}

# settings for direct connection to database
DB_PARMS = {'host':"localhost",
            'user': "admin",
            'passwd': "admin",
            'db': "webtracker",
            'charset': 'utf8'}
