from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
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


def get_threads_with_replies():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT t.threadID, t.threadName, u.userName, t.reply_count FROM temp_thread_with_replies t INNER JOIN User u ON t.thread_created_by = u.userID')
        fetched_comments = cursor.fetchall()
        comments_list = []
        for comment in fetched_comments:
            comment_dict = {
                'threadID': comment['threadID'],
                'threadName': comment['threadName'],
                'created_by': comment['username'],
                'count': comment['reply_count'],
                'replies': []
            }
            comments_list.append(comment_dict)

        global comments
        comments = comments_list

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

            if checkpw(entered_password, user['password'].encode()):
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
                flash('Registration successful!', 'success')
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
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# Profile
# @app.route('/profile')
# def profile():
#     if 'username' in session:
#         username = session['username']
#         if username in users:
#             user = users[username]
#             return render_template('profile.html', user=user)
#     return redirect(url_for('login'))


# Edit Profile
# @app.route('/editProfile', methods=['GET', 'POST'])
# def editProfile():
#     if 'username' in session:
#         current_username = session['username']
#         if request.method == 'POST':
#             new_username = request.form['username']
#             new_email = request.form['email']
#             new_password = request.form['password']
#             confirm_password = request.form['confirm_password']
#
#             if new_password != confirm_password:
#                 flash('Passwords do not match. Please try again.', 'danger')
#                 return redirect(url_for('editProfile'))
#
#             # Update user data if fields are not empty
#             if new_username and new_username != current_username:
#                 users[new_username] = users.pop(current_username)
#                 users[new_username]['username'] = new_username
#                 session['username'] = new_username  # Update session with new username
#             else:
#                 new_username = current_username
#
#             if new_email:
#                 users[new_username]['email'] = new_email
#             if new_password:
#                 users[new_username]['password'] = new_password
#
#             flash('Profile updated successfully!', 'success')
#             return redirect(url_for('profile'))
#
#         # Pass current user data to edit profile form
#         user = users[current_username]
#         return render_template('editProfile.html', user=user)
#
#     return redirect(url_for('login'))


# Recipe CRUD
# Get all recipes
@app.route('/recipes')
@login_required
def get_recipes():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute('SELECT * FROM Recipe')
        recipes = cursor.fetchall()

        return render_template('recipes.html', recipes=recipes)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')

    finally:
        cursor.close()


# Get Recipe
@app.route('/recipes/<int:recipe_id>')
@login_required
def get_recipe_details(recipe_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute('SELECT * FROM Recipe WHERE recipeID = %s', (recipe_id,))
        recipe = cursor.fetchone()

        if recipe:
            return render_template('moredetails.html', recipe=recipe)
        else:
            return flash('Recipe not found', 'danger')

    except mysql.connector.Error as err:
        return flash(f"Database error: {err}", 'danger')

    finally:
        cursor.close()
        db.close()


# Create Recipe
@app.route('/recipes/create', methods=['POST'])
@login_required
def create_recipe():
    db = get_db()
    cursor = db.cursor()

    try:
        recipeName = request.form['recipeName']
        description = request.form['description']
        instruction = request.form['instruction']
        created_by = session.get('user_id')  # Assuming user is logged in

        cursor.execute(
            'INSERT INTO Recipe (recipeName, description, instruction, created_by) VALUES (%s, %s, %s, %s)',
            (recipeName, description, instruction, created_by)
        )
        db.commit()

        flash('Recipe created!', 'success')
        return redirect(url_for('get_recipes'))

    except mysql.connector.Error as err:
        flash('Error creating recipe: {err}', 'danger')
        return redirect(url_for('get_recipes'))

    finally:
        cursor.close()


# Update Recipe
@app.route('/recipe/update/<int:recipe_id>', methods=['POST'])
@login_required
def update_recipe(recipe_id):
    db = get_db()
    cursor = db.cursor()

    try:
        recipe_name = request.form['recipe_name']
        description = request.form['description']
        instruction = request.form['instruction']
        user_id = session.get('user_id')  # Assuming user is logged in

        # Fetch the creator of the recipe
        cursor.execute('SELECT created_by FROM Recipe WHERE recipeID = %s', (recipe_id,))
        recipe = cursor.fetchone()

        if recipe is None:
            flash('Recipe not found', 'danger')
            return redirect(url_for('discover'))

        creator_id = recipe['created_by']

        # Check if the current user is the creator of the recipe
        if user_id != creator_id:
            flash('You are not authorized to update this recipe', 'danger')
            return redirect(url_for('get_recipe_details', recipe_id=recipe_id))

        cursor.execute(
            'UPDATE Recipe SET recipeName=%s, description=%s, instruction=%s WHERE recipeID=%s',
            (recipe_name, description, instruction, recipe_id)
        )
        db.commit()

        flash('Recipe updated successfully', 'success')
        return redirect(url_for('get_recipe_details', recipe_id=recipe_id))

    except mysql.connector.Error as err:
        flash(f"Error updating recipe: {err}", 'danger')
        return redirect(url_for('get_recipe_details', recipe_id=recipe_id))

    finally:
        cursor.close()


# Delete Recipe
@app.route('/recipe/delete/<int:recipe_id>', methods=["POST"])
@login_required
def delete_recipe(recipe_id):
    db = get_db()
    cursor = db.cursor()

    try:
        user_id = session.get('user_id')  # Assuming user is logged in

        # Fetch the creator of the recipe
        cursor.execute('SELECT created_by FROM Recipe WHERE recipeID = %s', (recipe_id,))
        recipe = cursor.fetchone()

        if recipe is None:
            flash('Recipe not found', 'danger')
            return redirect(url_for('get_recipe_details', recipe_id=recipe_id))

        creator_id = recipe['created_by']

        # Check if the current user is the creator of the recipe
        if user_id != creator_id:
            flash('You are not authorized to delete this recipe', 'danger')
            return redirect(url_for('get_recipe_details', recipe_id=recipe_id))

        cursor.execute('DELETE FROM Recipe WHERE recipeID = %s', (recipe_id,))
        db.commit()

        flash('Recipe deleted successfully', 'success')
        return redirect(url_for('get_recipe_details', recipe_id=recipe_id))

    except mysql.connector.Error as err:
        flash(f"Error deleting recipe: {err}", 'danger')
        return redirect(url_for('get_recipe_details', recipe_id=recipe_id))

    finally:
        cursor.close()


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


# def get_threads_with_replies():
#     try:
#         cursor.execute('SELECT t.threadID, t.threadName, u.userName, t.reply_count FROM temp_thread_with_replies t INNER JOIN User u ON t.thread_created_by = u.userID')
#         comments = cursor.fetchall()
#         comments_list = []
#         for comment in comments:
#             comment_dict = {
#                 'threadID': comment[0],
#                 'threadName': comment[1],
#                 'created_by': comment[2],
#                 'count': comment[3],
#                 'replies': []
#             }
#             comments_list.append(comment_dict)

#         return comments_list

#     except mysql.connector.Error as err:
#         return jsonify({
#             'success': False,
#             'error': f"Error fetching comments from database: {err}"
#         }), 500

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


# def get_comments():
#     try:
#         cursor.execute('SELECT t.threadID, t.threadName, u.userName FROM Thread t INNER JOIN User u ON t.created_by = u.userID')
#         comments = cursor.fetchall()
#         comments_list = []
#         for comment in comments:
#             comment_dict = {
#                 'threadID': comment[0],
#                 'threadName': comment[1],
#                 'created_by': comment[2],
#                 'replies': []
#             }
#             comments_list.append(comment_dict)

#         return comments_list

#     except mysql.connector.Error as err:
#         return jsonify({
#             'success': False,
#             'error': f"Error fetching comments from database: {err}"
#         }), 500

if __name__ == '__main__':
    app.run(debug=True)
