# Generated by Django 5.1.7 on 2025-05-21 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PetitionSummaryCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('청원제목', models.CharField(max_length=255)),
                ('청원요지', models.TextField()),
                ('분야', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': '분류된 청원요지',
                'verbose_name_plural': '분류된 청원요지 모음',
            },
        ),
    ]
