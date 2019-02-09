from django.db import migrations
from mainServer.models import *


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    color_dicts=[
        {
            "nazwa": "Czerwony",
            "kod": "rgba(255, 30, 30, 0.0)"
        },
        {
            "nazwa": "Zolty",
            "kod": "rgba(249, 245, 0, 0.0)"
        },
        {
            "nazwa": "Fioletowy",
            "kod": "rgba(100, 18, 132, 0.0)"
        },
        {
            "nazwa": "Niebieski",
            "kod": "rgba(14, 51, 237, 0.0)"
        }
    ]
    colors = [Kolor.objects.get_or_create(**color_dict)[0] for color_dict in color_dicts]
    colorSet = ZbiorKolorow.objects.get_or_create(nazwa="Domyslny zestaw")[0]

    for color in colors:
        colorSet.kolory.add(color)

    colorSet.domyslny_kolor = colors[0]



def reverse_func(apps, schema_editor):
    # forwards_func() creates two Country instances,
    # so reverse_func() should delete them.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('mainServer', '0026_auto_20190120_1834'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
