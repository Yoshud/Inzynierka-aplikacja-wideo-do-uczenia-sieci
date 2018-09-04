# Generated by Django 2.0.2 on 2018-09-04 06:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainServer', '0017_auto_20180904_0750'),
    ]

    operations = [
        migrations.CreateModel(
            name='FoldeZPrzetworzonymiObrazami',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sciezka', models.TextField(default='')),
            ],
        ),
        migrations.AlterField(
            model_name='sesja',
            name='nazwa',
            field=models.TextField(default='Nienazwana_2018-09-04 06:29:01.537335+00:00'),
        ),
        migrations.AddField(
            model_name='sesja',
            name='folderPrzetworzone',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mainServer.FoldeZPrzetworzonymiObrazami'),
        ),
    ]