from copy import deepcopy

from django.core.management.base import BaseCommand

from trials.models import Participant, Site, Study, Visit
from trials.mongo import studies_collection
from trials.sample_data import STUDY_DOCUMENT


class Command(BaseCommand):
    help = "Seed the Django lab PostgreSQL and MongoDB demo data."

    def handle(self, *args, **options):
        study_document = deepcopy(STUDY_DOCUMENT)

        Visit.objects.all().delete()
        Participant.objects.all().delete()
        Site.objects.all().delete()
        Study.objects.all().delete()

        study = Study.objects.create(
            code=study_document["code"],
            title=study_document["title"],
            phase=study_document["phase"],
            indication=study_document["indication"],
        )

        sites = {}
        for site_data in study_document["sites"]:
            site = Site.objects.create(study=study, **site_data)
            sites[site.code] = site

        for participant_data in study_document["participants"]:
            visits = participant_data["visits"]
            participant = Participant.objects.create(
                study=study,
                site=sites[participant_data["site_code"]],
                participant_id=participant_data["participant_id"],
                cohort=participant_data["cohort"],
                status=participant_data["status"],
            )
            for visit_data in visits:
                Visit.objects.create(participant=participant, **visit_data)

        collection = studies_collection()
        collection.delete_many({})
        collection.insert_one(study_document)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded 1 study and {len(study_document['participants'])} participants in PostgreSQL and MongoDB."
            )
        )
