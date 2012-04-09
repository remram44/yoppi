# Yoppi

Yoppi is an automatic FTP indexer written in Python.

## Database migrations

We're now using south for the database migrations.

To convert an existing database, please run :

        python manage.py syncb
        python manage.py migrate --all 0001 --fake

The usual migration workflow is :

        python manage.py syncb
        python manage.py migrate

To create a new migration :

        python manage.py schemamigration --auto <app_name>

and don't forget to push the migration.

For more info, see [the south doc](http://south.aeracode.org/docs/)
