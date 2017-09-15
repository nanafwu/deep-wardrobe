from keras.models import model_from_json
from keras.preprocessing.image import img_to_array, load_img
from keras.applications.inception_v3 import preprocess_input
import numpy as np


def load_model(weights_path, json_path):
    json_file = open(json_path, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)

    # load weights into new model
    loaded_model.load_weights(weights_path)
    print("Loaded model from disk")
    return loaded_model


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


def get_clothing_classifier():
    clothing_classifier_weights_path = '../model_files/inceptionv3_clothing_expanded_classifier.h5'
    clothing_classifier_json_path = '../model_files/incep_filter_clothing_expanded_classifier.json'
    clothing_classifier = load_model(
        clothing_classifier_weights_path, clothing_classifier_json_path)
    return clothing_classifier


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
