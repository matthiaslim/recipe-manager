from flask import Flask, render_template, request, redirect, url_for, session, flash, request
import hashlib  # For hashing passwords

app = Flask(__name__)
app.secret_key = 'key'  # secret key for session management

# Mock user database (replace this with your actual user authentication logic)
users = {'admin': 'password'}
emails = {'admin': 'admin@example.com'} 

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
        if username in users and users[username] == password:
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
            users[username] = password
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
            user = {'username': username, 'email': emails.get(username), 'password': users[username]}
            return render_template('profile.html', user=user)
    return redirect(url_for('login'))

# Edit Profile
@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
    if 'username' in session:
        username = session['username']
        if request.method == 'POST':
            new_username = request.form['username']
            new_email = request.form['email']
            new_password = request.form['password']
            
            # Update user data if fields are not empty
            if new_username:
                users[username]['username'] = new_username
                session['username'] = new_username  # Update session with new username
            if new_email:
                users[username]['email'] = new_email
            if new_password:
                users[username]['password_hash'] = hashlib.sha256(new_password.encode()).hexdigest()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        # Pass current user data to edit profile form
        user = {'username': username, 'email': users[username]['email']}
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