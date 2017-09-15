from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy import Table, Column
from sqlalchemy import String, MetaData, Float
from sqlalchemy.dialects.postgresql import ARRAY
import cnfg


def connect_db():
    """Connects to the specific database."""
    config = cnfg.load(".metis_config")
    engine = create_engine('postgresql://{}:{}@{}:5432/{}'.format(
        config['db_user'],
        config['db_pwd'],
        config['db_host'],
        'shopstyle'))

    conn = engine.connect()
    return conn


def get_user_wardrobe_table():
    metadata = MetaData()
    return Table('stylst_user_wardrobe', metadata,
                 Column('user_id', String),
                 Column('image_url', String),
                 Column('image_vector', ARRAY(Float)))


def insert_wardrobe_item(conn, user_id, image_url, image_vector):
    wardrobe_table = get_user_wardrobe_table()
    item = {'user_id': user_id,
            'image_url': image_url,
            'image_vector': image_vector}
    conn.execute(wardrobe_table.insert(), item)


def get_wardrobe_items(conn, user_id):
    query = "SELECT image_url, image_vector FROM stylst_user_wardrobe WHERE user_id = '{}' ORDER BY create_time".format(
        user_id)
    s_all = text(query)
    results = [{'url': i[0], 'vector': i[1]}
               for i in conn.execute(s_all).fetchall()]
    return results
