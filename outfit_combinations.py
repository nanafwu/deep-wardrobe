import importlib
import data_collection.db as db
from collections import defaultdict
from itertools import combinations
import csv
import random


def get_product_category_to_type():
    return {'jeans': 'bottom',
            'shorts': 'bottom',
            'womens-pants': 'bottom',
            'skirts': 'bottom',
            # 'dresses': 'one-piece',
            'womens-tops': 'top',
            'sweaters': 'top',
            'sweatshirts': 'top',
            'jackets': 'coat',
            'womens-outerwear': 'coat'}


def is_valid_combo(types):
    return types == set(['top', 'bottom']) or \
        types == set(['top', 'jacket']) or \
        types == set(['bottom', 'jacket'])


def get_collection_product_combinations():
    """
    For every collection, get possible combinations of products
    """
    category_to_types = get_product_category_to_type()

    collection_to_products = defaultdict(list)
    collection_products_db = db.get_collection_products()
    for row in collection_products_db:
        product_id = row[1]
        category = row[2]
        image_url = row[-1]
        collection_id = row[0]
        p = (product_id, category, image_url)
        collection_to_products[collection_id].append(p)

    all_collection_combinations = []
    counter = 0
    for collection_id, collection_products in collection_to_products.items():
        # For every collection, get one item per category
        seen_categories = set([])
        unique_products = []
        for product in collection_products:
            category = product[1]
            if category not in seen_categories:
                unique_products.append(product)
                seen_categories.add(category)

        product_combinations = list(combinations(unique_products, 2))
        for combo in product_combinations:
            item1_product_id = combo[0][0]
            item2_product_id = combo[1][0]
            # item3_product_id = combo[2][0]
            item1_type = combo[0][1]
            item2_type = combo[1][1]
            # item3_type = combo[2][1]
            item1_image = combo[0][2]
            item2_image = combo[1][2]
            # item3_image = combo[2][2]

            combo_types = set([category_to_types.get(cp[1], None)
                               for cp in combo])
            if is_valid_combo(combo_types):
                all_collection_combinations.append(
                    (counter, collection_id,
                     item1_product_id, item1_type, item1_image,
                     item2_product_id, item2_type, item2_image
                     # item3_product_id, item3_type, item3_image
                     ))
                counter += 1

    return all_collection_combinations


def write_tsv(rows, file_path):
    print('Writing to TSV ', file_path)
    with open(file_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for row in rows:
            writer.writerow(row)
            f.flush()


def main():
    all_collection_combinations = get_collection_product_combinations()
    print('Found {} combinations'.format(len(all_collection_combinations)))
    write_tsv(all_collection_combinations,
              'data-outfits/outfit_combinations.tsv')


if __name__ == '__main__':
    main()
