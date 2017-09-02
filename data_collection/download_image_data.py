"""
Store images from ShopStyle
"""

import db as db
import sys
import getopt
import concurrent.futures
import urllib.request


def getimg():
    path = 'test.jpg'
    urllib.request.urlretrieve(
        'https://img.shopstyle-cdn.com/pim/85/9b/859be4fc133a03b335089ccd87c6fa3b_best.jpg', path)


def save_shopstyle_products():
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as e:
        for i in range(1):
            e.submit(getimg, i)


def main(argv):
    opts, args = getopt.getopt(argv, "p:", ["process="])
    for opt, arg in opts:
        if opt in ('-p', '--process'):
            if arg == 'product':
                save_shopstyle_products()


if __name__ == "__main__":
    main(sys.argv[1:])
