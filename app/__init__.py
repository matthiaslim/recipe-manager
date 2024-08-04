from flask import Flask
import click
from flask.cli import with_appcontext
from .db import close_db, close_redis, close_mongo_db, get_db
from mysql.connector import Error


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


def execute_sql_file(cursor, filename):
    with open(filename, 'r') as file:
        sql_script = file.read()

    # Split statements by semicolon, handling multi-line statements
    statements = sql_script.split(';')

    for statement in statements:
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
            except Error as e:
                print(f"Error executing statement: {e}")


def init_db():
    try:
        db = get_db()
        if db is None:
            print("Error: unable to connect to MySQL")
            return

        cursor = db.cursor()
        execute_sql_file(cursor, './app/data_prep/table.sql')
        db.commit()
        cursor.close()
        print("Database initialized successfully.")
    except Error as e:
        print(f"MySQL Database Error: {e}")


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the MySQL database with schema and data')


def init_app(app):
    app.cli.add_command(init_db_command)
