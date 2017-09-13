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
    dir_path = 'data-all/'
    for product in products:
        parent_category = product[-1]
        url = product[1]
        id = product[0]
        path = dir_path + parent_category + '/' + str(id) + '.jpg'
        parsed_products.append((id, url, path))
    Pool(10).map(get_img, parsed_products)


def get_tsv_products(filepath, img_dir):
    products = []
    with open(filepath, 'r') as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter='\t')
        for row in tsvreader:
            product_id = row[0]
            product_img = row[1]
            path = img_dir + str(product_id) + '.jpg'
            products.append((product_id, product_img, path))
    return products


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


def save_outfit_combinations():
    img_dir = 'data-outfits/images_large/'
    outfits_file = 'data-outfits/outfit_products_large.tsv'
    outfits_products = get_tsv_products(outfits_file, img_dir)
    Pool(4).map(get_img, outfits_products)


def save_collection_images():
    img_dir = 'data-outfits/images_collections/'
    collections = db.get_collection_images()
    collection_imgs = []
    for c in collections:
        image_url = c[1]
        id = str(c[0])
        path = img_dir + id + '.jpg'
        collection_imgs.append((id, image_url, path))
    Pool(4).map(get_img, collection_imgs)


def save_paired_combinations():

    # Fashionable
    fashionable_dir_path = 'data-pairs/fashionable/'
    fashionable_product_pairs_file = 'data-pairs/fashionable_clothing_pairs.tsv'
    fashionable_products = get_tsv_images(
        fashionable_product_pairs_file, fashionable_dir_path)
    print('Getting fashionable clothing images ...')
    Pool(4).map(get_img, fashionable_products)

    # Invalid
    invalid_dir_path = 'data-pairs/invalid/'
    invalid_product_pairs_file = 'data-pairs/invalid_clothing_pairs.tsv'
    invalid_products = get_tsv_images(
        invalid_product_pairs_file, invalid_dir_path)
    print('Getting invalid clothing images ...')
    Pool(4).map(get_img, invalid_products)

    # Unfashionable
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
            elif arg == 'outfits':
                save_outfit_combinations()
            elif arg == 'paired':
                save_paired_combinations()
            elif arg == 'collection':
                save_collection_images()


if __name__ == "__main__":
    main(sys.argv[1:])
