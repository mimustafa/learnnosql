from django.db import models


class Study(models.Model):
    code = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=200)
    phase = models.CharField(max_length=20)
    indication = models.CharField(max_length=120)

    def __str__(self):
        return self.code


class Site(models.Model):
    study = models.ForeignKey(Study, related_name="sites", on_delete=models.CASCADE)
    code = models.CharField(max_length=32)
    country = models.CharField(max_length=80)

    class Meta:
        unique_together = [("study", "code")]

    def __str__(self):
        return self.code


class Participant(models.Model):
    study = models.ForeignKey(Study, related_name="participants", on_delete=models.CASCADE)
    site = models.ForeignKey(Site, related_name="participants", on_delete=models.PROTECT)
    participant_id = models.CharField(max_length=32, unique=True)
    cohort = models.CharField(max_length=80)
    status = models.CharField(max_length=40)

    def __str__(self):
        return self.participant_id


class Visit(models.Model):
    participant = models.ForeignKey(Participant, related_name="visits", on_delete=models.CASCADE)
    visit_name = models.CharField(max_length=80)
    day = models.IntegerField()
    systolic_bp = models.IntegerField()
    heart_rate = models.IntegerField()

    class Meta:
        ordering = ["day"]

    def __str__(self):
        return f"{self.participant.participant_id} {self.visit_name}"
