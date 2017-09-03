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
