from typing import Any

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from app.db import mongo_db, postgres_conn
from app.seed import fetch_postgres_participant, seed_mongo, seed_postgres


app = FastAPI(title="MongoDB vs PostgreSQL Clinical Trial Comparison API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VisitCreate(BaseModel):
    visit_code: str = Field(examples=["week_8"])
    completed_at: str = Field(examples=["2026-03-06"])
    mode: str = Field(examples=["telehealth"])
    measurements: dict[str, float] = Field(
        default_factory=lambda: {
            "systolic_bp": 136,
            "diastolic_bp": 84,
            "steps_7_day_avg": 5800,
            "app_sessions": 19,
        }
    )
    questionnaires: list[dict[str, Any]] = Field(
        default_factory=lambda: [{"name": "Medication adherence", "score": 9}]
    )
    adverse_events: list[dict[str, str]] = Field(default_factory=list)


def clean_mongo(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, list):
        return [clean_mongo(item) for item in value]
    if isinstance(value, dict):
        return {key: clean_mongo(item) for key, item in value.items()}
    return value


@app.on_event("startup")
def startup() -> None:
    seed_mongo()
    seed_postgres()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/comparison")
def comparison() -> dict[str, Any]:
    return {
        "domain": "eHealth remote clinical trial platform",
        "mongo_strengths": [
            "One participant timeline can be read as one nested document.",
            "New device or questionnaire fields can be added without schema migrations.",
            "Arrays and nested measurements match the JSON shape used by APIs and apps.",
            "Updates that belong to one participant can often stay inside one aggregate.",
        ],
        "postgres_strengths": [
            "Foreign keys protect study, site, participant, visit, and measurement consistency.",
            "Normalized tables are strong for cross-study analytics and reporting.",
            "SQL joins make cohort-level questions explicit and precise.",
            "Stable clinical concepts can be constrained with types, keys, and checks.",
        ],
        "design_questions": [
            "Is the main access pattern participant timeline reads or population-level reporting?",
            "Which fields are stable enough to model as columns?",
            "Which fields are flexible clinical/device payloads?",
            "Where would duplicated data become dangerous?",
        ],
    }


@app.get("/api/mongo/studies")
def mongo_studies() -> list[dict[str, Any]]:
    studies = list(mongo_db.studies.find({}, {"_id": 0}))
    for study in studies:
        study["participant_count"] = mongo_db.participants.count_documents({"study_id": study["study_id"]})
    return clean_mongo(studies)


@app.get("/api/postgres/studies")
def postgres_studies() -> list[dict[str, Any]]:
    with postgres_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return cur.execute(
                """
                SELECT s.study_id, s.title, s.condition, s.phase, s.status,
                       s.protocol_version, s.primary_outcome,
                       COUNT(p.participant_id)::int AS participant_count
                FROM studies s
                LEFT JOIN participants p ON p.study_id = s.study_id
                GROUP BY s.study_id
                ORDER BY s.study_id
                """
            ).fetchall()


@app.get("/api/mongo/participants/{participant_id}")
def mongo_participant(participant_id: str) -> dict[str, Any]:
    participant = mongo_db.participants.find_one({"participant_id": participant_id}, {"_id": 0})
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    study = mongo_db.studies.find_one({"study_id": participant["study_id"]}, {"_id": 0, "sites": 1})
    site = next((item for item in study["sites"] if item["site_id"] == participant["site_id"]), None)
    participant["site"] = site
    return clean_mongo(participant)


@app.get("/api/postgres/participants/{participant_id}")
def postgres_participant(participant_id: str) -> dict[str, Any]:
    participant = fetch_postgres_participant(participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@app.post("/api/mongo/participants/{participant_id}/visits")
def add_mongo_visit(participant_id: str, visit: VisitCreate) -> dict[str, Any]:
    result = mongo_db.participants.update_one(
        {"participant_id": participant_id},
        {"$push": {"visits": visit.model_dump()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Participant not found")
    return mongo_participant(participant_id)


@app.post("/api/postgres/participants/{participant_id}/visits")
def add_postgres_visit(participant_id: str, visit: VisitCreate) -> dict[str, Any]:
    with postgres_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM participants WHERE participant_id = %s",
            (participant_id,),
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Participant not found")

        visit_id = conn.execute(
            """
            INSERT INTO visits (participant_id, visit_code, completed_at, mode)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (participant_id, visit.visit_code, visit.completed_at, visit.mode),
        ).fetchone()[0]

        for name, value in visit.measurements.items():
            conn.execute(
                "INSERT INTO measurements (visit_id, name, numeric_value) VALUES (%s, %s, %s)",
                (visit_id, name, value),
            )
        for questionnaire in visit.questionnaires:
            conn.execute(
                "INSERT INTO questionnaires (visit_id, name, score) VALUES (%s, %s, %s)",
                (visit_id, questionnaire["name"], questionnaire["score"]),
            )
        for event in visit.adverse_events:
            conn.execute(
                "INSERT INTO adverse_events (visit_id, description, severity) VALUES (%s, %s, %s)",
                (visit_id, event["description"], event["severity"]),
            )
        conn.commit()

    return postgres_participant(participant_id)


@app.get("/api/model-comparison")
def model_comparison() -> dict[str, Any]:
    return {
        "access_pattern": {
            "mongodb": "Optimized for reading and updating a participant timeline as one aggregate.",
            "postgresql": "Optimized for joining normalized entities and enforcing relationships.",
        },
        "schema_evolution": {
            "mongodb": "A new measurement can appear inside visits.measurements without a migration.",
            "postgresql": "The generic measurements table accepts new measurement names, while core entities stay normalized.",
        },
        "consistency": {
            "mongodb": "A single participant document update is atomic; cross-document rules need application logic or transactions.",
            "postgresql": "Foreign keys and relational constraints protect references between studies, sites, participants, and visits.",
        },
        "query_shape": {
            "mongodb": "Queries target nested paths and arrays, for example visits.measurements.systolic_bp.",
            "postgresql": "Queries join tables and filter rows, for example measurements.name = 'systolic_bp'.",
        },
        "indexing": {
            "mongodb": [
                "participant_id unique index",
                "compound study_id plus visits.visit_code index",
                "nested visits.measurements.systolic_bp index",
            ],
            "postgresql": [
                "primary keys and foreign keys",
                "participant_id indexes through keys",
                "use measurement name/value indexes for analytic queries",
            ],
        },
    }


@app.get("/api/reports/systolic-by-cohort")
def systolic_by_cohort() -> dict[str, Any]:
    mongo_pipeline = [
        {"$unwind": "$visits"},
        {"$match": {"visits.measurements.systolic_bp": {"$exists": True}}},
        {
            "$group": {
                "_id": "$cohort",
                "average_systolic_bp": {"$avg": "$visits.measurements.systolic_bp"},
                "measurement_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    mongo_rows = list(mongo_db.participants.aggregate(mongo_pipeline))
    mongo_result = [
        {
            "cohort": row["_id"],
            "average_systolic_bp": round(row["average_systolic_bp"], 1),
            "measurement_count": row["measurement_count"],
        }
        for row in mongo_rows
    ]

    sql = """
SELECT p.cohort,
       ROUND(AVG(m.numeric_value), 1)::float AS average_systolic_bp,
       COUNT(*)::int AS measurement_count
FROM participants p
JOIN visits v ON v.participant_id = p.participant_id
JOIN measurements m ON m.visit_id = v.id
WHERE m.name = 'systolic_bp'
GROUP BY p.cohort
ORDER BY p.cohort;
""".strip()
    with postgres_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            postgres_result = cur.execute(sql).fetchall()

    return {
        "question": "Average systolic blood pressure by cohort.",
        "mongodb": {
            "pipeline": mongo_pipeline,
            "result": mongo_result,
        },
        "postgresql": {
            "sql": sql,
            "result": postgres_result,
        },
    }


@app.get("/api/query-examples")
def query_examples() -> dict[str, Any]:
    return {
        "examples": [
            {
                "name": "Read one participant timeline",
                "question": "Return participant profile, devices, visits, measurements, questionnaires, and events.",
                "mongodb": {
                    "query": {"participant_id": "P-1001"},
                    "note": "The document already has the nested timeline shape used by the API.",
                },
                "postgresql": {
                    "sql": "Join participants, sites, devices, visits, measurements, questionnaires, and adverse_events.",
                    "note": "The backend reconstructs the nested response from normalized rows.",
                },
            },
            {
                "name": "Filter nested clinical measurements",
                "question": "Find participants whose systolic BP was above 145 at any visit.",
                "mongodb": {
                    "query": {
                        "visits": {
                            "$elemMatch": {
                                "measurements.systolic_bp": {"$gt": 145}
                            }
                        }
                    },
                    "note": "The query targets a nested field inside an array of visits.",
                },
                "postgresql": {
                    "sql": """
SELECT DISTINCT p.participant_id, p.cohort
FROM participants p
JOIN visits v ON v.participant_id = p.participant_id
JOIN measurements m ON m.visit_id = v.id
WHERE m.name = 'systolic_bp' AND m.numeric_value > 145;
""".strip(),
                    "note": "The same question joins participant, visit, and measurement tables.",
                },
            },
            {
                "name": "Add a flexible follow-up measurement",
                "question": "Record app_sessions and patient_reported_confidence at week 8.",
                "mongodb": {
                    "update": {
                        "$push": {
                            "visits": {
                                "visit_code": "week_8",
                                "measurements": {
                                    "app_sessions": 19,
                                    "patient_reported_confidence": 8,
                                },
                            }
                        }
                    },
                    "note": "The new fields can be stored inside the visit document immediately.",
                },
                "postgresql": {
                    "sql": "Insert one visit row, then insert one measurements row per new measurement name.",
                    "note": "This design keeps the schema stable while storing flexible measurement names as rows.",
                },
            },
            {
                "name": "Report by cohort",
                "question": "Calculate average systolic BP by cohort.",
                "mongodb": {
                    "pipeline": ["$unwind visits", "$match systolic_bp exists", "$group by cohort"],
                    "note": "MongoDB can aggregate nested arrays, but large reporting workloads may need careful indexing or a reporting model.",
                },
                "postgresql": {
                    "sql": "Join participants, visits, and measurements; group by participants.cohort.",
                    "note": "Relational tables are naturally shaped for this cross-participant report.",
                },
            },
        ],
    }
