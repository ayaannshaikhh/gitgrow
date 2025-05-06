# import the necessary packages
from flask import Flask, request, session, redirect, url_for
from flask_github import GitHub
import os
import requests
import json
import mariadb

app = Flask(__name__)

app.config['GITHUB_CLIENT_ID'] = os.getenv("GITHUB_CLIENT_ID")
app.config['GITHUB_CLIENT_SECRET'] = os.getenv("GITHUB_CLIENT_SECRET")
app.config['GITHUB_CALLBACK_URL'] = "http://localhost:5000/callback"

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")

github = GitHub(app)

# configuration used to connect to MariaDB
config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'Password123!',
    'database': 'gitgrow'
}

def create_db():
    config_copy = config.copy()
    config_copy.pop("database")  # remove database from config
    connection = mariadb.connect(**config_copy)
    cursor = connection.cursor()
    cursor.execute("""CREATE DATABASE IF NOT EXISTS gitgrow""")
    connection.commit()
    connection.close()

def init_db():
    connection = mariadb.connect(**config)
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        github_id BIGINT UNIQUE,
        username VARCHAR(255),
        avatar_url TEXT
    )""")
    connection.commit()
    connection.close()

def store_user_in_db(user_data):
    connection = mariadb.connect(**config)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (github_id, username, avatar_url) VALUES (?, ?, ?)", 
                   (user_data['id'], user_data['login'], user_data['avatar_url']))
    connection.commit()
    connection.close()

@app.route('/callback')
@github.authorized_handler
def authorized(oauth_token):
    if oauth_token is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'], request.args['error_description']
        )

    print("OAuth Token:", oauth_token)

    user_data = github.get('user')
    print("User Data:", user_data) 

    store_user_in_db(user_data)
    return f"Welcome, {user_data['login']}!"

# Login page
@app.route('/login')
def login():
    return github.authorize()

@app.route('/profile')
def profile():
    if 'github_user' not in session:
        return redirect(url_for('login'))
    
    user_data = session['github_user']
    return f"Welcome, {user_data['login']}! <br> Avatar: <img src='{user_data['avatar_url']}' />"

# route to return all people
@app.route('/', methods=['GET'])
def index():
    return "hi"

if __name__ == '__main__':
    create_db()
    init_db()
    app.run(debug=True)