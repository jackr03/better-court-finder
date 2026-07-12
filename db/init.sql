CREATE TABLE subscriptions (
    user_id BIGINT NOT NULL,
    venue TEXT NOT NULL,
    PRIMARY KEY (user_id, venue)
);

CREATE INDEX subscriptions_venue_idx ON subscriptions (venue);