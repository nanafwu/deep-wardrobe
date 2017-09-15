from clothing_classifier import get_clothing_vector_model, get_img_vectors
import argparse
import utils
import db
import sys

COLLECTIONS_PRODUCT_FILE = 'data-outfits/products.tsv'
COLLECTION_IMAGES_DIR = 'images/images_collection_products/'
COLLECTIONS_PRODUCT_FEAT_FILE = 'data-outfits/products_features.tsv'


def save_product_features():
    products = []
    model = get_clothing_vector_model()

    print('Reading file ', COLLECTIONS_PRODUCT_FILE)
    with open(COLLECTIONS_PRODUCT_FILE, 'r') as f:
        for i, line in enumerate(f.readlines()):
            if i % 50 == 0:
                print('Processing product ', i)
            try:
                l = line.split('\t')
                product_id = l[0]
                product_img_path = COLLECTION_IMAGES_DIR + product_id + '.jpg'
                product_feat = get_img_vectors(model, product_img_path)
                products.append([product_id] + product_feat.tolist())
            except Exception as e:
                print(e)
    utils.write_tsv(products, COLLECTIONS_PRODUCT_FEAT_FILE)
    return products


def save_collection_product_ids():
    """ Afterwards run
    `python data_collection/download_image_data.py -p collection_products`
    """
    products_set = set([])
    collection_products = db.get_collection_products()

    for row in collection_products:
        product_id = row[1]
        category = row[2]
        product_name = row[-2]
        image_url = row[-1]
        p = (product_id, image_url, category, product_name)
        products_set.add(p)

    products_lst = [list(prod) for prod in products_set]
    print('Found {} unique products used in collections'.format(
        len(products_lst)))
    utils.write_tsv(products_lst, COLLECTIONS_PRODUCT_FILE)


def main(argv):
    """`python store_product_features.py --process collection-products`"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--process", dest="process",
                        help='process to run')
    args = parser.parse_args(argv)
    process = args.process

    if process == 'collection-products':
        save_collection_product_ids()
    elif process == 'product-features':
        save_product_features()


if __name__ == "__main__":
    main(sys.argv[1:])
