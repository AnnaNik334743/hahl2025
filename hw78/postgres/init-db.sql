CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);

INSERT INTO items (name)
SELECT 'initial_item_' || i
FROM generate_series(0, 10000) AS i
WHERE NOT EXISTS (SELECT 1 FROM items LIMIT 1);