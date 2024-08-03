from flask import Flask, g, current_app
import click
from flask.cli import with_appcontext
from .db import get_db, close_db, get_redis, close_redis, get_mongo_db, close_mongo_db, create_database


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.teardown_appcontext(close_db)
    app.teardown_appcontext(close_redis)
    app.teardown_appcontext(close_mongo_db)

    from . import routes
    app.register_blueprint(routes.bp)

    init_app(app)

    return app


def execute_script_from_file(filename, cursor):
    with current_app.open_resource(filename) as f:
        statements = f.read().decode('utf8').split(';')
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)


def init_db():
    if not create_database():
        print("Error: unable to create MySQL database")
        return

    db = get_db()
    if db is None:
        print("Error: unable to connect to MySQL")
        return

    cursor = db.cursor()

    # Execute table creation script
    execute_script_from_file('data_prep/table.sql', cursor)
    db.commit()

    # Execute data insertion script
    execute_script_from_file('data_prep/InsertEverything.sql', cursor)
    db.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the MySQL database with schema and data')


def init_app(app):
    app.cli.add_command(init_db_command)
