# Generated by Django 4.1.2 on 2022-11-10 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salesapp', '0010_userpaymentinformation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpaymentinformation',
            name='expiry',
            field=models.CharField(max_length=5),
        ),
    ]
