import sqlite3
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for


# Set up Database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# Set up Flask and Hashids
app = Flask(__name__)
app.config['SECRET_KEY'] = 'this is not very secure'

hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])

# Code for Homepage
@app.route('/', methods=('GET', 'POST'))
def index():
    conn = get_db_connection()

    if request.method == 'POST':
        # User has submitted a URL to be shortened.
        url = request.form['url']

        if not url:
            # User has not actually included URL
            flash('Please input a URL.')
            return redirect(url_for('index'))

        # User has included URL, add URL to database.
        url_data = conn.execute('INSERT INTO urls (original_url) VALUES (?)',
                                (url,))
        conn.commit()
        conn.close()

        # Get ID for URL and encode with hashid
        url_id = url_data.lastrowid
        hashid = hashids.encode(url_id)
        short_url = request.host_url + hashid

        return render_template('index.html', short_url=short_url)

    # request.method == 'GET'
    return render_template('index.html')

# Code for Redirecting
@app.route('/<id>')
def url_redirect(id):
    conn = get_db_connection()

    # Retrieve original ID from hashed ID
    original_id = hashids.decode(id)
    if original_id:
        # Succesfully retrieved original ID
        original_id = original_id[0]
        url_data = conn.execute('SELECT original_url, clicks FROM urls'
                                ' WHERE id = (?)', (original_id,)).fetchone()
        original_url = url_data['original_url']
        clicks = url_data['clicks']
        # TODO: Add a way to handle false positives (managed to retrieve an ID
        # That does not exist in Database)

        # Increment clicks to keep track of visits
        conn.execute('UPDATE urls SET clicks = ? WHERE id = ?',
                     (clicks+1, original_id))

        conn.commit()
        conn.close()
        return redirect(original_url)
    else:
        flash('Invalid URL')
        return redirect(url_for('index'))

# Code for Statistics Page
@app.route('/stats')
def stats():
    conn = get_db_connection()
    db_urls = conn.execute('SELECT id, created, original_url, clicks FROM urls').fetchall()
    conn.close()

    urls = []
    for url in db_urls:
        url = dict(url)
        url['short_url'] = request.host_url + hashids.encode(url['id'])
        urls.append(url)

    return render_template('stats.html', urls=urls)
