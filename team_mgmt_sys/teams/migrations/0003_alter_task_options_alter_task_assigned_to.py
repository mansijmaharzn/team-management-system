# Generated by Django 5.0.7 on 2024-07-24 07:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0002_task_due_date"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="task",
            options={"ordering": ["due_date"]},
        ),
        migrations.AlterField(
            model_name="task",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
