import importlib
import data_collection.db as db
from collections import defaultdict
from itertools import combinations
import csv
import random


def make_jean_category_pair_map():
    return [('jeans', 'sweaters'),
            ('jeans', 'sweatshirts'),
            ('jeans', 'womens-tops')]


def make_valid_category_pair_map(more_jeans=False):
    jeans_categories = make_jean_category_pair_map()
    categories = [('dresses', 'jackets'),
                  ('womens-pants', 'jackets'),
                  ('womens-pants', 'sweaters'),
                  ('womens-pants', 'sweatshirts'),
                  ('womens-pants', 'womens-tops'),
                  ('skirts', 'sweaters'),
                  ('skirts', 'sweatshirts'),
                  ('skirts', 'womens-tops')
                  # ('shorts', 'jackets'),
                  # ('shorts', 'sweaters'),
                  # ('shorts', 'sweatshirts'),
                  # ('shorts', 'womens-tops'),
                  # ('skirts', 'jackets'),
                  # ('jeans', 'jackets'),
                  # ('sweaters', 'jackets'),
                  # ('sweatshirts', 'jackets'),
                  # ('womens-tops', 'jackets')
                  ]
    if more_jeans:
        return categories + jeans_categories * 2
    else:
        return categories


def make_category_pair_map(product_combinations):
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
                            ('jackets', 'jackets')]
    return invalid_combinations


def is_valid_combination(valid_pairs, item1_type, item2_type):
    is_match = item2_type in valid_pairs[item1_type]
    return is_match


def generate_random_pairs(pair_categories, number_pairs):
    total = len(pair_categories)
    categories = ['dresses', 'jeans', 'jackets',
                  'womens-pants', 'shorts', 'skirts', 'sweaters',
                  'sweatshirts', 'womens-tops']

    category_to_product_ids = {}
    for category in categories:
        category_to_product_ids[
            category] = db.get_product_images_by_category(category)

    product_pairs = []
    counter = 0
    for i in range(number_pairs):
        # rotate amongst invalid combinations
        curr_combo = pair_categories[i % total]
        item1_type = curr_combo[0]
        item2_type = curr_combo[1]
        item1 = random.choice(category_to_product_ids[item1_type])
        item2 = random.choice(category_to_product_ids[item2_type])
        item1_product_id = item1[0]
        item2_product_id = item2[0]
        item1_image = item1[1]
        item2_image = item2[1]

        product_pairs.append(
            (counter, 'invalid_collection',
             item1_product_id, item1_type, item1_image,
             item2_product_id, item2_type, item2_image))
        counter += 1

    # random.shuffle(product_pairs)
    return product_pairs


def get_fashionable_product_pairs():
    """
    For every collection, get possible pairs of products
    """
    valid_pairs = make_category_pair_map(make_valid_category_pair_map())
    jean_pairs = make_category_pair_map(make_jean_category_pair_map())

    collection_to_products = defaultdict(list)
    collection_products_db = db.get_collection_products()
    for row in collection_products_db:
        product_id = row[1]
        category = row[2]
        image_url = row[-1]
        p = (product_id, category, image_url)
        collection_to_products[row[0]].append(p)

    product_pairs = []
    counter = 0

    for collection_id, collection_products in collection_to_products.items():
        seen_categories = set([])
        leftover_combinations = []
        product_combinations = list(combinations(collection_products, 2))

        for combo in product_combinations:
            item1_product_id = combo[0][0]
            item2_product_id = combo[1][0]
            item1_type = combo[0][1]
            item2_type = combo[1][1]
            item1_image = combo[0][2]
            item2_image = combo[1][2]
            if is_valid_combination(valid_pairs, item1_type, item2_type) and \
               item1_type not in seen_categories and \
               item2_type not in seen_categories:

                seen_categories.add(item1_type)
                seen_categories.add(item2_type)
                product_pairs.append(
                    (counter, collection_id,
                     item1_product_id, item1_type, item1_image,
                     item2_product_id, item2_type, item2_image))
                counter += 1
            else:
                leftover_combinations.append(combo)

        for combo in leftover_combinations:
            item1_product_id = combo[0][0]
            item2_product_id = combo[1][0]
            item1_type = combo[0][1]
            item2_type = combo[1][1]
            item1_image = combo[0][2]
            item2_image = combo[1][2]
            if is_valid_combination(jean_pairs, item1_type, item2_type) and \
               item1_type not in seen_categories and \
               item2_type not in seen_categories:

                seen_categories.add(item1_type)
                seen_categories.add(item2_type)
                product_pairs.append(
                    (counter, collection_id,
                     item1_product_id, item1_type, item1_image,
                     item2_product_id, item2_type, item2_image))
                counter += 1

    # random.shuffle(product_pairs)
    return product_pairs


def write_tsv(rows, file_path):
    with open(file_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for row in rows:
            writer.writerow(row)
            f.flush()


def main():
    product_pairs = get_fashionable_product_pairs()
    number_fashionable_pairs = len(product_pairs)
    print('Found {} pairs of fashionable clothing'.format(
        number_fashionable_pairs))

    # Get same number of invalid pairs
    print('Finding Invalid Clothing Pairs...')
    invalid_pairs = make_invalid_category_pair_map()
    invalid_product_pairs = generate_random_pairs(
        invalid_pairs, number_fashionable_pairs)

    # Get same number of 'unfashionable' pairs
    print('Finding Unfashionable Clothing Pairs...')
    valid_pairs = make_valid_category_pair_map()
    unfashionable_product_pairs = generate_random_pairs(
        valid_pairs, number_fashionable_pairs)

    print('Writing to TSVs')
    write_tsv(product_pairs, 'data-pairs/fashionable_clothing_pairs.tsv')
    write_tsv(unfashionable_product_pairs,
              'data-pairs/unfashionable_clothing_pairs.tsv')
    write_tsv(invalid_product_pairs, 'data-pairs/invalid_clothing_pairs.tsv')


if __name__ == '__main__':
    main()
