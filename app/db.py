import mysql.connector
import pymongo
from pymongo import MongoClient
from flask import current_app, g
import redis


def get_db():
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host=current_app.config['MYSQL_HOST'],
                user=current_app.config['MYSQL_USER'],
                password=current_app.config['MYSQL_PASSWORD'],
                database=current_app.config['MYSQL_DB']
            )
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    return g.db


def get_mysql_connection():
    try:
        return mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD']
        )
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def create_database():
    connection = get_mysql_connection()
    if connection is None:
        return False

    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {current_app.config['MYSQL_DB']}")
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Error creating database: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

    return True


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def get_redis():
    if 'redis' not in g:
        try:
            g.redis = redis.Redis(
                host=current_app.config['REDIS_HOST'],
                port=current_app.config['REDIS_PORT'],
                db=current_app.config['REDIS_DB'],
                decode_responses=True
            )
        except redis.RedisError as e:
            print(f"Error connecting to Redis: {e}")
            return None
    return g.redis


def close_redis(e=None):
    redis_db = g.pop('redis', None)
    if redis_db is not None:
        pass


def get_mongo_db():
    if 'mongo_db' not in g:
        try:
            g.mongo_client = MongoClient(current_app.config['MONGO_URI'])
            g.mongo_db = g.mongo_client[current_app.config['MONGO_DB']]
        except pymongo.errors.PyMongoError as e:
            print(f"Error connecting to MongoDB: {e}")
            return None
    return g.mongo_db


def close_mongo_db(e=None):
    mongo_client = g.pop('mongo_client', None)
    if mongo_client is not None:
        mongo_client.close()
