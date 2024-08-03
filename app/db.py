import mysql.connector
from pymongo import MongoClient
from flask import current_app, g
from flask.cli import with_appcontext
import click
import redis


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB']
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_redis():
    if 'redis' not in g:
        g.redis = redis.StrictRedis(
            host=current_app.config['REDIS_HOST'],
            port=current_app.config['REDIS_PORT'],
            db=current_app.config['REDIS_DB'],
            decode_responses=True
        )
    return g.redis

def close_redis(e=None):
    redis_db = g.pop('redis', None)
    if redis_db is not None:
        redis_db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    with current_app.open_resource('../data_prep/table.sql') as f:
        cursor.execute(f.read().decode('utf8'))
    db.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def get_mongo_db():
    if 'mongo_db' not in g:
        g.mongo_client = MongoClient(current_app.config['MONGO_URI'])
        g.mongo_db = g.mongo_client[current_app.config['MONGO_DB']]
    return g.mongo_db

def close_mongo_db(e=None):
    mongo_client = g.pop('mongo_client', None)
    if mongo_client is not None:
        mongo_client.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.teardown_appcontext(close_redis)
    app.cli.add_command(init_db_command)
