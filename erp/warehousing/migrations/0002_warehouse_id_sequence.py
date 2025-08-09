from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("warehousing", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=
            """
            -- Create sequence if it does not exist
            CREATE SEQUENCE IF NOT EXISTS warehousing_warehouse_warehouse_id_seq START WITH 1 INCREMENT BY 1 MINVALUE 1;
            -- Ensure the sequence is owned by the target column so it is dropped with the table/column
            ALTER SEQUENCE warehousing_warehouse_warehouse_id_seq OWNED BY warehousing_warehouse.warehouse_id;
            -- Position the sequence at current max so nextval returns max+1 (or 1 if empty)
            DO $$
            DECLARE
                max_val BIGINT;
            BEGIN
                SELECT MAX(warehouse_id) INTO max_val FROM warehousing_warehouse;
                IF max_val IS NULL OR max_val < 1 THEN
                    PERFORM setval('warehousing_warehouse_warehouse_id_seq', 1, false);
                ELSE
                    PERFORM setval('warehousing_warehouse_warehouse_id_seq', max_val, true);
                END IF;
            END $$;
            -- Set default to nextval
            ALTER TABLE warehousing_warehouse ALTER COLUMN warehouse_id SET DEFAULT nextval('warehousing_warehouse_warehouse_id_seq');
            """,
            reverse_sql=
            """
            -- Drop default and sequence on rollback
            ALTER TABLE warehousing_warehouse ALTER COLUMN warehouse_id DROP DEFAULT;
            DROP SEQUENCE IF EXISTS warehousing_warehouse_warehouse_id_seq;
            """,
        ),
        migrations.RunSQL(
            sql=
            """
            -- Backfill any existing rows with NULL warehouse_id
            UPDATE warehousing_warehouse
            SET warehouse_id = nextval('warehousing_warehouse_warehouse_id_seq')
            WHERE warehouse_id IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
