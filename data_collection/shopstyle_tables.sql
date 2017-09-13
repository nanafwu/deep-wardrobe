CREATE TABLE shopstyle_category (
       id VARCHAR(100) PRIMARY KEY,
       parent_id VARCHAR(100) REFERENCES shopstyle_category(id)
);

CREATE TABLE shopstyle_collection(
       id BIGINT PRIMARY KEY,
       post_url VARCHAR(2000),
       author_handle VARCHAR(1000),
       author_id BIGINT,
       image_url VARCHAR(5000) NOT NULL,
       tags VARCHAR(1000)[]
);

CREATE TABLE shopstyle_product(
       id BIGINT PRIMARY KEY,
       product_name VARCHAR(2000),
       image_url VARCHAR(5000) NOT NULL,
       categories VARCHAR(100)[],
       parent_category VARCHAR(100) REFERENCES shopstyle_category(id),
       create_time TIMESTAMP DEFAULT now()
);

CREATE TABLE shopstyle_collection_product (
       collection_id BIGINT REFERENCES shopstyle_collection(id),
       product_id BIGINT REFERENCES shopstyle_product(id),
       PRIMARY KEY (collection_id, product_id)
);

/**
Useful Queries
**/

SELECT parent_category, count(1)
FROM shopstyle_product
WHERE
parent_category IS NOT NULL
GROUP BY parent_category
ORDER BY count(1) DESC

-- Get all categorized products in collections

SELECT cp.collection_id, c.author_handle, p.id, p.parent_category, p.product_name
FROM shopstyle_collection_product cp, shopstyle_product p, shopstyle_collection c
WHERE
p.id = cp.product_id
AND c.id = cp.collection_id
AND p.parent_category IS NOT NULL
ORDER BY cp.collection_id


SELECT cp.collection_id, p.id, p.parent_category,
c.author_handle, p.product_name, p.image_url
FROM shopstyle_collection_product cp, shopstyle_product p, shopstyle_collection c
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


SELECT count(DISTINCT cp.collection_id)
FROM shopstyle_collection_product cp, shopstyle_product p
WHERE p.id = cp.product_id
AND p.parent_category IS NOT NULL
