# Generated by Django 4.0 on 2022-10-13 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calc_api', '0004_countrydata'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('name', models.TextField(primary_key=True, serialize=False)),
                ('id', models.TextField()),
                ('scale', models.CharField(max_length=15, null=True)),
                ('country', models.CharField(max_length=60, null=True)),
                ('country_id', models.CharField(max_length=3, null=True)),
                ('admin1', models.CharField(max_length=60, null=True)),
                ('admin1_id', models.CharField(max_length=15, null=True)),
                ('admin2', models.CharField(max_length=60, null=True)),
                ('admin2_id', models.CharField(max_length=15, null=True)),
                ('bbox', models.TextField(null=True)),
                ('poly', models.TextField(null=True)),
            ],
        ),
    ]
