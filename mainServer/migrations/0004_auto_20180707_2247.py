# Generated by Django 2.0.2 on 2018-07-07 20:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainServer', '0003_auto_20180707_2234'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='folderfilmy',
            name='sesja',
        ),
        migrations.AlterField(
            model_name='obraz',
            name='folder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mainServer.FolderZObrazami'),
        ),
        migrations.AlterField(
            model_name='sesja',
            name='nazwa',
            field=models.TextField(default='Nienazwana_<django.db.models.fields.AutoField>__2018-07-07 20:47:38.400053+00:00'),
        ),
        migrations.DeleteModel(
            name='FolderFilmy',
        ),
    ]