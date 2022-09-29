import sqlite3
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
import os
import logging
from werkzeug.exceptions import abort

# Count all database connections
connection_count = 0


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    try:
        if os.path.exists("database.db"):
            global connection_count
            connection = sqlite3.connect('database.db')
            connection.row_factory = sqlite3.Row
            connection_count += 1
            return connection
        else:
            raise RuntimeError('Failed to open database')
    except sqlite3.OperationalError:
        logging.error('Please initialize database by using the python init_db.py command')


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


# Function to get all posts count
def get_posts_count():
    connection = get_db_connection()
    posts_count = connection.execute('SELECT COUNT(id) FROM posts').fetchone()[0]
    connection.close()
    return posts_count


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logging.error('Article with id {} does not exists'.format(post_id))
        return render_template('404.html'), 404
    else:
        logging.debug('Article {} retrieved'.format(post['title']))
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    logging.debug("About page rendered")
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()
            logging.debug('Article {} created'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


# Define the health check endpoint
@app.route('/healthz')
def healthcheck():
    try:
        connection = get_db_connection()
        connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        response = app.response_class(
            response=json.dumps({"result": "OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    except sqlite3.OperationalError:
        response = app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
        )

    logging.debug('Health check request successful')
    return response


# Define the metrics endpoint
@app.route('/metrics')
def metrics():
    response = app.response_class(
        response=json.dumps({"db_connection_count": connection_count, "post_count": get_posts_count()}),
        status=200,
        mimetype='application/json'
    )
    logging.debug('Metrics request successful')
    return response


# start the application on port 3111
if __name__ == "__main__":
    # stream logs to a file
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
