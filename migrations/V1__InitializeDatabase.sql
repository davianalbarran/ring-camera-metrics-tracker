BEGIN;
-- uuid extension

-- Events:
    -- Event type
    -- Timestamp
    -- Source identifier
    -- Arbitrary metadata payload
CREATE TABLE IF NOT EXISTS events(
    event_id UUID NOT NULL PRIMARY KEY DEFAULT generate_uuid_v4(),
    event_type enum("alert", "yada", "foo", "bar") NOT NULL,
    timestamp timestamptz NOT NULL,
    source string NOT NULL,
    metadata json
);
COMMIT;