import importlib
import data_collection.db as db
from collections import defaultdict
from itertools import combinations
import csv
import random


def make_category_pair_map():
    product_combinations = [('dresses', 'jackets'),
                            ('dresses', 'womens-outerwear'),
                            ('dresses', 'sweaters'),
                            ('jeans', 'jackets'),
                            ('jeans', 'womens-outerwear'),
                            ('jeans', 'sweaters'),
                            ('jeans', 'sweatshirts'),
                            ('jeans', 'womens-tops'),
                            ('womens-pants', 'jackets'),
                            ('womens-pants', 'womens-outerwear'),
                            ('womens-pants', 'sweaters'),
                            ('womens-pants', 'sweatshirts'),
                            ('womens-pants', 'womens-tops'),
                            ('shorts', 'jackets'),
                            ('shorts', 'womens-outerwear'),
                            ('shorts', 'sweaters'),
                            ('shorts', 'sweatshirts'),
                            ('shorts', 'womens-tops'),
                            ('skirts', 'jackets'),
                            ('skirts', 'womens-outerwear'),
                            ('skirts', 'sweaters'),
                            ('skirts', 'sweatshirts'),
                            ('skirts', 'womens-tops'),
                            ('sweaters', 'womens-outerwear'),
                            ('sweaters', 'jackets'),
                            ('sweatshirts', 'womens-outerwear'),
                            ('sweatshirts', 'jackets'),
                            ('womens-tops', 'womens-outerwear'),
                            ('womens-tops', 'sweaters'),
                            ('womens-tops', 'sweatshirts'),
                            ('womens-tops', 'jackets')]
    category_pair = defaultdict(set)
    for combo in product_combinations:
        category_pair[combo[0]].add(combo[1])
        category_pair[combo[1]].add(combo[0])

    return category_pair


def make_invalid_category_pair_map():
    invalid_combinations = [('dresses', 'jeans'),
                            ('dresses', 'womens-pants'),
                            ('dresses', 'shorts'),
                            ('dresses', 'skirts'),
                            ('dresses', 'womens-tops'),
                            ('dresses', 'dresses'),
                            ('jeans', 'womens-pants'),
                            ('jeans', 'shorts'),
                            ('jeans', 'skirts'),
                            ('jeans', 'jeans'),
                            ('shorts', 'womens-pants'),
                            ('shorts', 'skirts'),
                            ('shorts', 'shorts'),
                            ('skirts', 'skirts'),
                            ('skirts', 'womens-pants'),
                            ('womens-pants', 'womens-pants'),
                            ('sweaters', 'sweaters'),
                            ('sweatshirts', 'sweatshirts'),
                            ('womens-tops', 'womens-tops'),
                            ('jackets', 'jackets'),
                            ('womens-outerwear', 'womens-outerwear')]
    return invalid_combinations


def is_valid_combination(valid_pairs, item1_type, item2_type):
    is_match = item2_type in valid_pairs[item1_type]
    return is_match


def generate_invalid_pairs(number_pairs):
    invalid_pairs = make_invalid_category_pair_map()
    total = len(invalid_pairs)  # 21
    categories = ['dresses', 'jeans', 'jackets', 'womens-outerwear',
                  'womens-pants', 'shorts', 'skirts', 'sweaters',
                  'sweatshirts', 'womens-tops']

    category_to_product_ids = {}
    for category in categories:
        category_to_product_ids[
            category] = db.get_product_images_by_category(category)

    invalid_product_pairs = []
    products_used = set([])
    for i in range(number_pairs):
        # rotate amongst invalid combinations
        curr_invalid_combo = invalid_pairs[i % total]
        item1_type = curr_invalid_combo[0]
        item2_type = curr_invalid_combo[1]
        item1_product_id = random.choice(
            category_to_product_ids[item1_type])[0]
        item2_product_id = random.choice(
            category_to_product_ids[item2_type])[0]
        products_used.add(item1_product_id)
        products_used.add(item2_product_id)

        invalid_product_pairs.append(
            ('invalid_collection',
             item1_product_id, item1_type,
             item2_product_id, item2_type))

    random.shuffle(invalid_product_pairs)
    return invalid_product_pairs, products_used


def get_product_pairs():
    """
    For every collection, get possible pairs of products
    """
    valid_pairs = make_category_pair_map()
    collection_to_products = defaultdict(list)
    collection_products_db = db.get_collection_products()
    for row in collection_products_db:
        prod_and_category = (row[1], row[2])
        collection_to_products[row[0]].append(prod_and_category)

    product_pairs = []
    products_used = set([])
    for collection_id, collection_products in collection_to_products.items():
        # print('collection {}: {}'.format(collection_id, collection_products))
        product_combinations = combinations(collection_products, 2)
        for combo in product_combinations:
            item1_product_id = combo[0][0]
            item2_product_id = combo[1][0]
            item1_type = combo[0][1]
            item2_type = combo[1][1]
            if is_valid_combination(valid_pairs, item1_type, item2_type):
                products_used.add(item1_product_id)
                products_used.add(item2_product_id)

                product_pairs.append(
                    (collection_id,
                     item1_product_id, item1_type,
                     item2_product_id, item2_type))

    random.shuffle(product_pairs)
    return product_pairs, products_used


def write_tsv(rows, file_path):
    with open(file_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for row in rows:
            writer.writerow(row)
            f.flush()


def main():
    product_pairs, products_used = get_product_pairs()
    number_valid_pairs = len(product_pairs)
    print('Found {} pairs of clothing in {} products'.format(
        number_valid_pairs, len(products_used)))

    # Get same number of invalid pairs
    invalid_product_pairs, invalid_products_used = generate_invalid_pairs(
        number_valid_pairs)

    products_used_rows = [[p] for p in products_used]
    invalid_products_used_rows = [[p] for p in invalid_products_used]

    print('Writing to TSVs')
    write_tsv(product_pairs, 'data-pairs/valid_clothing_pairs.tsv')
    write_tsv(list(products_used_rows), 'data-pairs/valid_product_ids.tsv')

    write_tsv(invalid_product_pairs, 'data-pairs/invalid_clothing_pairs.tsv')
    write_tsv(list(invalid_products_used_rows),
              'data-pairs/invalid_product_ids.tsv')

if __name__ == '__main__':
    main()
