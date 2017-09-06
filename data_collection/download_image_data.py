"""
Store images from ShopStyle
"""

import db as db
import sys
import getopt
from multiprocessing.dummy import Pool
import urllib.request


def get_img(product):
    parent_category = product[-1]
    url = product[1]
    id = product[0]
    print('Getting ', str(id), ': ', parent_category, ', ', url)
    path = 'data-all/train/' + parent_category + '/' + str(id) + '.jpg'
    urllib.request.urlretrieve(url, path)


def save_shopstyle_products():
    products = db.get_product_images()
    Pool(10).map(get_img, products)


def main(argv):
    opts, args = getopt.getopt(argv, "p:", ["process="])
    for opt, arg in opts:
        if opt in ('-p', '--process'):
            if arg == 'product':
                save_shopstyle_products()


if __name__ == "__main__":
    main(sys.argv[1:])
