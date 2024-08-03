import math
import mysql.connector

from .db import get_db, get_redis, get_mongo_db
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_paginate import Pagination, get_page_parameter
from bcrypt import hashpw, gensalt, checkpw
from functools import wraps
from bson import ObjectId

bp = Blueprint('routes', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page!', 'danger')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)

    return decorated_function


def get_threads_with_replies(search_query=None):
    db = get_mongo_db()
    try:
        if search_query:
            threads = db.thread.find({'threadName': {'$regex': search_query, '$options': 'i'}})
        else:
            threads = db.thread.find()

        comment_list = []
        for thread in threads:
            comment = {
                'threadID': str(thread['_id']),
                'threadName': thread['threadName'],
                'created_by': thread['created_by'],
                'created_by_username': thread['created_by_username'],
                'replies': thread['replies'],
                'count': len(thread['replies'])
            }
            comment_list.bpend(comment)
        return comment_list
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error fetching comments from database: {e}"
        }), 500

    # db = get_db()
    # cursor = db.cursor(dictionary=True)
    # try:
    #     if search_query:
    #         cursor.execute(
    #             'SELECT t.threadID, t.threadName, u.userName, t.reply_count FROM temp_thread_with_replies t INNER JOIN User u ON t.thread_created_by = u.userID WHERE t.threadName LIKE %s',
    #             ('%' + search_query + '%',))
    #     else:
    #         cursor.execute(
    #             'SELECT t.threadID, t.threadName, u.userName, t.reply_count FROM temp_thread_with_replies t INNER JOIN User u ON t.thread_created_by = u.userID')
    #     fetched_comments = cursor.fetchall()
    #     comments_list = []
    #     for comment in fetched_comments:
    #         comment_dict = {
    #             'threadID': comment['threadID'],
    #             'threadName': comment['threadName'],
    #             'created_by': comment.get('userName', 'Unknown'),  # Corrected from 'username' to 'userName'
    #             'count': comment.get('reply_count', 0),
    #             'replies': []
    #         }
    #         comments_list.bpend(comment_dict)

    #     return comments_list

    # except mysql.connector.Error as err:
    #     return jsonify({
    #         'success': False,
    #         'error': f"Error fetching comments from database: {err}"
    #     }), 500

    # finally:
    #     cursor.close()
    #     db.close()


# Context processor to inject `user_logged_in` and `username` into templates
@bp.context_processor
def inject_user():
    return dict(user_logged_in='username' in session, username=session.get('username'))


# Index
@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/save_search', methods=['POST'])
def save_search():
    term = request.json.get('term')
    user_id = session.get('user_id')
    if term:
        r = get_redis()
        key = f'previous_searches:{user_id}'
        r.lrem(key, 0, term)
        r.lpush(key, term)
        r.ltrim(key, 0, 9)
    return '', 204


@bp.route('/load_searches', methods=['GET'])
def load_searches():
    user_id = session.get('user_id')
    if user_id:
        r = get_redis()
        key = f'previous_searches:{user_id}'
        searches = r.lrange(key, 0, -1)
        return jsonify([search for search in searches])


@bp.route('/clear_searches', methods=['POST'])
def clear_searches():
    user_id = session.get('user_id')
    if user_id:
        r = get_redis()
        key = f'previous_searches:{user_id}'
        r.delete(key)  # Delete the key and its associated data
    return '', 204


# Login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        entered_password = request.form['password'].encode()

        try:
            cursor.execute('SELECT * FROM User WHERE username = %s', (username,))
            user = cursor.fetchone()

            if user and checkpw(entered_password, user['password'].encode()):
                session['username'] = user['username']
                session['user_id'] = user['userID']
                flash('Login Successful!', 'success')
                return redirect(url_for('routes.index'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
                return redirect(url_for('routes.login'))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'danger')

        finally:
            cursor.close()
            db.close()

    return render_template('login.html')


# Register
@bp.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # If password does not match the confirmation
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('routes.register'))

        salt = gensalt()  # Generate a random salt
        hashed_password = hashpw(password.encode(), salt)  # Hash the password

        try:
            # Check if username already exists
            cursor.execute('SELECT * FROM User WHERE username = %s', (username,))
            if cursor.fetchone():
                flash('Username already exists. Please try a different one.', 'danger')
            else:
                # Insert new user into database
                cursor.execute('INSERT INTO User (username, password) VALUES (%s, %s)', (username, hashed_password))
                db.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('routes.login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('register.html')


# Logout
@bp.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('routes.index'))


# Profile
@bp.route('/profile')
@login_required
def profile():
    if 'user_id' in session:
        user_id = session['user_id']
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute('SELECT * FROM User WHERE userID = %s', (user_id,))
            user = cursor.fetchone()
            if user:
                # Fetch additional information such as recipes created, threads created, replies made
                cursor.execute('''
                               SELECT (SELECT COUNT(*) FROM Recipe WHERE created_by = %s) AS recipes_count, 
                               (SELECT COUNT(*) FROM Thread WHERE created_by = %s) AS threads_count, 
                               (SELECT COUNT(*) FROM Reply WHERE created_by = %s) AS replies_count
                               ''', (user_id, user_id, user_id))
                counts = cursor.fetchone()

                return render_template('profile.html', user=user, recipes_count=counts['recipes_count'],
                                       threads_count=counts['threads_count'], replies_count=counts['replies_count'])
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
        finally:
            cursor.close()
            db.close()
    return redirect(url_for('routes.login'))


# Change Password
@bp.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if 'user_id' in session:
        user_id = session['user_id']
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            try:
                cursor.execute('SELECT password FROM User WHERE userID = %s', (user_id,))
                user = cursor.fetchone()

                if user and checkpw(current_password.encode(), user['password'].encode()):
                    if new_password == confirm_password:
                        hashed_password = hashpw(new_password.encode(), gensalt())
                        cursor.execute('UPDATE User SET password = %s WHERE userID = %s', (hashed_password, user_id))
                        db.commit()
                        flash('Password updated successfully!', 'success')
                        return redirect(url_for('routes.profile'))
                    else:
                        flash('New passwords do not match. Please try again.', 'danger')
                else:
                    flash('Current password is incorrect. Please try again.', 'danger')

            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
            finally:
                cursor.close()
                db.close()

        return render_template('change_password.html')

    return redirect(url_for('routes.login'))


# Recipe CRUD
# Get all recipes
@bp.route('/recipes', methods=['GET'])
def get_recipes():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Get current page number and search term
        page = request.args.get(get_page_parameter(), type=int, default=1)
        search_term = request.args.get('search', '')
        per_page = 5  # Number of recipes per page
        offset = (page - 1) * per_page

        # Build the query dynamically based on the search term
        query_params = []
        if search_term:
            search_query = "WHERE r.recipeName LIKE %s"
            query_params.bpend(f"%{search_term}%")
        else:
            search_query = ""

        # Fetch total number of recipes
        query = f"SELECT COUNT(*) as total FROM Recipe r {search_query}"
        cursor.execute(query, query_params)
        total = cursor.fetchone()['total']

        # Fetch recipes for the current page
        query = (
            f"SELECT r.recipeID, r.recipeName, r.description, u.username "
            f"FROM Recipe r JOIN User u ON r.created_by = u.userID "
            f"{search_query} LIMIT %s OFFSET %s"
        )
        query_params.extend([per_page, offset])
        cursor.execute(query, query_params)
        recipes = cursor.fetchall()

        # Create pagination object
        pagination = Pagination(page=page, total=total, per_page=per_page, css_framework='bootstrap5',
                                search=search_term, record_name='recipes')

        return render_template('recipes/recipes.html', page_title="Discover Recipes", recipes=recipes,
                               pagination=pagination, search_term=search_term, is_discover=True)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')

    finally:
        cursor.close()
        db.close()


@bp.route('/search_by_ingredient', methods=['GET', 'POST'])
def search_by_ingredient():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            # Get input data from form
            ingredients_input = request.form.get('ingredients', '').strip()
            search_option = request.form.get('search_option', 'only_listed')
            page = 1  # Start with the first page for new search
        else:
            # For GET requests, retrieve search parameters from query string
            ingredients_input = request.args.get('ingredients', '').strip()
            search_option = request.args.get('search_option', 'only_listed')
            page = int(request.args.get('page', 1))

        # Split ingredients_input into a list of ingredients
        ingredients_list = [ingredient.strip().lower() for ingredient in ingredients_input.split(',')]

        # Construct the SQL query with LIKE for partial matching
        if search_option == 'only_listed':
            # Search for recipes containing all listed ingredients
            select_recipes_query = """
                SELECT r.*
                FROM Recipe r
                JOIN Recipe_Ingredient ri ON r.recipeID = ri.recipeID
                JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE {}
                GROUP BY r.recipeID
                HAVING COUNT(DISTINCT i.ingredientID) = {}
                LIMIT %s OFFSET %s
            """.format(' AND '.join(['LOWER(i.ingredientName) LIKE %s'] * len(ingredients_list)), len(ingredients_list))

            # Adjust ingredients_list for LIKE operation
            ingredients_list = ['%' + ingredient + '%' for ingredient in ingredients_list]

            # Calculate the total number of recipes
            count_query = """
                SELECT COUNT(DISTINCT r.recipeID) as total
                FROM Recipe r
                JOIN Recipe_Ingredient ri ON r.recipeID = ri.recipeID
                JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE {}
                GROUP BY r.recipeID
                HAVING COUNT(DISTINCT i.ingredientID) = {}
            """.format(' AND '.join(['LOWER(i.ingredientName) LIKE %s'] * len(ingredients_list)), len(ingredients_list))

            cursor.execute(count_query, ingredients_list)
            total_recipes_result = cursor.fetchall()
            total_recipes = len(total_recipes_result)

        elif search_option == 'with_more':
            # Search for recipes containing any of the listed ingredients
            select_recipes_query = """
                SELECT DISTINCT r.*
                FROM Recipe r
                JOIN Recipe_Ingredient ri ON r.recipeID = ri.recipeID
                JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE {}
                LIMIT %s OFFSET %s
            """.format(' OR '.join(['LOWER(i.ingredientName) LIKE %s'] * len(ingredients_list)))

            # Adjust ingredients_list for LIKE operation
            ingredients_list = ['%' + ingredient + '%' for ingredient in ingredients_list]

            # Calculate the total number of recipes
            count_query = """
                SELECT COUNT(DISTINCT r.recipeID) as total
                FROM Recipe r
                JOIN Recipe_Ingredient ri ON r.recipeID = ri.recipeID
                JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE {}
            """.format(' OR '.join(['LOWER(i.ingredientName) LIKE %s'] * len(ingredients_list)))

            cursor.execute(count_query, ingredients_list)
            total_recipes = cursor.fetchone()['total']

        # Calculate the total number of pages
        per_page = 5  # Number of recipes per page
        total_pages = math.ceil(total_recipes / per_page)

        # Execute the query with adjusted ingredients_list and pagination
        params = ingredients_list + [per_page, (page - 1) * per_page]
        cursor.execute(select_recipes_query, params)
        recipes = cursor.fetchall()

        if not recipes:
            flash('No recipes found for the specified ingredients.', 'info')
            return render_template('recipes/search_by_ingredient.html', recipes=[], page=page, total_pages=total_pages,
                                   ingredients=ingredients_input, search_option=search_option)

        return render_template('recipes/search_by_ingredient.html', recipes=recipes, page=page, total_pages=total_pages,
                               ingredients=ingredients_input, search_option=search_option)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('routes.get_recipes'))

    finally:
        cursor.close()
        db.close()


# Get Recipe
@bp.route('/recipes/<int:recipe_id>')
def get_recipe_details(recipe_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session.get('user_id')

    try:
        # Get recipe details
        cursor.execute(
            'SELECT r.*, u.username FROM Recipe r JOIN User u ON r.created_by = u.userID WHERE r.recipeID = %s',
            (recipe_id,))
        recipe = cursor.fetchone()

        if not recipe:
            flash('Recipe not found', 'danger')
            return redirect(url_for('routes.recipes'))

        # Get ingredients
        cursor.execute('''
                SELECT i.ingredientName, ri.quantity, ri.unit
                FROM Recipe_Ingredient ri
                JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE ri.recipeID = %s
            ''', (recipe_id,))
        ingredients = cursor.fetchall()

        # Get directions
        cursor.execute('''
                SELECT instructionOrder, instruction
                FROM Recipe_Direction
                WHERE recipeID = %s
                ORDER BY instructionOrder
            ''', (recipe_id,))
        directions = cursor.fetchall()

        # Get ratings
        cursor.execute('''
                SELECT r.rating, r.comment, u.username, r.created_At
                FROM Rating r
                JOIN User u ON r.userID = u.userID
                WHERE r.recipeID = %s
            ''', (recipe_id,))
        ratings = cursor.fetchall()

        # Check if the recipe is favourited by the current user
        is_favourited = False
        if user_id:
            redis_db = get_redis()
            is_favourited = redis_db.sismember(f'user:{user_id}:favourites', recipe_id)

        return render_template('recipes/recipe_details.html', recipe=recipe, ingredients=ingredients,
                               directions=directions,
                               ratings=ratings, is_favourited=is_favourited)

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        return redirect(url_for('routes.recipes'))

    finally:
        cursor.close()
        db.close()


@bp.route('/save_favourite', methods=['POST'])
@login_required
def save_favourite():
    if request.content_type != 'application/json':
        return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400

    user_id = session.get('user_id')
    data = request.get_json()
    recipe_id = data.get('recipe_id')

    if not user_id or not recipe_id:
        return jsonify({'success': False, 'message': 'Invalid data'})

    try:
        redis_db = get_redis()
        # Check if the recipe is already favourited
        if redis_db.sismember(f'user:{user_id}:favourites', recipe_id):
            # If already favourited, remove it
            redis_db.srem(f'user:{user_id}:favourites', recipe_id)
            flash('Recipe removed from favourites!', 'success')
            return jsonify({'success': True, 'message': 'Recipe removed from favourites'})
        else:
            # If not favourited, add it
            redis_db.sadd(f'user:{user_id}:favourites', recipe_id)
            flash('Recipe added to favourites!', 'success')
            return jsonify({'success': True, 'message': 'Recipe added to favourites'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/favourites')
@login_required
def my_favourites():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to be logged in to view your favourite recipes!', 'danger')

    try:
        redis_db = get_redis()
        # Fetch favourite recipe IDs from Redis
        favourite_recipe_ids = redis_db.smembers(f'user:{user_id}:favourites')
        favourite_recipe_ids = [int(recipe_id) for recipe_id in favourite_recipe_ids]

        # Fetch recipe details from the database
        recipes = []
        total = 0
        if favourite_recipe_ids:
            format_strings = ','.join(['%s'] * len(favourite_recipe_ids))
            query = f"SELECT r.recipeID, r.recipeName, r.description, u.username " \
                    f"FROM Recipe r JOIN User u ON r.created_by = u.userID " \
                    f"WHERE r.recipeID IN ({format_strings})"
            cursor.execute(query, tuple(favourite_recipe_ids))
            recipes = cursor.fetchall()

            # Fetch total number of favourite recipes
            cursor.execute(f"SELECT COUNT(*) as total FROM Recipe WHERE recipeID IN ({format_strings})",
                           tuple(favourite_recipe_ids))
            total = cursor.fetchone()['total']

        # Create pagination object
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 5  # Number of recipes per page
        pagination = Pagination(page=page, total=total, per_page=per_page, css_framework='bootstrap5')
        pagination.record_name = 'favourites'

        return render_template('recipes/my_favourites.html', recipes=recipes, pagination=pagination)

    except Exception as e:
        flash(f'Error fetching favourite recipes: {str(e)}', 'danger')
        return redirect(url_for('routes.index'))
    finally:
        cursor.close()
        db.close()


# My Recipes Page
@bp.route('/my_recipes', methods=['GET'])
@login_required
def my_recipes():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session.get('user_id')

    try:
        search_term = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)

        per_page = 5  # Number of recipes per page
        offset = (page - 1) * per_page

        # SQL query to fetch recipes with optional search filter
        query = 'SELECT * FROM Recipe WHERE created_by = %s'
        params = [user_id]

        if search_term:
            query += ' AND (recipeName LIKE %s OR description LIKE %s)'
            params.extend([f'%{search_term}%', f'%{search_term}%'])

        query += ' LIMIT %s OFFSET %s'
        params.extend([per_page, offset])

        cursor.execute(query, params)
        recipes = cursor.fetchall()

        # Get the total count of recipes created by the user
        cursor.execute('SELECT COUNT(*) as count FROM Recipe WHERE created_by = %s', (user_id,))
        total_count = cursor.fetchone()['count']

        # Create pagination object
        pagination = Pagination(page=page, total=total_count, per_page=per_page, search=search_term,
                                css_framework='bootstrap5')

        return render_template('recipes/recipes.html', page_title="My Recipes", recipes=recipes,
                               search_term=search_term, pagination=pagination, is_discover=False)

    except (mysql.connector.Error, KeyError, TypeError) as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('routes.index'))

    finally:
        cursor.close()
        db.close()


# Add Recipe
@bp.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'POST':
        # Handle form submission to add a new recipe
        recipe_name = request.form.get('recipe_name')
        description = request.form.get('description')
        directions = request.form.getlist('directions[]')
        ingredients = request.form.getlist('ingredients[]')
        quantities = request.form.getlist('quantities[]')
        units = request.form.getlist('units[]')
        user_id = session.get('user_id')

        db = get_db()
        cursor = db.cursor()
        try:
            # Insert new recipe
            cursor.execute("INSERT INTO Recipe (recipeName, description, created_by) VALUES (%s, %s, %s)",
                           (recipe_name, description, user_id))
            recipe_id = cursor.lastrowid

            # Insert directions
            for i, direction in enumerate(directions):
                cursor.execute(
                    "INSERT INTO Recipe_Direction (recipeID, instructionOrder, instruction) VALUES (%s, %s, %s)",
                    (recipe_id, i + 1, direction))

            # Insert ingredients
            for ingredient, quantity, unit in zip(ingredients, quantities, units):
                cursor.execute(
                    "INSERT INTO Ingredient (ingredientName) VALUES (%s) ON DUPLICATE KEY UPDATE ingredientID=LAST_INSERT_ID(ingredientID)",
                    (ingredient,))
                ingredient_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO Recipe_Ingredient (recipeID, ingredientID, quantity, unit) VALUES (%s, %s, %s, %s)",
                    (recipe_id, ingredient_id, quantity, unit))

            db.commit()
            flash('Recipe added successfully!', 'success')
            return redirect(url_for('routes.get_recipes'))
        except mysql.connector.Error as err:
            db.rollback()
            flash(f"Database error: {err}", 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('recipes/edit_recipe.html', recipe=None, directions=[], ingredients=[])


@bp.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    current_user = session.get('user_id')
    try:
        # Check if the current user is the creator of the recipe
        cursor.execute("SELECT created_by FROM Recipe WHERE recipeID = %s", (recipe_id,))
        creator_id = cursor.fetchone()['created_by']
        if creator_id != current_user:
            flash('You are not authorized to edit this recipe', 'danger')
            return redirect(url_for('routes.get_recipes'))

        if request.method == 'POST':
            # Handle form submission to edit the recipe
            recipe_name = request.form.get('recipe_name')
            description = request.form.get('description')
            directions = request.form.getlist('directions[]')
            ingredients = request.form.getlist('ingredients[]')
            quantities = request.form.getlist('quantities[]')
            units = request.form.getlist('units[]')

            # Update recipe
            cursor.execute("UPDATE Recipe SET recipeName = %s, description = %s WHERE recipeID = %s",
                           (recipe_name, description, recipe_id))

            # Update directions
            cursor.execute("DELETE FROM Recipe_Direction WHERE recipeID = %s", (recipe_id,))
            for i, direction in enumerate(directions):
                cursor.execute(
                    "INSERT INTO Recipe_Direction (recipeID, instructionOrder, instruction) VALUES (%s, %s, %s)",
                    (recipe_id, i + 1, direction))

            # Update ingredients
            cursor.execute("DELETE FROM Recipe_Ingredient WHERE recipeID = %s", (recipe_id,))
            for ingredient, quantity, unit in zip(ingredients, quantities, units):
                cursor.execute(
                    "INSERT INTO Ingredient (ingredientName) VALUES (%s) ON DUPLICATE KEY UPDATE ingredientID=LAST_INSERT_ID(ingredientID)",
                    (ingredient,))
                ingredient_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO Recipe_Ingredient (recipeID, ingredientID, quantity, unit) VALUES (%s, %s, %s, %s)",
                    (recipe_id, ingredient_id, quantity, unit))

            db.commit()
            flash('Recipe updated successfully!', 'success')
            return redirect(url_for('routes.get_recipes'))
        else:
            # Load recipe details for editing
            cursor.execute("SELECT * FROM Recipe WHERE recipeID = %s", (recipe_id,))
            recipe = cursor.fetchone()

            cursor.execute("SELECT * FROM Recipe_Direction WHERE recipeID = %s ORDER BY instructionOrder", (recipe_id,))
            directions = cursor.fetchall()

            cursor.execute("""
                SELECT i.ingredientName, ri.quantity, ri.unit
                FROM Recipe_Ingredient ri
                JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE ri.recipeID = %s
            """, (recipe_id,))
            ingredients = cursor.fetchall()

            return render_template('recipes/edit_recipe.html', recipe=recipe, directions=directions,
                                   ingredients=ingredients)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('routes.get_recipes'))

    finally:
        cursor.close()
        db.close()


# Delete Recipe
@bp.route('/my_recipes/delete/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Check if the user is the creator of the recipe
        cursor.execute('SELECT created_by FROM Recipe WHERE recipeID = %s', (recipe_id,))
        recipe = cursor.fetchone()

        if not recipe:
            flash('Recipe not found.', 'danger')
            return redirect(url_for('routes.my_recipes'))

        if 'user_id' not in session or recipe['created_by'] != session['user_id']:
            flash('You are not authorized to delete this recipe.', 'danger')
            return redirect(url_for('routes.my_recipes'))

        # Delete the recipe
        cursor.execute('DELETE FROM Recipe WHERE recipeID = %s', (recipe_id,))
        db.commit()

        flash('Recipe deleted successfully!', 'success')
        return redirect(url_for('routes.my_recipes'))

    except (mysql.connector.Error, KeyError, TypeError) as err:
        flash(f"Error deleting recipe: {err}", 'danger')

    finally:
        cursor.close()
        db.close()

    return redirect(url_for('routes.my_recipes'))


# Community
@bp.route('/community')
@login_required
def community():
    if not 'user_id' in session:
        return redirect(url_for('routes.login'))
    comments = get_threads_with_replies()
    return render_template('community.html', comments=comments)


@bp.route('/get_replies/<string:thread_id>', methods=['GET'])
@login_required
def get_replies(thread_id):
    db = get_mongo_db()
    try:
        replies = db.thread.find_one({'_id': ObjectId(thread_id)}, {'replies': 1})
        return jsonify({
            'success': True,
            'replies': replies['replies']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error fetching replies from database: {e}"
        }), 500


@bp.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    if not 'user_id' in session:
        return jsonify({'success': False, 'error': 'You need to be logged in to comment'}), 401

    db = get_mongo_db()

    data = request.get_json()
    comment_text = data.get('comment')

    try:
        if comment_text:
            db.thread.insert_one({
                'threadName': comment_text,
                'created_by': session.get('user_id'),
                'created_by_username': session.get('username'),
                'replies': [],
            })

            return jsonify({
                'success': True,
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid data'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error inserting into database: {e}"
        }), 500


@bp.route('/add_reply', methods=['POST'])
@login_required
def add_reply():
    if not 'user_id' in session:
        return jsonify({'success': False, 'error': 'You need to be logged in to reply'}), 401

    db = get_mongo_db()

    data = request.get_json()
    comment_index = data.get('comment_index')
    reply_text = data.get('reply')
    user_id = session.get('user_id')

    try:
        if comment_index is not None and reply_text and user_id:
            db.thread.update_one(
                {'_id': ObjectId(comment_index)},
                {'$push': {'replies': {'userID': user_id, 'user': session.get('username'), 'reply': reply_text}}}
            )
            return jsonify({
                'success': True,
                'reply': {'user': session.get('username'), 'reply': reply_text}
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid data'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error inserting into database: {e}"
        }), 500


@bp.route('/add_rating', methods=['POST'])
def add_rating():
    user = session.get('username', 'Anonymous')
    user_id = session.get('user_id')
    recipe_id = request.form.get('recipe_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment', None)

    if not user_id or not recipe_id or not rating:
        flash('Missing required data', 'danger')
        return redirect(url_for('routes.get_recipe_details', recipe_id=recipe_id))

    db = get_db()
    cursor = db.cursor()

    try:
        insert_query = "INSERT INTO Rating (userID, recipeID, rating, comment) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (user_id, recipe_id, rating, comment))
        db.commit()

        flash("Rating successfully added", 'success')
        return redirect(url_for('routes.get_recipe_details', recipe_id=recipe_id))

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('routes.get_recipe_details', recipe_id=recipe_id))

    finally:
        cursor.close()
        db.close()


@bp.route('/get_ratings/<int:recipeID>', methods=['GET'])
def get_ratings_by_recipe_id(recipeID):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "SELECT * FROM Rating WHERE recipeID = %s"
        cursor.execute(query, (recipeID,))
        ratings = cursor.fetchall()

        return jsonify({
            'success': True,
            'ratings': ratings
        }), 200

    except mysql.connector.Error as e:
        return jsonify({
            'success': False,
            'error': f"Error fetching ratings from database: {e}"
        }), 500
    finally:
        cursor.close()


@bp.route('/update_rating/<int:rating_id>', methods=['PUT'])
def update_rating(rating_id):
    db = get_db()
    cursor = db.cursor()

    data = request.get_json()
    user = session.get('username', 'Anonymous')
    user_id = session.get('user_id')
    rating = data.get('rating')
    comment = data.get('comment')

    # Validate input
    try:
        if user and rating is not None:
            # Check if the rating belongs to current user
            select_query = "SELECT userID FROM Rating WHERE ratingID = %s"
            cursor.execute(select_query, (rating_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Rating not found'
                }), 404

            rating_user_id = result[0]
            if rating_user_id != user_id:
                return jsonify({
                    'success': False,
                    'error': 'You are not authorized to update this rating'
                }), 403

            # Update the rating
            update_query = "UPDATE Rating SET rating = %s, comment = %s WHERE ratingID = %s"
            cursor.execute(update_query, (rating, comment, rating_id))
            db.commit()

            return jsonify({
                'success': True,
                'message': 'Rating updated successfully'
            }), 200

        else:
            return jsonify({
                'success': False,
                'error': 'Invalid Data'
            }), 400

    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error updating rating: {err}"
        }), 500

    finally:
        cursor.close()


@bp.route('/delete_rating/<int:rating_id>', methods=['DELETE'])
def delete_rating(rating_id):
    db = get_db()
    cursor = db.cursor()

    user_id = session.get('user_id')

    # Validate input
    try:
        if user_id:
            # Check if the rating belongs to current user
            select_query = "SELECT userID FROM Rating WHERE ratingID = %s"
            cursor.execute(select_query, (rating_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Rating not found'
                }), 404

            rating_user_id = result[0]

            if rating_user_id != user_id:
                return jsonify({
                    'success': False,
                    'error': 'You are not authorized to delete this rating'
                }), 403

            # Delete the rating
            delete_query = "DELETE FROM Rating WHERE ratingID = %s"
            cursor.execute(delete_query, (rating_id,))
            db.commit()

            return jsonify({
                'success': True,
                'message': 'Rating deleted successfully'
            }), 200

        else:
            return jsonify({
                'success': False,
                'error': 'User is not authenticated'
            }), 401

    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error deleting rating: {err}"
        }), 500

    finally:
        cursor.close()
