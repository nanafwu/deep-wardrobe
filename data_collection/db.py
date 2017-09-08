from sqlalchemy import create_engine
from sqlalchemy import Table, Column
from sqlalchemy import Integer, String, MetaData
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import text
import cnfg


def make_db_conn():
    config = cnfg.load(".metis_config")
    engine = create_engine('postgresql://{}:{}@{}:5432/{}'.format(
        config['db_user'],
        config['db_pwd'],
        config['db_host'],
        'shopstyle'))

    conn = engine.connect()
    return conn


def get_shopstyle_category_table():
    metadata = MetaData()
    return Table('shopstyle_category', metadata,
                 Column('id', String), Column('parent_id', String))


def get_shopstyle_collection_table():
    metadata = MetaData()
    return Table('shopstyle_collection', metadata,
                 Column('id', Integer),
                 Column('post_url', String),
                 Column('author_handle', String),
                 Column('author_id', Integer),
                 Column('image_url', String),
                 Column('tags', ARRAY(String)))


def get_shopstyle_product_table():
    metadata = MetaData()
    return Table('shopstyle_product', metadata,
                 Column('id', Integer),
                 Column('product_name', String),
                 Column('image_url', String),
                 Column('categories', ARRAY(String)),
                 Column('parent_category', String))


def get_shopstyle_collection_product_table():
    metadata = MetaData()
    return Table('shopstyle_collection_product', metadata,
                 Column('collection_id', Integer),
                 Column('product_id', Integer))


def get_category_parent_mapping(conn):
    cat_mapping = {}
    parent_category_query_results = set(
        ['dresses', 'jeans', 'jackets', 'womens-outerwear', 'womens-pants',
         'shorts', 'skirts', 'sweaters', 'sweatshirts', 'womens-tops',
         'womens-shoes', 'jewelry', 'handbags'])
    for parent_cat in parent_category_query_results:
        cat_mapping[parent_cat] = parent_cat

    all_categories_query = "SELECT * FROM shopstyle_category"
    s_all = text(all_categories_query)
    all_categories_result = conn.execute(s_all).fetchall()
    for cat, parent_cat in all_categories_result:
        if parent_cat in parent_category_query_results:
            cat_mapping[cat] = parent_cat
        elif cat == 'sunglasses' or cat == 'hats':
            cat_mapping[cat] = cat
    return cat_mapping


def get_product_images():
    conn = make_db_conn()
    query = "SELECT id, image_url, parent_category FROM shopstyle_product WHERE parent_category IS NOT NULL"
    s_all = text(query)
    products_result = conn.execute(s_all).fetchall()
    return products_result


def get_product_images_by_category(category):
    conn = make_db_conn()
    query = "SELECT id, image_url, parent_category FROM shopstyle_product WHERE parent_category = '{}' LIMIT 4000".format(
        category)
    s_all = text(query)
    products_result = conn.execute(s_all).fetchall()
    return products_result


def get_authors():
    conn = make_db_conn()
    query = "select author_handle from shopstyle_collection group by author_handle order by count(1) asc"
    s_all = text(query)
    authors_result = [author[0] for author in conn.execute(s_all).fetchall()]
    return authors_result


def get_collection_products():
    conn = make_db_conn()
    query = """SELECT cp.collection_id, p.id, p.parent_category,
               c.author_handle, p.product_name, p.image_url
               FROM shopstyle_collection_product cp, shopstyle_product p,
                    shopstyle_collection c
               WHERE
               p.id = cp.product_id
               AND c.id = cp.collection_id
               AND p.parent_category IS NOT NULL
               AND c.id IN (
                    SELECT cp.collection_id
                    FROM shopstyle_collection_product cp, shopstyle_product p
                    WHERE p.id = cp.product_id
                    AND p.parent_category IS NOT NULL
                    GROUP BY cp.collection_id
                    HAVING count(1) < 8
               )
            """
    s_all = text(query)
    products_result = conn.execute(s_all).fetchall()
    return products_result
