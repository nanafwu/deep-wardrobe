import numpy as np
from clothing_classifier import get_clothing_vector_model, get_img_vectors
from clothing_classifier import get_product_to_features, get_bottom_feature_indexes
from collections import defaultdict
import db.db as db
from sklearn.neighbors import NearestNeighbors
import cv2
import urllib.request
import matplotlib.pyplot as plt

from itertools import combinations


def list_product_categories():
    return [('womens-tops', 'Tops'),
            ('jeans', 'Jeans'),
            ('shorts', 'Shorts'),
            ('womens-pants', 'Pants'),
            ('skirts', 'Skirts'),
            ('dresses', 'Dresses'),
            ('sweaters', 'Sweaters'),
            ('sweatshirts', 'Sweatshirts'),
            ('jackets', 'Jackets'),
            ('womens-outerwear', 'Outerwear'),
            ('handbags', 'Handbags'),
            ('hats', 'Hats'),
            ('jewelry', 'Jewelry'),
            ('sunglasses', 'Sunglasses'),
            ('womens-shoes', 'Shoes')]


def map_product_categories():
    return {'womens-tops': 'Top',
            'jeans': 'Jean',
            'shorts': 'Shorts',
            'womens-pants': 'Pants',
            'skirts': 'Skirt',
            'dresses': 'Dress',
            'sweaters': 'Sweater',
            'sweatshirts': 'Sweatshirt',
            'jackets': 'Jacket',
            'womens-outerwear': 'Outerwear',
            'handbags': 'Handbag',
            'hats': 'Hat',
            'jewelry': 'Jewelry',
            'sunglasses': 'Sunglasses',
            'womens-shoes': 'Shoes'}


def get_product_collections():
    collection_products = db.get_collection_products()
    product_to_collections = defaultdict(set)
    collections_to_products = defaultdict(list)
    product_info = {}
    for cp in collection_products:
        collection_id = str(cp[0])
        product_id = str(cp[1])
        product_name = cp[4]
        product_category = cp[2]
        image_url = cp[5]
        p = {'product_id': product_id,
             'product_name': product_name,
             'category': product_category,
             'image_url': image_url}
        product_to_collections[product_id].add(collection_id)
        collections_to_products[collection_id].append(p)
        product_info[product_id] = p
    return product_to_collections, collections_to_products, product_info


def get_closest_products(
        input_features, model, index_to_prod_mapping, count=15):
    """Only allow one product at a time"""
    product_distances, product_indexes = model.kneighbors(
        input_features, count, return_distance=True)
    closest_product_ids = [index_to_prod_mapping[index]
                           for index in product_indexes[0]]
    return closest_product_ids, product_distances[0]


def get_product_category_to_type():
    return {'jeans': 'bottom',
            'shorts': 'bottom',
            'womens-pants': 'bottom',
            'skirts': 'bottom',
            'dresses': 'dress',
            'womens-tops': 'top',
            'sweaters': 'top',
            'sweatshirts': 'top',
            'jackets': 'coat',
            'womens-outerwear': 'coat',
            'handbags': 'accessories',
            'hats': 'accessories',
            'jewelry': 'accessories',
            'sunglasses': 'accessories',
            'womens-shoes': 'accessories'}


def is_valid_combo(types):
    is_invalid = (types.count('top') >= 2) or \
                 (types.count('bottom') >= 2) or \
                 (types.count('coat') >= 2) or \
                 (types.count('shoes') >= 2) or \
                 (types.count('dress') >= 2) or \
                 (types.count('accessories') > 2) or \
                 (types.count('dress') >= 1 and
                  types.count('bottom') >= 1) or \
                 (types.count('dress') >= 1 and
                  types.count('top') >= 1) or \
                 (types.count('accessories') == 1 and
                  len(types) == 2 and
                  types.count('top') == 1) or \
                 (types.count('accessories') >= 1 and
                  len(types) == 2 and
                  types.count('bottom') >= 1)

    return not is_invalid


def get_wardrobe_closest_collections(
        wardrobe_items, nn_model,
        index_to_prod_mapping,
        prod_to_collection_mapping, bottom_feature_indexes):
    """For every item in an wardrobe, get closest Shopstyle products
    used in curated collections and then corresponding collections"""
    wardrobe_closest = {}
    item_to_closest_prod_ids = defaultdict(list)
    for item in wardrobe_items:
        item_id = item['item_id']
        input_features = np.array(item['image_vector'])
        input_features_reduced = np.array(
            [np.delete(input_features, bottom_feature_indexes)])
        closest_prods, prod_dists = get_closest_products(
            input_features_reduced, nn_model,
            index_to_prod_mapping, count=500)
        collection_ids_for_item = {}
        item_to_closest_prod_ids[str(item_id)] = closest_prods
        for prod_id, dist in zip(closest_prods, prod_dists):
            if dist < 6:
                collection_ids = prod_to_collection_mapping.get(prod_id, [])
                for cid in collection_ids:
                    collection_ids_for_item[cid] = dist
        wardrobe_closest[item_id] = collection_ids_for_item
    return wardrobe_closest, item_to_closest_prod_ids


def get_wardrobe_combinations(wardrobe_items):
    """Get combinations of items in wardrobe"""
    category_to_types = get_product_category_to_type()
    combos2 = list(combinations(wardrobe_items, 2))
    combos3 = list(combinations(wardrobe_items, 3))
    combos4 = list(combinations(wardrobe_items, 4))
    all_combos = combos2 + combos3 + combos4
    valid_combos = []
    for combo in all_combos:
        combo_types = [category_to_types[p['category']] for p in combo]
        if is_valid_combo(combo_types):
            valid_combos.append(combo)
    return valid_combos


def display_images(image_paths):
    image_count = len(image_paths)
    fig, ax = plt.subplots(1, image_count, figsize=(image_count * 5, 4))

    if image_count == 1:
        image_file = image_paths[0]
        image = cv2.imread(image_file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        plt.imshow(image, interpolation='nearest')
        plt.axis("off")
    else:
        for i, image_file in enumerate(image_paths):
            image = cv2.imread(image_file)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            ax[i].imshow(image, interpolation='nearest')
            ax[i].axis("off")
    plt.show()


def display_url_images(image_urls):
    image_count = len(image_urls)

    if image_count == 1:
        image_url = image_urls[0]
        req = urllib.request.urlopen(image_url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(img)
        plt.axis("off")
    else:
        fig, ax = plt.subplots(1, image_count, figsize=(image_count * 5, 4))
        for i, image_url in enumerate(image_urls):
            req = urllib.request.urlopen(image_url)
            arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)
            # Correct BGR to RGB channel
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            ax[i].imshow(img)
            ax[i].axis("off")
    plt.show()


def display_product_images(product_ids):
    image_files = ['images/images_collection_products/' +
                   product_id + '.jpg' for product_id in product_ids]
    display_images(image_files)


def make_nn_model(prods_to_feats):
    """Return Nearest Neighbors model fitted on products
       in curated collections"""
    index_to_prod = {}
    prod_features = []
    for i, prod_feat in enumerate(prods_to_feats.items()):
        prod_id, feat = prod_feat
        index_to_prod[i] = prod_id
        prod_features.append(feat[0])
    prod_features = np.array(prod_features)
    print('Making Nearest Neighbors ...')
    nn_model = NearestNeighbors(n_neighbors=500, metric='l2', algorithm='auto')
    nn_model.fit(prod_features)
    return nn_model, index_to_prod


def get_wardrobe_combo_collections(valid_combos, items_to_collections):
    """Return collections that match a wardrobe combination most closely"""
    combo_to_closest_collections = {}
    for combo in valid_combos:
        combo_id = tuple([(str(item['item_id']), item['image_url'])
                          for item in combo])
        collection_matches = None
        collection_match_to_distance = {}
        for item in combo:
            item_id = item['item_id']
            collections_dists_for_item = items_to_collections[item_id]
            collections_for_item = set(collections_dists_for_item.keys())
            if collection_matches is None:
                collection_matches = collections_for_item
            else:
                collection_matches = set.intersection(
                    collection_matches, collections_for_item)

            # Find closest collections for combination
            for collection_id in collection_matches:
                coll_dist = collection_match_to_distance.get(
                    collection_id, 0) + collections_dists_for_item[collection_id]
                collection_match_to_distance[collection_id] = coll_dist
        # If there are matching collections
        if len(collection_matches) > 0:
            avg_collection_distances = []
            for coll_id in collection_matches:
                average_distance = collection_match_to_distance[
                    coll_id] / float(len(combo_id))
                # Maximum average distance
                if average_distance < 5.2:
                    avg_collection_distances.append(
                        (coll_id, average_distance))
            avg_collection_distances = sorted(
                avg_collection_distances, key=lambda tup: tup[1])
            # Map every combination to matching collections and distance
            combo_to_closest_collections[combo_id] = avg_collection_distances
    return combo_to_closest_collections


def get_sorted_combos(valid_combos, items_to_collections):
    closest_matches = get_wardrobe_combo_collections(
        valid_combos, items_to_collections)
    combo_to_closest_coll = []
    matched_item_ids = set([])
    for combo_id, matching_collections in closest_matches.items():
        if len(matching_collections) > 0:
            item_ids = [i[0] for i in combo_id]
            matched_item_ids = matched_item_ids | set(item_ids)
            sorted_matching_colls = sorted(
                matching_collections, key=lambda tup: tup[1])
            # Store closest collection for each combination
            combo_to_closest_coll.append([combo_id, sorted_matching_colls[0]])

    combo_to_closest_coll = sorted(
        combo_to_closest_coll, key=lambda tup: tup[1][1])
    return combo_to_closest_coll, matched_item_ids


def suggest_additional_products(
        items_to_collections, item_to_closest_prod_ids, excluded_item_ids,
        cols_to_prod, product_data):
    """Suggest more Shopstyle products to buy to complete the look"""
    item_to_missing_prods = {}
    for item_id, collections_dists_for_item in items_to_collections.items():
        item_id = str(item_id)
        if item_id not in excluded_item_ids:
            # Get collection with smallest distance
            sorted_collections = sorted(
                collections_dists_for_item.items(), key=lambda tup: tup[1])
            if len(sorted_collections) > 0:
                closest_collection_id = sorted_collections[0][0]
                closest_product_ids = set(item_to_closest_prod_ids[item_id])
                collection_products = cols_to_prod[closest_collection_id]
                collection_products_ids = [p['product_id']
                                           for p in collection_products]
                missing_product_ids = set(
                    collection_products_ids) - closest_product_ids
                missing_products = [product_data[pid]
                                    for pid in missing_product_ids]
                item_to_missing_prods[item_id] = (
                    closest_collection_id, missing_products)
    return item_to_missing_prods
