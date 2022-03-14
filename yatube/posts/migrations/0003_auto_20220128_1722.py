# Generated by Django 2.2.19 on 2022-01-28 07:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0002_auto_20220122_2012"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="post",
            options={"ordering": ["-pub_date"]},
        ),
        migrations.AlterField(
            model_name="group",
            name="description",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="group",
            name="slug",
            field=models.SlugField(max_length=300, unique=True),
        ),
        migrations.AlterField(
            model_name="group",
            name="title",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="post",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="posts",
                to="posts.Group",
            ),
        ),
    ]