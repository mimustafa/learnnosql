# Django PostgreSQL vs MongoDB Lab

This is a separate Django experiment inside the `learnnosql` repo. It compares:

- PostgreSQL through the normal Django ORM.
- MongoDB through `pymongo`, because Django does not officially support MongoDB as a native ORM backend.

Keeping this as a folder in the same repo makes it easy to compare with the FastAPI demo without mixing dependencies, ports, or app code.

## Run

```bash
cd django_lab
docker compose up --build
```

Then open:

- Django comparison route: http://localhost:8010/
- PostgreSQL data: http://localhost:8010/postgres/studies/
- MongoDB data: http://localhost:8010/mongo/studies/

The Django lab uses its own Compose project name, ports, and volumes:

- Django: `8010`
- PostgreSQL: `5440`
- MongoDB: `27040`

## What To Look At

PostgreSQL is modeled with normalized Django models in `trials/models.py`.

MongoDB is accessed directly with `pymongo` in `trials/mongo.py`, storing a study document with embedded sites, participants, and visits.

This mirrors a real tradeoff: Django is excellent with relational data through its ORM, while MongoDB usually means using a driver or a separate integration layer instead of first-class Django models.
