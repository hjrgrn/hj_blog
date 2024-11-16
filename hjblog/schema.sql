DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS cities;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(60) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    city_id INTEGER,
    hash_pass TEXT NOT NULL,
    subscribed TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    is_admin BOOL NOT NULL DEFAULT(FALSE),
    is_two_factor_authentication_enabled NOT NULL DEFAULT(FALSE),
    secret_token VARCHAR(300),
    FOREIGN KEY (city_id) REFERENCES cities (id)
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    title VARCHAR(60) NOT NULL,
    content TEXT(2000) NOT NULL,
    path_to_file VARCHAR(500),
    posted TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    author_id INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES users (id)
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    content TEXT(400) NOT NULL,
    author_id INTEGER NOT NULL,
    written TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (author_id) REFERENCES users (id),
    FOREIGN KEY (post_id) REFERENCES posts (id)
);

CREATE TABLE cities (
	id INTEGER PRIMARY KEY,
	name VARCHAR(169) NOT NULL,
	latitude NUMERIC NOT NULL,
	longitude NUMERIC NOT NULL,
    timezone VARCHAR(200) NOT NULL,
    UNIQUE (name, latitude, longitude)
);
