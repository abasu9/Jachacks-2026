CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    apr FLOAT8[] NOT NULL,
    pip INTEGER NOT NULL,
    joiningDate DATE NOT NULL,
    rank FLOAT8 NOT NULL
);
