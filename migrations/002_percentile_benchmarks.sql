BEGIN;

-- One compact snapshot: 401 values per metric and weighting mode, for 1.00–5.00.
CREATE TABLE IF NOT EXISTS percentile_benchmarks (
    benchmark_id TEXT PRIMARY KEY CHECK (benchmark_id = 'current'),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL,
    pending_evaluations BIGINT NOT NULL DEFAULT 0 CHECK (pending_evaluations >= 0)
);

-- Also support reapplying this migration to the earlier review version.
ALTER TABLE percentile_benchmarks
    ADD COLUMN IF NOT EXISTS pending_evaluations BIGINT NOT NULL DEFAULT 0 CHECK (pending_evaluations >= 0);

INSERT INTO percentile_benchmarks (benchmark_id, payload)
VALUES ('current', '{}'::JSONB) ON CONFLICT (benchmark_id) DO NOTHING;

-- Only a genuinely new evaluation row counts. Metadata changes and the UPDATE
-- arm of an upsert do not fire this trigger. Imports use the same counter.
CREATE OR REPLACE FUNCTION count_new_percentile_evaluation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO percentile_benchmarks (benchmark_id, payload, pending_evaluations)
    VALUES ('current', '{}'::JSONB, 1)
    ON CONFLICT (benchmark_id) DO UPDATE
        SET pending_evaluations = percentile_benchmarks.pending_evaluations + 1;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS count_new_percentile_evaluation ON courses;
CREATE TRIGGER count_new_percentile_evaluation
AFTER INSERT ON courses
FOR EACH ROW EXECUTE FUNCTION count_new_percentile_evaluation();

COMMIT;
