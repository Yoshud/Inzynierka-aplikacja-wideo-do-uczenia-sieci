from django.db import migrations
from mainServer.models import *


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version

    movie_status_tags = [
        "Do przetworzenia", "Aktywny", "Przypisano punkty", "W trakcie obslugi", "Przetworzono",
        "W trakcie przetwarzania"
    ]
    for tag in movie_status_tags:
        StatusFilmu.objects.get_or_create(status=tag)

    point_status_tags = [
        "Koniec", "Dodane uzytkownik", "Interpolacja", "Brak"
    ]
    for tag in point_status_tags:
        StatusPozycji.objects.get_or_create(status=tag)

    StatusPozycjiCrop.objects.get_or_create(status="punktOrginalny")


def reverse_func(apps, schema_editor):
    # forwards_func() creates two Country instances,
    # so reverse_func() should delete them.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('mainServer', '0026_v1_add_default_colors_and_color_set'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
