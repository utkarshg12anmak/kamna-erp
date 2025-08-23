# Generated manually for PriceCoverage partial unique index

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('sales', '0001_initial')]
    operations = [
        migrations.RunSQL(
            sql=("CREATE UNIQUE INDEX IF NOT EXISTS ux_pricecoverage_active_unique ON sales_pricecoverage(item_id, pincode_id, status) WHERE status IN ('DRAFT','PUBLISHED');"),
            reverse_sql="DROP INDEX IF EXISTS ux_pricecoverage_active_unique;"
        )
    ]
