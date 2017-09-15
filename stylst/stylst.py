from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
import cnfg
import boto3
from clothing_classifier import get_clothing_vector_model
from clothing_classifier import get_img_vectors
from db.db import insert_wardrobe_item, make_db_conn, get_wardrobe_items
import os

# -------- GLOBAL VARIABLES --------
app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file, stylst.py

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

# -------- CLASSIFIER IN MEMORY --------
global model
global wardrobe  # hardcode wardrobe for now


def upload_file_to_s3(file, filename, bucket_name, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": 'image/jpeg'
            }
        )
    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format(config['s3']["S3_LOCATION"], filename)


@app.route("/upload", methods=["POST"])
def upload_file():

    if "user_file" not in request.files:
        return "No user_file key in request.files"

    file = request.files["user_file"]

    """
        file.filename               # The actual name of the file
        file.content_type
        file.content_length
        file.mimetype
    """
    if file.filename == "":
        return "Please select a file"

    if file:
        print('Uploading ..', session.keys())
        # file.filename = secure_filename(file.filename)
        s3bucket = config['s3']["S3_BUCKET"]

        # Save locally to make predictions
        filename = file.filename
        temp_dest = filename + ' .jpg'
        file.save(temp_dest)

        with open(temp_dest, 'rb') as data:
            image_url = upload_file_to_s3(data, filename, s3bucket)

        print('Uploaded image to', str(image_url))

        # img_vec = get_img_vectors(model, temp_dest)
        # img_vec = [i.item() for i in img_vec]
        img_vec = []
        print('PREDICTION: ', img_vec)

        conn = get_db()
        user_id = session['user']['user_id']
        insert_wardrobe_item(conn, user_id, image_url, img_vec)

        wardrobe.append({'url': image_url, 'vector': img_vec})
        os.remove(temp_dest)
        # redirect(url_for('show_wardrobe'))
        return render_template('show_wardrobe.html', wardrobe=wardrobe)

    else:
        # TODO: Show ERROR message
        return redirect(url_for('show_wardrobe'))


@app.route('/')
def show_wardrobe():
    print('wardrobe user: ', session.get('user', None))
    print(session.keys())
    return render_template('show_wardrobe.html', page='wardrobe', wardrobe=wardrobe)


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


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'postgres_db'):
        g.postgres_db = make_db_conn()
    return g.postgres_db


@app.before_first_request
def first_load():
    app.logger.info("Loading Clothing Classifier")
    global model
    global wardrobe
    # model = get_clothing_vector_model()
    conn = get_db()
    session['logged_in'] = True
    user_id = '5221de0a-cd0c-45a3-ac66-d1a6339ab446'
    wardrobe = get_wardrobe_items(conn, user_id)
    session.permanent = True
    session['user'] = {
        'user_id': user_id,
        'name': 'Nana'}  # hard code 1 user for now
    print('You were logged in')


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'postgres_db'):
        g.postgres_db.close()
