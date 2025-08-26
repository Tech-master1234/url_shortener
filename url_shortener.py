from flask import Flask, request, redirect, jsonify, render_template, url_for, flash
import sqlite3
import hashlib
import base64
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' # Replace with a strong secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = 'urls.db'

# Database Configuration
# DB_CONFIG = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'root',
#     'database': 'url'
# }

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DATABASE):
        return
    conn = get_db_connection()
    with open('schema.sql', mode='r') as f:
        conn.cursor().executescript(f.read())
    conn.commit()
    conn.close()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user_data = conn.execute("SELECT id, username, password FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['password'])
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        user_data = conn.execute("SELECT id, username, password FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['password'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Function to generate a short URL
def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash

# Serve the HTML form
@app.route('/')
def home():
    user_urls = []
    if current_user.is_authenticated:
        conn = get_db_connection()
        user_urls = conn.execute("SELECT long_url, short_url, clicks FROM url_mapping WHERE user_id = ?", (current_user.id,)).fetchall()
        conn.close()
    return render_template('index.html', user_urls=user_urls)

# Handle URL shortening
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    usage_limit_str = request.form.get('usage_limit')
    password = request.form.get('password')

    if not long_url:
        return redirect(url_for('home'))

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    usage_limit = None
    if usage_limit_str and usage_limit_str.isdigit():
        usage_limit = int(usage_limit_str)

    conn = get_db_connection()

    # Check if the long URL already exists for this user
    existing_entry = conn.execute("SELECT short_url FROM url_mapping WHERE long_url = ? AND user_id = ?", (long_url, current_user.id)).fetchone()

    if existing_entry:
        conn.close()
        short_url = existing_entry['short_url']
        flash(f"URL already shortened: <a href=\"{request.host_url}{short_url}\" target=\"_blank\">{request.host_url}{short_url}</a>", "error")
        return redirect(url_for('home'))

    # Generate new short URL
    short_url = generate_short_url(long_url)
    
    # Hash the password if it exists
    hashed_password = None
    if password:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    conn.execute("INSERT INTO url_mapping (long_url, short_url, user_id, usage_limit, password) VALUES (?, ?, ?, ?, ?)", 
                   (long_url, short_url, current_user.id, usage_limit, hashed_password))
    conn.commit()
    conn.close()
    flash(f"Shortened URL: <a href=\"{request.host_url}{short_url}\" target=\"_blank\">{request.host_url}{short_url}</a>", "success")
    return redirect(url_for('home'))



# Redirect shortened URLs
@app.route('/<short_url>', methods=['GET', 'POST'])
def redirect_url(short_url):
    conn = get_db_connection()
    entry = conn.execute("SELECT long_url, clicks, usage_limit, password FROM url_mapping WHERE short_url = ?", (short_url,)).fetchone()

    if not entry:
        conn.close()
        return redirect(url_for('home'))

    if entry['usage_limit'] is not None and entry['clicks'] >= int(entry['usage_limit']):
        conn.close()
        flash("Usage limit reached for this URL.", "error")
        return redirect(url_for('home'))

    if entry['password']:
        if request.method == 'POST':
            password = request.form.get('password')
            if check_password_hash(entry['password'], password):
                conn.execute("UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = ?", (short_url,))
                conn.commit()
                conn.close()
                return redirect(entry['long_url'])
            else:
                flash("Invalid password.", "error")
                return render_template('password.html', short_url=short_url)
        else:
            conn.close()
            return render_template('password.html', short_url=short_url)

    conn.execute("UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = ?", (short_url,))
    conn.commit()
    conn.close()
    return redirect(entry['long_url'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return redirect(url_for('register'))

        conn = get_db_connection()
        
        # Check if username already exists
        if conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            conn.close()
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user_data = conn.execute("SELECT id, username, password FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['id'], user_data['username'], user_data['password'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/my_urls')
@login_required
def my_urls():
    conn = get_db_connection()
    user_urls = conn.execute("SELECT long_url, short_url, clicks, usage_limit, password FROM url_mapping WHERE user_id = ?", (current_user.id,)).fetchall()
    conn.close()
    return render_template('my_urls.html', user_urls=user_urls)

@app.route('/delete/<short_url>', methods=['POST'])
@login_required
def delete_url(short_url):
    conn = get_db_connection()
    conn.execute("DELETE FROM url_mapping WHERE short_url = ? AND user_id = ?", (short_url, current_user.id))
    conn.commit()
    conn.close()
    flash("URL deleted successfully.", "success")
    return redirect(url_for('my_urls'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Run the Flask application
if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)