"""
Store images from ShopStyle
"""

import db as db
import sys
import getopt


def save_shopstyle_products():


def main(argv):
    opts, args = getopt.getopt(argv, "p:", ["process="])
    for opt, arg in opts:
        if opt in ('-p', '--process'):
            if arg == 'product':
                save_shopstyle_products()


if __name__ == "__main__":
    main(sys.argv[1:])
