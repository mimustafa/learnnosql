import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Study",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32, unique=True)),
                ("title", models.CharField(max_length=200)),
                ("phase", models.CharField(max_length=20)),
                ("indication", models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name="Site",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32)),
                ("country", models.CharField(max_length=80)),
                ("study", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sites", to="trials.study")),
            ],
            options={"unique_together": {("study", "code")}},
        ),
        migrations.CreateModel(
            name="Participant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("participant_id", models.CharField(max_length=32, unique=True)),
                ("cohort", models.CharField(max_length=80)),
                ("status", models.CharField(max_length=40)),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="participants", to="trials.site")),
                ("study", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="trials.study")),
            ],
        ),
        migrations.CreateModel(
            name="Visit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visit_name", models.CharField(max_length=80)),
                ("day", models.IntegerField()),
                ("systolic_bp", models.IntegerField()),
                ("heart_rate", models.IntegerField()),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="visits", to="trials.participant")),
            ],
            options={"ordering": ["day"]},
        ),
    ]
