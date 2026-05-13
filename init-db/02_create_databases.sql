DO $$
BEGIN
    CREATE DATABASE payment_accounting;
EXCEPTION WHEN duplicate_database THEN
    RAISE NOTICE 'database payment_accounting already exists, skipping';
END
$$;
