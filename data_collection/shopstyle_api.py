"""
Sample API Calls:

https://www.shopstyle.com/api/v2/site/featuredLooks?limit=1&offset=0&pid=shopstyle
http://api.shopstyle.com/api/v2/categories?pid=shopstyle
http://api.shopstyle.com/api/v2/products/359131344?pid=shopstyle
https://www.shopstyle.com/api/v2/posts?limit=6&maxNumProducts=4&offset=6&pid=shopstyle&userId=newdarlings
"""

import requests
import json
from sqlalchemy.exc import IntegrityError
import db as db
import cnfg
import sys
import argparse

config = cnfg.load(".metis_config")


def get_api_json(api_url):
    response = requests.get(api_url).text
    resp_obj = json.loads(response)
    return resp_obj


def parse_collection_obj(c):
    id = c['id']
    post_url = c['postUrl']
    author = c['author']
    author_id = author['id']
    author_handle = author['handle']
    image_url = c['images'][0]['sizes']['Large']['url']
    collection_tags = c['internalTags']
    return {'id': id,
            'post_url': post_url,
            'author_handle': author_handle,
            'author_id': author_id,
            'image_url': image_url,
            'tags': collection_tags}


def get_parent_category(category_map, categories):
    parent_categories = [category_map.get(cat, None)
                         for cat in categories if category_map.get(
        cat, None)]
    parent_category = None
    if parent_categories:
        parent_category = parent_categories[0]
    return parent_category


def parse_product(prod, category_map):
    id = prod['id']
    name = prod['name']
    image_url = prod['image']['sizes']['Original']['url']
    categories = [cat['id'] for cat in prod['categories']]
    parent_category = get_parent_category(category_map, categories)
    return {'id': id,
            'product_name': name,
            'image_url': image_url,
            'categories': categories,
            'parent_category': parent_category}


def store_collections(api_url):
    print('Getting API url', api_url)
    posts = get_api_json(api_url)['posts']
    conn = db.make_db_conn()
    collection_table = db.get_shopstyle_collection_table()
    product_table = db.get_shopstyle_product_table()
    cp_table = db.get_shopstyle_collection_product_table()
    category_map = db.get_category_parent_mapping(conn)

    for i, p in enumerate(posts):
        post_type = p['type']
        if post_type == 'Collection':
            collection = parse_collection_obj(p)
            print(i, ' - Found collection:', collection)

            try:
                conn.execute(collection_table.insert(), collection)
            except IntegrityError as e:
                print('Already inserted collection ', collection['id'])

            collection_products = [parse_product(
                prod, category_map) for prod in p['products']]
            print('Found {} products: {}'.format(
                len(collection_products), collection_products))

            for cp in collection_products:
                try:
                    conn.execute(product_table.insert(), cp)
                except IntegrityError as e:
                    print('Already product id', cp['id'])

                try:
                    collection_product_id = {'collection_id': collection['id'],
                                             'product_id': cp['id']}
                    conn.execute(cp_table.insert(), collection_product_id)
                except IntegrityError as e:
                    print('Already inserted collection product id',
                          collection_product_id)


def paginate_shopstyle_products(url, offset, category_map):
    api_url = url + '&offset=' + str(offset)
    products = get_api_json(api_url)['products']
    products = [parse_product(
                prod, category_map) for prod in products]
    return products


def store_shopstyle_products(product_type):
    api_url = ''
    if product_type == 'dress':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=dress&limit=50'
    elif product_type == 'jeans':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+jeans&limit=50'
    elif product_type == 'jacket':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+jacket&limit=50'
    elif product_type == 'outerwear':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+outerwear&limit=50'
    elif product_type == 'pants':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+pants&limit=50'
    elif product_type == 'shorts':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+shorts&limit=50'
    elif product_type == 'skirts':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=skirts&limit=50'
    elif product_type == 'sweaters':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+sweater&limit=50'
    elif product_type == 'sweatshirt':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+sweatshirts&limit=50'
    elif product_type == 'tops':
        api_url = 'http://api.shopstyle.com/api/v2/products?pid=shopstyle&fts=women+tops&limit=50'

    conn = db.make_db_conn()
    product_table = db.get_shopstyle_product_table()
    category_map = db.get_category_parent_mapping(conn)
    offset = 0
    while offset <= 4000:
        print('Getting {} batch {}'.format(product_type, offset))
        product_batch = paginate_shopstyle_products(
            api_url, offset, category_map)
        for p in product_batch:
            try:
                conn.execute(product_table.insert(), p)
            except IntegrityError:
                print('product ', p['id'], ' already exists')
        offset += 50


def store_featured_looks():
    featured_looks_api_url = 'https://www.shopstyle.com/api/v2/site/featuredLooks?' + \
        'limit=1000&offset=0&pid=shopstyle'
    store_collections(featured_looks_api_url)


def store_author_collections():
    authors = db.get_authors()
    for i, author_handle in enumerate(authors):
        print(i, ' - Getting collections from author ', author_handle)
        collections_api_url = 'https://www.shopstyle.com/api/v2/posts?limit=1000' + \
            '&maxNumProducts=50&offset=0&pid=shopstyle&userId=' + author_handle
        store_collections(collections_api_url)


def store_shopstyle_categories():
    categories_api_url = 'http://api.shopstyle.com/api/v2/categories?pid=' + \
        config['shopstyle']['api_key']
    print('Getting API url', categories_api_url)
    categories = get_api_json(categories_api_url)['categories']
    conn = db.make_db_conn()
    category_table = db.get_shopstyle_category_table()

    try:
        for category in categories:
            id = category['id']
            parent_id = category['parentId']
            print('Inserting category: ', id, ', ', parent_id)
            conn.execute(category_table.insert(),
                         {'id': id, 'parent_id': parent_id})
    except:
        e = sys.exc_info()[0]
        print('Error, skipping batch')
        print(e)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--process", dest="process",
                        help='process to run')
    parser.add_argument("--type", dest="type",
                        help='subcategory in process')
    args = parser.parse_args(argv)
    process = args.process

    if process == 'category':
        store_shopstyle_categories()
    if process == 'featured-looks':
        store_featured_looks()
    if process == 'author':
        store_author_collections()
    if process == 'product':
        category = args.type
        store_shopstyle_products(category)


if __name__ == "__main__":
    main(sys.argv[1:])
