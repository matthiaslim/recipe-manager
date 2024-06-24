from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_paginate import Pagination, get_page_parameter
import mysql.connector
import os
from bcrypt import hashpw, gensalt, checkpw
from db import get_db
from config import Config
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from config.py
app.secret_key = os.urandom(24)  # secret key for session management

# Dummy data for community comments
comments = []


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def get_threads_with_replies(search_query=None):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        if search_query:
            cursor.execute(
                'SELECT t.threadID, t.threadName, u.userName, t.reply_count FROM temp_thread_with_replies t INNER JOIN User u ON t.thread_created_by = u.userID WHERE t.threadName LIKE %s',
                ('%' + search_query + '%',))
        else:
            cursor.execute(
                'SELECT t.threadID, t.threadName, u.userName, t.reply_count FROM temp_thread_with_replies t INNER JOIN User u ON t.thread_created_by = u.userID')
        fetched_comments = cursor.fetchall()
        comments_list = []
        for comment in fetched_comments:
            comment_dict = {
                'threadID': comment['threadID'],
                'threadName': comment['threadName'],
                'created_by': comment.get('userName', 'Unknown'),  # Corrected from 'username' to 'userName'
                'count': comment.get('reply_count', 0),
                'replies': []
            }
            comments_list.append(comment_dict)

        return comments_list

    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error fetching comments from database: {err}"
        }), 500

    finally:
        cursor.close()
        db.close()


# comments = get_threads_with_replies() # get all the threads

# comments = [
#     {
#         'user': 'user1',
#         'comment': 'Hellooo in general, how long does it take to make Nasi lemak?',
#         'replies': [
#             {'user': 'user2', 'reply': 'It usually takes about 2 hours.'},
#             {'user': 'user3', 'reply': 'I think it depends on the recipe.'}
#         ]
#     },
#     {
#         'user': 'user2',
#         'comment': 'Any recipes on how to make Army stew?',
#         'replies': [
#             {'user': 'user1', 'reply': 'Yes, I have one. I will share it later.'}
#         ]
#     },
#     {
#         'user': 'user3',
#         'comment': 'Hihi, I\'m using a toaster instead of an oven to bake cookies, any idea on how long should I bake it for?',
#         'replies': [
#             {'user': 'user4', 'reply': 'Try baking for 15 minutes and check.'}
#         ]
#     },
#     {
#         'user': 'user4',
#         'comment': 'Difference between condensed milk and evaporated milk? Does it really affect?',
#         'replies': [
#             {'user': 'user3', 'reply': 'Yes, condensed milk is sweetened while evaporated milk is not.'},
#             {'user': 'user2', 'reply': 'They have different uses in recipes.'}
#         ]
#     }
# ]

# Context processor to inject `user_logged_in` and `username` into templates
@app.context_processor
def inject_user():
    return dict(user_logged_in='username' in session, username=session.get('username'))


# Index
@app.route('/')
def index():
    return render_template('index.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
                return redirect(url_for('login'))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'danger')

        finally:
            cursor.close()
            db.close()

    return render_template('login.html')


# Register
@app.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('register'))

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
                # flash('Registration successful!', 'success')
                return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('register.html')


# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# Profile
@app.route('/profile')
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
    return redirect(url_for('login'))


# Change Password
@app.route('/profile/change_password', methods=['GET', 'POST'])
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
                        return redirect(url_for('profile'))
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

    return redirect(url_for('login'))


# Recipe CRUD
# Get all recipes
@app.route('/recipes')
def get_recipes():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        # Get current page number
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 5  # Number of recipes per page
        offset = (page - 1) * per_page

        # Fetch total number of recipes
        cursor.execute('SELECT COUNT(*) as total FROM Recipe')
        total = cursor.fetchone()['total']

        # Fetch recipes for the current page
        cursor.execute(
            'SELECT r.recipeID, r.recipeName, r.description, u.username '
            'FROM Recipe r JOIN User u ON r.created_by = u.userID '
            'LIMIT %s OFFSET %s',
            (per_page, offset)
        )
        recipes = cursor.fetchall()

        # Create pagination object
        pagination = Pagination(page=page, total=total, per_page=per_page, css_framework='bootstrap4')

        return render_template('recipes.html', recipes=recipes, pagination=pagination)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')

    finally:
        cursor.close()
        db.close()


@app.route('/search_by_ingredient', methods=['POST'])
def search_by_ingredient():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Get input data from form
        ingredients_input = request.form.get('ingredients', '').strip()
        search_option = request.form.get('search_option', 'only_listed')

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
            """.format(' AND '.join(['LOWER(i.ingredientName) LIKE %s'] * len(ingredients_list)), len(ingredients_list))

            # Adjust ingredients_list for LIKE operation
            ingredients_list = ['%' + ingredient + '%' for ingredient in ingredients_list]

        elif search_option == 'with_more':
            # Search for recipes containing any of the listed ingredients
            select_recipes_query = """
                SELECT DISTINCT r.*
                FROM Recipe r
                JOIN Recipe_Ingredient ri ON r.recipeID = ri.recipeID
                JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE {}
            """.format(' OR '.join(['LOWER(i.ingredientName) LIKE %s'] * len(ingredients_list)))

            # Adjust ingredients_list for LIKE operation
            ingredients_list = ['%' + ingredient + '%' for ingredient in ingredients_list]

        # Execute the query with adjusted ingredients_list
        cursor.execute(select_recipes_query, ingredients_list)
        recipes = cursor.fetchall()

        if not recipes:
            flash('No recipes found for the specified ingredients.', 'info')
            return render_template('search_by_ingredient.html', recipes=[])

        return render_template('search_by_ingredient.html', recipes=recipes)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('get_recipes'))

    finally:
        cursor.close()
        db.close()


# Get Recipe
@app.route('/recipes/<int:recipe_id>')
def get_recipe_details(recipe_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Get recipe details
        cursor.execute(
            'SELECT r.*, u.username FROM Recipe r JOIN User u ON r.created_by = u.userID WHERE r.recipeID = %s',
            (recipe_id,))
        recipe = cursor.fetchone()

        if not recipe:
            flash('Recipe not found', 'danger')
            return redirect(url_for('recipes'))

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

        return render_template('recipe_details.html', recipe=recipe, ingredients=ingredients, directions=directions,
                               ratings=ratings)

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        return redirect(url_for('recipes'))

    finally:
        cursor.close()
        db.close()


# My Recipes Page
@app.route('/my_recipes', methods=['GET', 'POST'])
@login_required
def my_recipes():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    user_id = session.get('user_id')

    try:
        if request.method == 'POST':
            search_term = request.form.get('search_term', '')
            page = request.args.get('page', 1, type=int)
        else:
            search_term = request.args.get('search_term', '')
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

        # Calculate the total number of pages
        total_pages = (total_count + per_page - 1) // per_page

        # Create pagination object
        pagination = Pagination(page=page, total=total_count, per_page=per_page, search=search_term,
                                css_framework='bootstrap4')

        return render_template('my_recipes.html', recipes=recipes, page=page, total_count=total_count,
                               total_pages=total_pages, search_term=search_term, pagination=pagination)

    except (mysql.connector.Error, KeyError, TypeError) as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('index'))

    finally:
        cursor.close()
        db.close()


# Create Recipe
@app.route('/recipes/create', methods=['GET', 'POST'])
@login_required
def create_recipe():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        try:
            recipe_name = request.form['recipe_name']
            description = request.form['description']
            created_by = session['user_id']

            # Insert recipe
            cursor.execute(
                'INSERT INTO Recipe (recipeName, description, created_by) VALUES (%s, %s, %s)',
                (recipe_name, description, created_by)
            )
            recipe_id = cursor.lastrowid

            # Insert directions
            directions = request.form.getlist('directions[]')
            for order, direction in enumerate(directions, start=1):
                cursor.execute(
                    'INSERT INTO Recipe_Direction (recipeID, instructionOrder, instruction) VALUES (%s, %s, %s)',
                    (recipe_id, order, direction)
                )

            # Insert ingredients
            ingredients = request.form.getlist('ingredients[]')
            quantities = request.form.getlist('quantities[]')
            units = request.form.getlist('units[]')

            for ingredient, quantity, unit in zip(ingredients, quantities, units):
                # Check if ingredient already exists
                cursor.execute(
                    'SELECT ingredientID FROM Ingredient WHERE LOWER(ingredientName) = %s',
                    (ingredient.strip().lower(),)
                )
                existing_ingredient = cursor.fetchone()

                if existing_ingredient:
                    ingredient_id = existing_ingredient[0]
                else:
                    # Insert new ingredient
                    cursor.execute(
                        'INSERT INTO Ingredient (ingredientName) VALUES (%s)',
                        (ingredient,)
                    )
                    ingredient_id = cursor.lastrowid

                # Insert into Recipe_Ingredient table
                cursor.execute(
                    'INSERT INTO Recipe_Ingredient (recipeID, ingredientID, quantity, unit) VALUES (%s, %s, %s, %s)',
                    (recipe_id, ingredient_id, quantity, unit)
                )

            db.commit()

            flash('Recipe created successfully!', 'success')
            return redirect(url_for('get_recipes'))  # Redirect to a page where recipes are listed

        except mysql.connector.Error as err:
            db.rollback()
            flash(f"Error creating recipe: {err}", 'danger')
            return redirect(url_for('create_recipe'))

        finally:
            cursor.close()
            db.close()

    # Render the form if it's a GET request or if there was an error
    return render_template('add_recipe.html')


@app.route('/my_recipes/edit/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check if the user is the creator of the recipe
    cursor.execute('SELECT created_by FROM Recipe WHERE recipeID = %s', (recipe_id,))
    recipe = cursor.fetchone()
    if not recipe or recipe['created_by'] != session['user_id']:
        flash('You are not authorized to edit this recipe.', 'danger')
        return redirect(url_for('my_recipes'))

    try:
        if request.method == 'POST':
            # Handle form submission to update recipe
            recipe_name = request.form['recipe_name']
            description = request.form['description']
            directions = request.form.getlist('directions[]')
            ingredients = request.form.getlist('ingredients[]')
            quantities = request.form.getlist('quantities[]')
            units = request.form.getlist('units[]')

            # Update recipe details in Recipe table
            cursor.execute(
                'UPDATE Recipe SET recipeName=%s, description=%s WHERE recipeID=%s',
                (recipe_name, description, recipe_id)
            )

            # Delete old directions for the recipe
            cursor.execute('DELETE FROM Recipe_Direction WHERE recipeID = %s', (recipe_id,))

            # Insert new directions into Recipe_Direction table
            for i, direction in enumerate(directions):
                cursor.execute(
                    'INSERT INTO Recipe_Direction (recipeID, instructionOrder, instruction) VALUES (%s, %s, %s)',
                    (recipe_id, i + 1, direction)
                )

            # Delete old ingredients for the recipe
            cursor.execute('DELETE FROM Recipe_Ingredient WHERE recipeID = %s', (recipe_id,))

            # Insert or update Recipe_Ingredient entries
            for i in range(len(ingredients)):
                ingredient_name = ingredients[i]
                quantity = quantities[i]
                unit = units[i]

                # Check if ingredientName exists in Ingredient table
                cursor.execute(
                    'SELECT ingredientID FROM Ingredient WHERE LOWER(ingredientName) = %s',
                    (ingredient_name.strip().lower(),)
                )
                existing_ingredient = cursor.fetchone()

                if existing_ingredient:
                    # If ingredient exists, use its ingredientID
                    ingredient_id = existing_ingredient['ingredientID']
                else:
                    # If ingredient does not exist, insert it into Ingredient table
                    cursor.execute(
                        'INSERT INTO Ingredient (ingredientName) VALUES (%s)',
                        (ingredient_name,)
                    )
                    db.commit()
                    ingredient_id = cursor.lastrowid  # Get the last inserted ID

                # Insert into Recipe_Ingredient table
                cursor.execute(
                    'INSERT INTO Recipe_Ingredient (recipeID, ingredientID, quantity, unit) VALUES (%s, %s, %s, %s)',
                    (recipe_id, ingredient_id, quantity, unit)
                )

            db.commit()
            flash('Recipe updated successfully!', 'success')
            return redirect(url_for('my_recipes'))

        else:
            # Fetch current recipe details for the form
            cursor.execute('SELECT * FROM Recipe WHERE recipeID = %s', (recipe_id,))
            recipe = cursor.fetchone()

            cursor.execute('''
                SELECT instructionOrder, instruction
                FROM Recipe_Direction
                WHERE recipeID = %s
                ORDER BY instructionOrder
            ''', (recipe_id,))
            directions = cursor.fetchall()

            cursor.execute('''
                SELECT ri.quantity, ri.unit, i.ingredientName
                FROM Recipe_Ingredient ri
                INNER JOIN Ingredient i ON ri.ingredientID = i.ingredientID
                WHERE ri.recipeID = %s
            ''', (recipe_id,))
            ingredients = cursor.fetchall()

            return render_template('edit_recipe.html', recipe=recipe, directions=directions, ingredients=ingredients)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('my_recipes'))

    finally:
        cursor.close()
        db.close()


# Delete Recipe
@app.route('/my_recipes/delete/<int:recipe_id>', methods=['POST'])
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
            return redirect(url_for('my_recipes'))

        if 'user_id' not in session or recipe['created_by'] != session['user_id']:
            flash('You are not authorized to delete this recipe.', 'danger')
            return redirect(url_for('my_recipes'))

        # Delete the recipe
        cursor.execute('DELETE FROM Recipe WHERE recipeID = %s', (recipe_id,))
        db.commit()

        flash('Recipe deleted successfully!', 'success')
        return redirect(url_for('my_recipes'))

    except (mysql.connector.Error, KeyError, TypeError) as err:
        flash(f"Error deleting recipe: {err}", 'danger')

    finally:
        cursor.close()
        db.close()

    return redirect(url_for('my_recipes'))


# Community
@app.route('/community')
def community():
    global comments
    comments = get_threads_with_replies()
    return render_template('community.html', comments=comments)


@app.route('/get_replies/<int:thread_id>', methods=['GET'])
def get_replies(thread_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('SELECT replyText, created_by FROM Reply WHERE threadID = %s', (thread_id,))
        replies = cursor.fetchall()

        return jsonify({
            'success': True,
            'replies': [{'user': reply[0], 'reply': reply[1]} for reply in replies]
        })

    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error fetching replies from database: {err}"
        }), 500

    finally:
        cursor.close()


@app.route('/add_comment', methods=['POST'])
def add_comment():
    db = get_db()
    cursor = db.cursor()

    global comments
    data = request.get_json()
    comment_text = data.get('comment')

    # Assuming you have a user in the session
    user = session.get('username', 'Anonymous')
    user_id = session.get('user_id')

    try:
        if comment_text and user:
            # Insert thread into Thread table
            insert_query = "INSERT INTO Thread (threadName, created_by) VALUES (%s, %s)"
            cursor.execute(insert_query, (comment_text, user_id))
            db.commit()

            thread_id = cursor.lastrowid

            new_comment = {
                'threadID': thread_id,
                'threadName': comment_text,
                'created_by': user_id,
                'count': 0,
                'replies': []
            }
            comments.append(new_comment)

            return jsonify({
                'success': True,
                'comment': new_comment
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid data'
            }), 400
    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error inserting into database: {err}"
        }), 500

    finally:
        cursor.close()


@app.route('/add_reply', methods=['POST'])
def add_reply():
    db = get_db()
    cursor = db.cursor()

    global comments
    data = request.get_json()
    comment_index = data.get('comment_index')
    reply_text = data.get('reply')

    # Assuming you have a user in the session
    user = session.get('username', 'Anonymous')
    user_id = session.get('user_id')

    try:
        if comment_index is not None and reply_text and user:
            try:
                comment_index = int(comment_index)
                thread_id = comments[comment_index]['threadID']
                insert_query = "INSERT INTO Reply (threadID, replyText, created_by) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (thread_id, reply_text, user_id))
                db.commit()
                # reply_id = cursor.lastrowid

                # Insert reply into dictionary
                new_reply = {
                    'user': user_id,
                    'reply': reply_text
                }
                comments[comment_index]['replies'].append(new_reply)
                comments[comment_index]['count'] += 1

                return jsonify({
                    'success': True,
                    'reply': new_reply
                })
            except (IndexError, ValueError) as e:
                return jsonify({
                    'success': False,
                    'error': 'Invalid comment index'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid data'
            }), 400

    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error inserting into database: {err}"
        }), 500

    finally:
        cursor.close()


@app.route('/add_rating', methods=['POST'])
def add_rating():
    db = get_db()
    cursor = db.cursor()

    data = request.get_json()
    user = session.get('username', 'Anonymous')
    user_id = session.get('user_id')
    recipe_id = data.get('recipe_id')
    rating = data.get('rating')
    comment = data.get('comment', None)

    # Validate input
    try:
        if user and recipe_id and rating is not None:
            try:
                insert_query = "INSERT INTO Rating (userID, recipeID, rating, comment) VALUES (%s, %s, %s, %s)"
                cursor.execute(insert_query, (user_id, recipe_id, rating, comment))
                db.commit()

                rating_id = cursor.lastrowid

                return jsonify({
                    'success': True,
                    'rating_id': rating_id
                }), 200

            except mysql.connector.Error as err:
                return jsonify({
                    'success': False,
                    'error': f"Error inserting into database: {err}"
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid Data'
            }), 400
    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error inserting into database: {err}"
        }), 500
    finally:
        cursor.close()


@app.route('/get_ratings/<int:recipeID>', methods=['GET'])
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


@app.route('/update_rating/<int:rating_id>', methods=['PUT'])
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


@app.route('/delete_rating/<int:rating_id>', methods=['DELETE'])
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


if __name__ == '__main__':
    app.run(debug=True)
