from keras.models import model_from_json, Model
from keras.preprocessing.image import img_to_array, load_img
from keras.applications.inception_v3 import preprocess_input
import numpy as np
import csv

WEIGHTS_PATH = 'model_files/inceptionv3_clothing_expanded_classifier.h5'
JSON_MODEL = 'model_files/incep_filter_clothing_expanded_classifier.json'
PRODUCT_FEATURES_FILE = 'data-outfits/products_features.tsv'


def load_model(weights_path, json_path):
    json_file = open(json_path, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)

    # load weights into new model
    loaded_model.load_weights(weights_path)
    print("Loaded model from disk")
    return loaded_model


def get_clothing_vector_model(weights_path=WEIGHTS_PATH,
                              json_model=JSON_MODEL):
    loaded_model = load_model(weights_path, json_model)
    loaded_model.layers.pop()  # Get rid of the classification layer
    last = loaded_model.layers[-1].output
    model = Model(loaded_model.input, last)
    return model


def image_preprocess(img_path):
    image = load_img(img_path, target_size=(299, 299))
    image = img_to_array(image)

    # our input image is now represented as a NumPy array of shape
    # (inputShape[0], inputShape[1], 3) however we need to expand the
    # dimension by making the shape (1, inputShape[0], inputShape[1], 3)
    # so we can pass it through thenetwork
    image = np.expand_dims(image, axis=0)

    # pre-process the image using the appropriate function based on the
    # model that has been loaded (i.e., mean subtraction, scaling, etc.)
    image = preprocess_input(image)
    return image


def get_classier_prediction(clothing_classifier, img_path):
    clothes_labels = ['dresses', 'handbags', 'hats', 'jackets', 'jeans',
                      'jewelry', 'shorts', 'skirts', 'sunglasses', 'sweaters',
                      'sweatshirts', 'womens-outerwear', 'womens-pants',
                      'womens-shoes', 'womens-tops']
    img = image_preprocess(img_path)
    preds = clothing_classifier.predict(img)[0]
    preds_labels = list(zip(clothes_labels, preds))
    preds_labels.sort(key=lambda p: p[1], reverse=True)
    return preds_labels


def get_img_vectors(model, img_path):
    img = image_preprocess(img_path)
    preds = model.predict(img)[0]
    return preds


def get_product_to_features(product_feats_file=PRODUCT_FEATURES_FILE,
                            number_features_to_keep=300):
    product_to_feats = {}
    rf_feature_import_file = 'rf_feat_import.dat'
    all_feat_importances = np.load(rf_feature_import_file)
    top_features = sorted(list(
        zip(range(0, 1024), all_feat_importances)),
        key=lambda tup: tup[1], reverse=True)
    bottom_feature_indexes = [f[0]
                              for f in top_features[number_features_to_keep:]]
    with open(product_feats_file, 'r') as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter='\t')
        for row in tsvreader:
            product_id = row[0]
            feats_stored = [float(n) for n in row[1:]]
            feats_reduced = np.delete(feats_stored, bottom_feature_indexes)
            feats = np.array([feats_reduced])
            product_to_feats[product_id] = feats
    return product_to_feats
