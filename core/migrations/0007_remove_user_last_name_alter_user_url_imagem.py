# Generated by Django 4.2.6 on 2023-11-27 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_address_complement_alter_address_reference'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='last_name',
        ),
        migrations.AlterField(
            model_name='user',
            name='url_imagem',
            field=models.ImageField(null=True, upload_to='uploads/user/'),
        ),
    ]
