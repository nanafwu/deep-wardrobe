"""
Store images from ShopStyle
"""

import db as db
import sys
import getopt
from multiprocessing.dummy import Pool
import urllib.request
import csv


def get_img(product):
    path = product[-1]
    url = product[1]
    id = product[0]
    print('Getting ', str(id), ': ', path, ', ', url)
    urllib.request.urlretrieve(url, path)


def save_shopstyle_products():
    products = db.get_product_images()
    parsed_products = []
    dir_path = 'data-all/train/'
    for product in products:
        parent_category = product[-1]
        url = product[1]
        id = product[0]
        path = dir_path + parent_category + '/' + str(id) + '.jpg'
        parsed_products.append((id, url, path))
    Pool(10).map(get_img, parsed_products)


def get_tsv_images(filepath, dir_path):
    products = []
    with open(filepath, 'r') as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter='\t')
        for row in tsvreader:
            product1 = row[2]
            product1_image = row[4]
            product2 = row[5]
            product2_image = row[7]
            pair_id = row[0]
            path1 = dir_path + pair_id + '_' + str(product1) + '.jpg'
            path2 = dir_path + pair_id + '_' + str(product2) + '.jpg'
            products.append((product1, product1_image, path1))
            products.append((product2, product2_image, path2))
    return products


def save_paired_combinations():
    valid_dir_path = 'data-pairs/valid/'
    valid_product_pairs_file = 'data-pairs/valid_clothing_pairs.tsv'

    unfashionable_dir_path = 'data-pairs/unfashionable/'
    unfashionable_product_pairs_file = 'data-pairs/unfashionable_clothing_pairs.tsv'
    unfashionable_products = get_tsv_images(
        unfashionable_product_pairs_file, unfashionable_dir_path)
    Pool(4).map(get_img, unfashionable_products)


def main(argv):
    opts, args = getopt.getopt(argv, "p:", ["process="])
    for opt, arg in opts:
        if opt in ('-p', '--process'):
            if arg == 'product':
                save_shopstyle_products()
            elif arg == 'paired':
                save_paired_combinations()


if __name__ == "__main__":
    main(sys.argv[1:])
