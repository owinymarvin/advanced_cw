# Generated by Django 5.1.3 on 2024-11-17 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='action_type',
            field=models.CharField(max_length=20),
        ),
    ]