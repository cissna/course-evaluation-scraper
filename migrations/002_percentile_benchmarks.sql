BEGIN;

-- A precomputed snapshot; never rebuilt during a search or frontend filter change.
CREATE TABLE IF NOT EXISTS percentile_benchmarks (
    benchmark_id TEXT PRIMARY KEY CHECK (benchmark_id = 'current'),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

COMMIT;
