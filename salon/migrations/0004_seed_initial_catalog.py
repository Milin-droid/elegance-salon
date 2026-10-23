from django.db import migrations


SERVICES = [
    ("Haircut", "300.00"),
    ("Braiding", "800.00"),
    ("Hair coloring", "1500.00"),
    ("Hair washing", "200.00"),
    ("Manicure", "500.00"),
    ("Pedicure", "700.00"),
    ("Facial Treatment", "1000.00"),
    ("Shampoo and Blow dry", "700.00"),
    ("Nail Art", "700.00"),
    ("Gel Nails", "1200.00"),
    ("Dreadlocks", "2000.00"),
    ("conrows", "700.00"),
]

STYLISTS = ["Jane", "Bridget", "Lilian"]


def seed_catalog(apps, schema_editor):
    Service = apps.get_model("salon", "Service")
    Stylist = apps.get_model("salon", "Stylist")
    database = schema_editor.connection.alias

    for name, price in SERVICES:
        Service.objects.using(database).get_or_create(
            name=name,
            defaults={"price": price, "duration_minutes": 30},
        )

    for name in STYLISTS:
        Stylist.objects.using(database).get_or_create(
            name=name,
            defaults={"phone": "", "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("salon", "0003_stylist_appointment_source_appointment_status_and_more"),
    ]

    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
