# Generated by Django 2.2.1 on 2019-05-15 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainServer', '0028_auto_20190515_1940'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='zlecenieaugmentacji',
            name='oczekiwanyRozmiarX',
        ),
        migrations.RemoveField(
            model_name='zlecenieaugmentacji',
            name='oczekiwanyRozmiarY',
        ),
        migrations.AlterField(
            model_name='sesja',
            name='nazwa',
            field=models.TextField(default='Nienazwana_2019-05-15 20:34:18.228170+00:00'),
        ),
    ]