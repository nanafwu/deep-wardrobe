from app.clothing_classifier import image_preprocess
import csv
import argparse
import utils
import data_collection.db as db
import sys


def save_product_features(model, product_file, img_dir, output_file):
    products = []
    print('Reading file ', product_file)
    with open(product_file, 'r') as f:
        for i, line in enumerate(f.readlines()[:]):
            if i % 50 == 0:
                print('Processing product ', i)
            try:
                l = line.split('\t')
                product_id = l[0]
                product_img_path = img_dir + product_id + '.jpg'
                product_img = image_preprocess(product_img_path)
                product_feat = model.predict(product_img)

                products.append([product_id] + product_feat[0].tolist())
            except Exception as e:
                print(e)

    print('Saving products to ', output_file)
    with open(output_file, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for p in products:
            writer.writerow(p)
            f.flush()
    return products


def save_collection_product_ids():
    """ Afterwards run
    `python data_collection/download_image_data.py -p collection_products`
    """
    file_output_path = 'data-outfits/products.tsv'
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
    utils.write_tsv(products_lst, file_output_path)


def main(argv):
    """`python store_product_features.py --process collection-products`"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--process", dest="process",
                        help='process to run')
    args = parser.parse_args(argv)
    process = args.process

    if process == 'collection-products':
        save_collection_product_ids()


if __name__ == "__main__":
    main(sys.argv[1:])
