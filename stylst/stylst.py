from flask import Flask, request, g, redirect, url_for, render_template
import cnfg
import boto3
import wardrobe_recommender as rec
from clothing_classifier import get_clothing_vector_model, load_model
from clothing_classifier import get_img_vectors, get_classier_prediction
from clothing_classifier import get_product_to_features
from clothing_classifier import get_bottom_feature_indexes
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
global classifier
global user
global wardrobe
global prod_to_colls
global cols_to_prod
global product_data
global neighbors_model
global prods_to_feats
global index_to_prod
global bottom_feature_indexes


def sort_wardrobe(w):
    sorted_wardrobe = {}
    for item in w:
        wardrobe_category = item['category']
        curr_category = sorted_wardrobe.get(wardrobe_category, [])
        curr_category.append(item)
        sorted_wardrobe[wardrobe_category] = curr_category

    wardrobe_categories = []
    for category, display_name in rec.list_product_categories():
        wardrobe_cat = sorted_wardrobe.get(category, [])
        if len(wardrobe_cat) > 0:
            wardrobe_categories.append(
                [display_name, len(wardrobe_cat), wardrobe_cat])
    return wardrobe_categories


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

    if file.filename == "":
        return "Please select a file"

    if file:
        s3bucket = config['s3']["S3_BUCKET"]

        # Save locally to make predictions
        filename = file.filename
        temp_dest = filename + ' .jpg'
        file.save(temp_dest)

        with open(temp_dest, 'rb') as data:
            image_url = upload_file_to_s3(data, filename, s3bucket)

        print('Uploaded image to', str(image_url))

        category = get_classier_prediction(classifier, temp_dest)[0][0]
        img_vec = get_img_vectors(model, temp_dest)
        img_vec = [i.item() for i in img_vec]

        print('{} / clothing vector {} '.format(category, len(img_vec)))

        conn = get_db()
        user_id = user['user_id']
        new_item = insert_wardrobe_item(
            conn, user_id, image_url, img_vec, category)

        wardrobe.append(new_item)
        os.remove(temp_dest)

        return redirect(url_for('show_wardrobe'))

    else:
        # TODO: Show ERROR message
        return redirect(url_for('show_wardrobe'))


@app.route("/upload", methods=["GET"])
def show_upload():
    return render_template('upload.html', page='upload')


@app.route('/')
def show_wardrobe():
    return render_template('show_wardrobe.html', page='wardrobe',
                           wardrobe=sort_wardrobe(wardrobe), user=user)


@app.route('/style_suggestions', methods=['GET'])
def show_styled_suggestions():
    # Items to closest collections and product ids
    items_to_colls, item_to_prod_ids = rec.get_wardrobe_closest_collections(
        wardrobe, neighbors_model, index_to_prod, prod_to_colls,
        bottom_feature_indexes)

    valid_combos = rec.get_wardrobe_combinations(wardrobe)

    matching_collections, matched_wardrobe_item_ids = rec.get_sorted_combos(
        valid_combos, items_to_colls)

    suggested_combos = []
    outfit_counter = 1
    for combo_id, closest_collection in matching_collections:
        wardrobe_item_images = [c[1] for c in combo_id]
        closest_collection_id = closest_collection[0]
        collection_img = 'images_collections/' + closest_collection_id + '.jpg'
        suggested_combos.append(
            [outfit_counter, collection_img, wardrobe_item_images])
        outfit_counter += 1
    return render_template('styled_suggestions.html', page='suggestions',
                           suggested_combos=suggested_combos)


@app.route('/shop', methods=['GET'])
def show_shop():
    wardrobe_item_info = get_wardrobe_item_info()
    items_to_colls, item_to_prod_ids = rec.get_wardrobe_closest_collections(
        wardrobe, neighbors_model, index_to_prod, prod_to_colls,
        bottom_feature_indexes)

    item_to_missing_prods = rec.suggest_additional_products(
        items_to_colls, item_to_prod_ids, [],
        cols_to_prod, product_data)

    all_suggested_products = []
    for item_id, closest_coll in item_to_missing_prods.items():
        wardrobe_item = wardrobe_item_info[item_id]
        item_image_url = wardrobe_item['image_url']
        item_category = wardrobe_item['category']
        closest_collection_id = closest_coll[0]

        print('Closest collection: ', closest_collection_id, ', ', item_image_url)
        collection_img = '/images_collections/' + \
                         closest_collection_id + '.jpg'

        # Exclude any items from current category
        suggested_products = []
        suggested_product_categories = set()
        for p in closest_coll[1]:
            curr_category = p['category']
            # Suggest products in unique categories
            if (curr_category != item_category) and \
               (curr_category not in suggested_product_categories):
                suggested_product_categories.add(curr_category)
                suggested_products.append(p)

        all_suggested_products.append(
            [item_image_url, collection_img, suggested_products[:3]])

    return render_template('shop.html', page='shop',
                           suggested_products=all_suggested_products)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'postgres_db'):
        g.postgres_db = make_db_conn()
    return g.postgres_db


def get_wardrobe_item_info():
    wardrobe_item_info = {}
    for item in wardrobe:
        item_id = item['item_id']
        wardrobe_item_info[item_id] = item
    return wardrobe_item_info


@app.before_first_request
def first_load():
    app.logger.info("Loading Clothing Classifier")
    global model
    global wardrobe  # hardcode 1 wardrobe for now
    global user
    global classifier

    global prod_to_colls
    global cols_to_prod
    global product_data

    global neighbors_model
    global prods_to_feats
    global index_to_prod
    global bottom_feature_indexes

    # Initialize classifier and Vector Model
    model = get_clothing_vector_model()
    classifier = load_model()

    conn = get_db()
    user_id = '5221de0a-cd0c-45a3-ac66-d1a6339ab446'
    wardrobe = get_wardrobe_items(conn, user_id)
    user = {
        'user_id': user_id,
        'name': 'Nana'}  # hard code 1 user for now

    # Initialize Collection Product Features
    app.logger.info("Loading Collection Product Features")
    prod_to_colls, cols_to_prod, product_data = rec.get_product_collections()
    PRODUCT_FEATS_FILE = 'data-outfits/products_features.tsv'
    FEATURE_COUNT = 850
    bottom_feature_indexes = get_bottom_feature_indexes(
        number_features_to_keep=FEATURE_COUNT)

    # Load collection product features in memory
    prods_to_feats = get_product_to_features(
        product_feats_file=PRODUCT_FEATS_FILE,
        number_features_to_keep=FEATURE_COUNT)

    neighbors_model, index_to_prod = rec.make_nn_model(prods_to_feats)
    print('Done initializing...')


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'postgres_db'):
        g.postgres_db.close()

# export FLASK_APP=stylst
# export FLASK_DEBUG=true
