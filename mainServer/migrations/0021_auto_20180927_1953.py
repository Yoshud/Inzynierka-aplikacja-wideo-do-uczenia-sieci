# Generated by Django 2.1.1 on 2018-09-27 17:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainServer', '0020_auto_20180918_0739'),
    ]

    operations = [
        migrations.AddField(
            model_name='foldermodele',
            name='nazwa',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='folderzobrazami',
            name='nazwa',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='folderzprzygotowanymiobrazami',
            name='nazwa',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='folderzprzygotowanymiobrazami',
            name='sesja',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mainServer.Sesja'),
        ),
        migrations.AddField(
            model_name='foldezprzetworzonymiobrazami',
            name='nazwa',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='sesja',
            name='sciezka',
            field=models.FilePathField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='foldermodele',
            name='sciezka',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='folderzobrazami',
            name='sciezka',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='folderzprzygotowanymiobrazami',
            name='sciezka',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='foldezprzetworzonymiobrazami',
            name='sciezka',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='sesja',
            name='nazwa',
            field=models.TextField(default='Nienazwana_2018-09-27 17:53:55.115290+00:00'),
        ),
    ]
