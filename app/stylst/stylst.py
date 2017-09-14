from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import cnfg
import boto3


app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

config = cnfg.load(".metis_config")

s3 = boto3.client(
    "s3",
    aws_access_key_id=config['s3']['S3_KEY'],
    aws_secret_access_key=config['s3']['S3_SECRET_ACCESS_KEY']
)


def upload_file_to_s3(file, bucket_name, acl="public-read"):
    """
    Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
    """

    try:

        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format(config['s3']["S3_LOCATION"], file.filename)


@app.route("/upload", methods=["POST"])
def upload_file():

    if "user_file" not in request.files:
        return "No user_file key in request.files"

    file = request.files["user_file"]

    """
        These attributes are also available

        file.filename               # The actual name of the file
        file.content_type
        file.content_length
        file.mimetype

    """
    if file.filename == "":
        return "Please select a file"

    if file:
        # file.filename = secure_filename(file.filename)
        s3bucket = config['s3']["S3_BUCKET"]
        output = upload_file_to_s3(file, s3bucket)
        print('Uploaded image to', str(output))
        return redirect(url_for('show_wardrobe'))

    else:
        # TODO: Show ERROR message
        return redirect(url_for('show_wardrobe'))


def init_db():
    """Initializes the database."""
    # db = get_db()
    print('initializing nothing ...')


def connect_db():
    """Connects to the specific database."""
    engine = create_engine('postgresql://{}:{}@{}:5432/{}'.format(
        config['db_user'],
        config['db_pwd'],
        config['db_host'],
        'shopstyle'))

    conn = engine.connect()
    return conn


@app.route('/')
def show_wardrobe():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template(
        'show_wardrobe.html',
        page='wardrobe', entries=entries)


@app.route('/style_suggestions', methods=['GET'])
def show_styled_suggestions():
    print('Show Styled Suggestions')
    return render_template('styled_suggestions.html', page='suggestions')


@app.route('/shop', methods=['GET'])
def show_shop():
    print('SHOP')
    return render_template('shop.html', page='shop')


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('/'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    print('request: ', request)
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_wardrobe'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_wardrobe'))


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'postgres_db'):
        g.postgres_db = connect_db()
    return g.postgres_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'postgres_db'):
        g.postgres_db.close()
