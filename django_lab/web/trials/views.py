from django.http import JsonResponse

from .models import Study
from .mongo import studies_collection


def index(request):
    return JsonResponse(
        {
            "message": "Django PostgreSQL vs MongoDB lab",
            "routes": {
                "comparison": "/comparison/",
                "postgres": "/postgres/studies/",
                "mongo": "/mongo/studies/",
            },
        }
    )


def comparison(request):
    return JsonResponse(
        {
            "decision": "Keep this as an isolated folder in the existing learning repo.",
            "postgres_with_django": [
                "Uses Django's official ORM and migrations.",
                "Best fit for relational constraints, joins, admin, forms, and reporting.",
            ],
            "mongodb_with_django": [
                "Uses pymongo directly because Django has no official MongoDB ORM backend.",
                "Best fit for document-shaped aggregates and flexible nested participant timelines.",
            ],
        }
    )


def postgres_studies(request):
    studies = []
    for study in Study.objects.prefetch_related("sites", "participants__visits"):
        studies.append(
            {
                "code": study.code,
                "title": study.title,
                "phase": study.phase,
                "indication": study.indication,
                "sites": [
                    {"code": site.code, "country": site.country}
                    for site in study.sites.all()
                ],
                "participants": [
                    {
                        "participant_id": participant.participant_id,
                        "site_code": participant.site.code,
                        "cohort": participant.cohort,
                        "status": participant.status,
                        "visits": [
                            {
                                "visit_name": visit.visit_name,
                                "day": visit.day,
                                "systolic_bp": visit.systolic_bp,
                                "heart_rate": visit.heart_rate,
                            }
                            for visit in participant.visits.all()
                        ],
                    }
                    for participant in study.participants.all()
                ],
            }
        )
    return JsonResponse({"source": "postgres_django_orm", "studies": studies})


def mongo_studies(request):
    studies = []
    for study in studies_collection().find({}, {"_id": False}):
        studies.append(study)
    return JsonResponse({"source": "mongodb_pymongo", "studies": studies})
