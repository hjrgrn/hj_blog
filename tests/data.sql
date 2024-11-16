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

INSERT INTO cities (
    id,
    name,
    latitude,
    longitude,
    timezone
) VALUES (
    1,
    "rome",
    41.89193,
    12.51133,
    "Europe/Rome"
);

INSERT INTO users (
    id,
    username,
    email,
    city_id,
    hash_pass,
    subscribed
) VALUES (
    1,
    "prova",
    "prova@prova.com",
    1,
    "pbkdf2:sha256:600000$vF0pgSVKHdhZSj3e$35fdd55422ef0e97477b2076124de040795635a61ff6174e36a206a47cbf7280", -- Password: prova
    "2023-01-01 00:00:00"
);

INSERT INTO users (
    id,
    username,
    email,
    hash_pass,
    subscribed,
    is_admin
) VALUES (
    2,
    "admin",
    "admin@admin.com",
    "pbkdf2:sha256:600000$vF0pgSVKHdhZSj3e$35fdd55422ef0e97477b2076124de040795635a61ff6174e36a206a47cbf7280", -- Password: prova
    "2023-01-01 00:00:00",
    TRUE
);


INSERT INTO posts (
    title,
    content,
    author_id
) VALUES (
    "test-title-0",
    "This is a test, this is the content of the post.",
    2
);

INSERT INTO posts (
    title,
    content,
    author_id
) VALUES (
    "test-title-1",
    "This is a test, this is the content of the post.",
    2
);

INSERT INTO posts (
    title,
    content,
    author_id
) VALUES (
    "test-title-2",
    "This post has no comments.",
    2
);

INSERT INTO comments (
    post_id,
    content,
    author_id
) VALUES (
    1,
    "Commento di prova da utente 'prova'",
    2
);

INSERT INTO comments (
    post_id,
    content,
    author_id
) VALUES (
    2,
    "Questo commento non apparirà nel test",
    2
);
