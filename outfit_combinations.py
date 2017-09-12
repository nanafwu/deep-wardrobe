import importlib
import data_collection.db as db
from collections import defaultdict, Counter
from itertools import permutations
import csv
import random


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
            'handbags': 'handbags',
            'hats': 'hats',
            'jewelry': 'jewelry',
            'sunglasses': 'sunglasses',
            'womens-shoes': 'shoes'}


def is_valid_combo(types):
    is_invalid = (types.count('top') == 2) or \
                 (types.count('bottom') == 2) or \
                 (types.count('coat') == 2) or \
                 (types.count('shoes') == 2) or \
                 (types.count('dress') == 2) or \
                 (types.count('hats') == 2) or \
                 (types.count('jewelry') == 2) or \
                 (types.count('sunglasses') == 2) or \
                 (types.count('handbags') == 2) or \
                 (types.count('dress') == 1 and
                  types.count('bottom') == 1) or \
                 (types.count('dress') == 1 and
                  types.count('top') == 1)

    return not is_invalid


def get_collection_product_permutations():
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

    all_collection_permutations = []
    all_products = set([])
    counter = 0
    permutation_categories_all = []
    for collection_id, collection_products in collection_to_products.items():
        # For every collection, get one item per category
        seen_categories = set([])
        unique_products = []
        for product in collection_products:
            category = product[1]
            if category not in seen_categories:
                unique_products.append(product)
                seen_categories.add(category)

        # Must have at last 4 unique types of products in collection
        if len(unique_products) < 4:
            pass

        product_combinations = list(permutations(unique_products, 4))
        for combo in product_combinations:
            item1_product_id = combo[0][0]
            item2_product_id = combo[1][0]
            item3_product_id = combo[2][0]
            item4_product_id = combo[3][0]

            item1_type = combo[0][1]
            item2_type = combo[1][1]
            item3_type = combo[2][1]
            item4_type = combo[3][1]

            item1_image = combo[0][2]
            item2_image = combo[1][2]
            item3_image = combo[2][2]
            item4_image = combo[3][2]

            combo_types = [category_to_types[cp[1]] for cp in combo]
            if is_valid_combo(combo_types):
                all_products.add((item1_product_id, item1_image))
                all_products.add((item2_product_id, item2_image))
                all_products.add((item3_product_id, item3_image))
                all_products.add((item4_product_id, item4_image))

                all_collection_permutations.append(
                    (counter, collection_id,
                     item1_product_id, item1_type, item1_image,
                     item2_product_id, item2_type, item2_image,
                     item3_product_id, item3_type, item3_image,
                     item4_product_id, item4_type, item4_image
                     ))
                permutation_categories = set([
                    item1_type, item2_type, item3_type, item4_type])
                permutation_categories_all.append(permutation_categories)
                counter += 1
    random.shuffle(all_collection_permutations)
    permutations_counter = Counter([tuple(per)
                                    for per in permutation_categories_all])
    return all_collection_permutations, all_products, permutations_counter


def write_tsv(rows, file_path):
    print('Writing to TSV ', file_path)
    with open(file_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for row in rows:
            writer.writerow(row)
            f.flush()


def main():
    all_collection_permutations, all_products, permutations_counter = get_collection_product_permutations()
    print('Found {} permuations'.format(len(all_collection_permutations)))
    print(permutations_counter)
    write_tsv(all_collection_permutations,
              'data-outfits/outfit_permutations.tsv')
    write_tsv(list(all_products),
              'data-outfits/outfit_products.tsv')


if __name__ == '__main__':
    main()
