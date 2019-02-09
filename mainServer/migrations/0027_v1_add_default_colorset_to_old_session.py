# Generated by Django 2.1.5 on 2019-02-09 15:26

from django.db import migrations, models
import django.db.models.deletion
from mainServer.models import *


def colorSetPk():
    return ZbiorKolorow.objects.get(nazwa="Domyslny zestaw").pk


def forwards_func(apps, schema_editor):
    sessions = Sesja.objects.filter(zbiorKolorow=None)
    for session in sessions:
        session.zbiorKolorow = ZbiorKolorow.objects.get(nazwa="Domyslny zestaw")


def reverse_func(apps, schema_editor):
    # forwards_func() creates two Country instances,
    # so reverse_func() should delete them.
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('mainServer', '0027_auto_20190209_1526'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),

        migrations.AlterField(
            model_name='sesja',
            name='zbiorKolorow',
            field=models.ForeignKey(default=colorSetPk(), on_delete=django.db.models.deletion.PROTECT, to='mainServer.ZbiorKolorow'),
        ),

    ]
