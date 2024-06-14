from flask import Flask, render_template, request, redirect, url_for, session, flash
import hashlib  # For hashing passwords

app = Flask(__name__)
app.secret_key = 'key'  # secret key for session management

# Mock user database (replace this with your actual user authentication logic)
users = {
    'admin': {'password': 'password', 'email': 'admin@example.com'}
}

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
    return render_template('community.html')

if __name__ == '__main__':
    app.run(debug=True)
