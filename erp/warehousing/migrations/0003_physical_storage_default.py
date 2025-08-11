# Generated manually: Set default STORAGE subtype for PHYSICAL locations and backfill existing data
from django.db import migrations, models
from django.db.models import Q


def set_storage_for_physical(apps, schema_editor):
    Location = apps.get_model("warehousing", "Location")
    Location.objects.filter(type="PHYSICAL").filter(Q(subtype__isnull=True) | Q(subtype="")).update(subtype="STORAGE")


def noop_reverse(apps, schema_editor):
    # No reverse operation; leaving STORAGE values as-is is safe
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("warehousing", "0002_warehouse_id_sequence"),
    ]

    operations = [
        migrations.AlterField(
            model_name="location",
            name="subtype",
            field=models.CharField(
                blank=True,
                choices=[
                    ("STORAGE", "STORAGE"),
                    ("RECEIVE", "RECEIVE"),
                    ("DISPATCH", "DISPATCH"),
                    ("RETURN", "RETURN"),
                    ("QC", "QC"),
                    ("HOLD", "HOLD"),
                    ("DAMAGE", "DAMAGE"),
                    ("LOST", "LOST"),
                    ("EXCESS", "EXCESS"),
                    ("LOST_PENDING", "LOST_PENDING"),
                    ("EXCESS_PENDING", "EXCESS_PENDING"),
                    ("DAMAGE_PENDING", "DAMAGE_PENDING"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.RunPython(set_storage_for_physical, noop_reverse),
    ]
