from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import hashlib  # For hashing passwords
import mysql.connector # For database connection
from config import Config

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from config.py
app.secret_key = 'key'  # secret key for session management

# MySQL configurations
db = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)
cursor = db.cursor()

# Mock user database (replace this with your actual user authentication logic)
users = {}
# users = {
#     'admin': {'password': 'password', 'email': 'admin@example.com'}
# }

# Dummy data for community comments
comments = []

def get_threads_with_replies():
    try:
        cursor.execute('SELECT t.threadID, t.threadName, u.userName, t.reply_count FROM temp_thread_with_replies t INNER JOIN User u ON t.thread_created_by = u.userID')
        comments = cursor.fetchall()
        comments_list = []
        for comment in comments:
            comment_dict = {
                'threadID': comment[0],
                'threadName': comment[1],
                'created_by': comment[2],
                'count': comment[3],
                'replies': []
            }
            comments_list.append(comment_dict)
        
        return comments_list
    
    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f"Error fetching comments from database: {err}"
        }), 500

comments = get_threads_with_replies() # get all the threads

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
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username and password are correct
        cursor.execute('SELECT * FROM User WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()

        if user:
            user_id = user[0]  # userID is the first column
            session['username'] = username  # Store username in session
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if username already exists
        cursor.execute('SELECT * FROM User WHERE username = %s', (username,))
        if cursor.fetchone():
            flash('Username already exists. Please try a different one.', 'danger')

        # Insert new user into database
        else:
            if password != confirm_password:
                flash('Passwords do not match. Please try again.', 'danger')
            else:
                cursor.execute('INSERT INTO User (username, password) VALUES (%s, %s)', (username, password))
                db.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
    
    return render_template('register.html', error=error)

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('index'))

# Profile
@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        if username in users:
            user = users[username]
            return render_template('profile.html', user=user)
    return redirect(url_for('login'))

# Edit Profile
@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
    if 'username' in session:
        current_username = session['username']
        if request.method == 'POST':
            new_username = request.form['username']
            new_email = request.form['email']
            new_password = request.form['password']
            confirm_password = request.form['confirm_password']

            if new_password != confirm_password:
                flash('Passwords do not match. Please try again.', 'danger')
                return redirect(url_for('editProfile'))
            
            # Update user data if fields are not empty
            if new_username and new_username != current_username:
                users[new_username] = users.pop(current_username)
                users[new_username]['username'] = new_username
                session['username'] = new_username  # Update session with new username
            else:
                new_username = current_username

            if new_email:
                users[new_username]['email'] = new_email
            if new_password:
                users[new_username]['password'] = new_password
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        # Pass current user data to edit profile form
        user = users[current_username]
        return render_template('editProfile.html', user=user)
    
    return redirect(url_for('login'))

# Discover
@app.route('/discover')
def discover():
    return render_template('discover.html')

# Moredetails
@app.route('/moredetails')
def moredetails():
    return render_template('moredetails.html')

# Community
@app.route('/community')
def community():
    # comments = get_threads_with_replies()
    # print(comments)
    return render_template('community.html', comments=comments)

@app.route('/get_replies/<int:thread_id>', methods=['GET'])
def get_replies(thread_id):
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
                'replies': []
            }
            comments.append(new_comment)
            print(comments)
            
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
    
@app.route('/add_reply', methods=['POST'])
def add_reply():
    print(comments)
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
                comments[comment_index]['count']+=1
                
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
