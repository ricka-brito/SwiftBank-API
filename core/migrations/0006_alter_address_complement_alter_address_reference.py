# Generated by Django 4.2.6 on 2023-11-24 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_user_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='complement',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='address',
            name='reference',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
