from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import hashlib  # For hashing passwords

app = Flask(__name__)
app.secret_key = 'key'  # secret key for session management

# Mock user database (replace this with your actual user authentication logic)
users = {
    'admin': {'password': 'password', 'email': 'admin@example.com'}
}

# Dummy data for community comments
comments = [
    {
        'user': 'user1',
        'comment': 'Hellooo in general, how long does it take to make Nasi lemak?',
        'replies': [
            {'user': 'user2', 'reply': 'It usually takes about 2 hours.'},
            {'user': 'user3', 'reply': 'I think it depends on the recipe.'}
        ]
    },
    {
        'user': 'user2',
        'comment': 'Any recipes on how to make Army stew?',
        'replies': [
            {'user': 'user1', 'reply': 'Yes, I have one. I will share it later.'}
        ]
    },
    {
        'user': 'user3',
        'comment': 'Hihi, I\'m using a toaster instead of an oven to bake cookies, any idea on how long should I bake it for?',
        'replies': [
            {'user': 'user4', 'reply': 'Try baking for 15 minutes and check.'}
        ]
    },
    {
        'user': 'user4',
        'comment': 'Difference between condensed milk and evaporated milk? Does it really affect?',
        'replies': [
            {'user': 'user3', 'reply': 'Yes, condensed milk is sweetened while evaporated milk is not.'},
            {'user': 'user2', 'reply': 'They have different uses in recipes.'}
        ]
    }
]

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
        if username in users and users[username]['password'] == password:
            session['username'] = username  # Store username in session
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
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if username in users:
            flash('Username already exists. Please try a different one.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
        else:
            users[username] = {'password': password, 'email': email}
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

# Community
@app.route('/community')
def community():
    return render_template('community.html', comments=comments)

@app.route('/add_reply', methods=['POST'])
def add_reply():
    data = request.get_json()
    comment_index = data.get('comment_index')
    reply_text = data.get('reply')
    
    # Assuming you have a user in the session
    user = session.get('username', 'Anonymous')
    
    if comment_index is not None and reply_text:
        try:
            comment_index = int(comment_index)
            new_reply = {
                'user': user,
                'reply': reply_text
            }
            comments[comment_index]['replies'].append(new_reply)
            
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
        })

    
@app.route('/add_comment', methods=['POST'])
def add_comment():
    data = request.get_json()
    comment_text = data.get('comment')
    
    # Assuming you have a user in the session
    user = session.get('username', 'Anonymous')
    
    if comment_text:
        new_comment = {
            'user': user,
            'comment': comment_text,
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
        })

if __name__ == '__main__':
    app.run(debug=True)
