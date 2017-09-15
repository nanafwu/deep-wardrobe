CREATE TABLE stylst_user (
       user_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
       name VARCHAR(100),
       create_time TIMESTAMP DEFAULT now()
);

CREATE TABLE stylst_user_wardrobe(
       user_id uuid REFERENCES stylst_user(user_id),
       image_url VARCHAR(1000),
       image_vector FLOAT[],
       create_time TIMESTAMP DEFAULT now(),
       item_id uuid PRIMARY KEY DEFAULT uuid_generate_v4()
);
