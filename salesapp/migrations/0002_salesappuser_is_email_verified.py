# Generated by Django 4.1.2 on 2022-11-05 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salesapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesappuser',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
