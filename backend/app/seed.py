from psycopg.rows import dict_row

from app.db import mongo_db, postgres_conn
from app.sample_data import PARTICIPANTS, STUDY


def seed_mongo() -> None:
    mongo_db.studies.delete_many({})
    mongo_db.participants.delete_many({})

    mongo_db.studies.insert_one(STUDY)
    mongo_db.participants.insert_many(PARTICIPANTS)

    mongo_db.participants.create_index("participant_id", unique=True)
    mongo_db.participants.create_index([("study_id", 1), ("visits.visit_code", 1)])
    mongo_db.participants.create_index("visits.measurements.systolic_bp")


def seed_postgres() -> None:
    with postgres_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS studies (
                study_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                condition TEXT NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                protocol_version TEXT NOT NULL,
                primary_outcome TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sites (
                site_id TEXT PRIMARY KEY,
                study_id TEXT NOT NULL REFERENCES studies(study_id),
                name TEXT NOT NULL,
                country TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS protocol_visits (
                study_id TEXT NOT NULL REFERENCES studies(study_id),
                visit_code TEXT NOT NULL,
                label TEXT NOT NULL,
                target_day INTEGER NOT NULL,
                PRIMARY KEY (study_id, visit_code)
            );

            CREATE TABLE IF NOT EXISTS participants (
                participant_id TEXT PRIMARY KEY,
                study_id TEXT NOT NULL REFERENCES studies(study_id),
                site_id TEXT NOT NULL REFERENCES sites(site_id),
                cohort TEXT NOT NULL,
                age INTEGER NOT NULL,
                sex TEXT NOT NULL,
                risk_group TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                participant_id TEXT NOT NULL REFERENCES participants(participant_id),
                type TEXT NOT NULL,
                vendor TEXT NOT NULL,
                paired BOOLEAN NOT NULL
            );

            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                participant_id TEXT NOT NULL REFERENCES participants(participant_id),
                visit_code TEXT NOT NULL,
                completed_at DATE NOT NULL,
                mode TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                visit_id INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                numeric_value NUMERIC NOT NULL
            );

            CREATE TABLE IF NOT EXISTS questionnaires (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                visit_id INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                score NUMERIC NOT NULL
            );

            CREATE TABLE IF NOT EXISTS adverse_events (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                visit_id INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                severity TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_visits_participant_id ON visits(participant_id);
            CREATE INDEX IF NOT EXISTS idx_measurements_name_value ON measurements(name, numeric_value);
            CREATE INDEX IF NOT EXISTS idx_participants_study_cohort ON participants(study_id, cohort);
            """
        )
        conn.execute(
            """
            TRUNCATE adverse_events, questionnaires, measurements, visits, devices,
                     participants, protocol_visits, sites, studies
            RESTART IDENTITY CASCADE;
            """
        )

        conn.execute(
            """
            INSERT INTO studies
            (study_id, title, condition, phase, status, protocol_version, primary_outcome)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                STUDY["study_id"],
                STUDY["title"],
                STUDY["condition"],
                STUDY["phase"],
                STUDY["status"],
                STUDY["protocol"]["version"],
                STUDY["protocol"]["primary_outcome"],
            ),
        )

        for site in STUDY["sites"]:
            conn.execute(
                "INSERT INTO sites (site_id, study_id, name, country) VALUES (%s, %s, %s, %s)",
                (site["site_id"], STUDY["study_id"], site["name"], site["country"]),
            )

        for visit in STUDY["protocol"]["visit_schedule"]:
            conn.execute(
                """
                INSERT INTO protocol_visits (study_id, visit_code, label, target_day)
                VALUES (%s, %s, %s, %s)
                """,
                (STUDY["study_id"], visit["code"], visit["label"], visit["day"]),
            )

        for participant in PARTICIPANTS:
            conn.execute(
                """
                INSERT INTO participants
                (participant_id, study_id, site_id, cohort, age, sex, risk_group)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    participant["participant_id"],
                    participant["study_id"],
                    participant["site_id"],
                    participant["cohort"],
                    participant["profile"]["age"],
                    participant["profile"]["sex"],
                    participant["profile"]["risk_group"],
                ),
            )
            for device in participant["devices"]:
                conn.execute(
                    """
                    INSERT INTO devices (participant_id, type, vendor, paired)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (participant["participant_id"], device["type"], device["vendor"], device["paired"]),
                )
            for visit in participant["visits"]:
                visit_row = conn.execute(
                    """
                    INSERT INTO visits (participant_id, visit_code, completed_at, mode)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        participant["participant_id"],
                        visit["visit_code"],
                        visit["completed_at"],
                        visit["mode"],
                    ),
                ).fetchone()
                visit_id = visit_row[0]
                for name, value in visit["measurements"].items():
                    conn.execute(
                        "INSERT INTO measurements (visit_id, name, numeric_value) VALUES (%s, %s, %s)",
                        (visit_id, name, value),
                    )
                for questionnaire in visit["questionnaires"]:
                    conn.execute(
                        "INSERT INTO questionnaires (visit_id, name, score) VALUES (%s, %s, %s)",
                        (visit_id, questionnaire["name"], questionnaire["score"]),
                    )
                for event in visit["adverse_events"]:
                    conn.execute(
                        "INSERT INTO adverse_events (visit_id, description, severity) VALUES (%s, %s, %s)",
                        (visit_id, event["description"], event["severity"]),
                    )

        conn.commit()


def fetch_postgres_participant(participant_id: str) -> dict | None:
    with postgres_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            participant = cur.execute(
                """
                SELECT p.*, s.name AS site_name, s.country AS site_country
                FROM participants p
                JOIN sites s ON s.site_id = p.site_id
                WHERE p.participant_id = %s
                """,
                (participant_id,),
            ).fetchone()
            if not participant:
                return None

            devices = cur.execute(
                "SELECT type, vendor, paired FROM devices WHERE participant_id = %s ORDER BY id",
                (participant_id,),
            ).fetchall()
            visits = cur.execute(
                """
                SELECT id, visit_code, completed_at::text, mode
                FROM visits
                WHERE participant_id = %s
                ORDER BY completed_at
                """,
                (participant_id,),
            ).fetchall()

            for visit in visits:
                measurements = cur.execute(
                    "SELECT name, numeric_value FROM measurements WHERE visit_id = %s ORDER BY name",
                    (visit["id"],),
                ).fetchall()
                questionnaires = cur.execute(
                    "SELECT name, score FROM questionnaires WHERE visit_id = %s ORDER BY id",
                    (visit["id"],),
                ).fetchall()
                adverse_events = cur.execute(
                    "SELECT description, severity FROM adverse_events WHERE visit_id = %s ORDER BY id",
                    (visit["id"],),
                ).fetchall()
                visit["measurements"] = {row["name"]: float(row["numeric_value"]) for row in measurements}
                visit["questionnaires"] = [
                    {"name": row["name"], "score": float(row["score"])}
                    for row in questionnaires
                ]
                visit["adverse_events"] = adverse_events
                del visit["id"]

            return {
                "participant_id": participant["participant_id"],
                "study_id": participant["study_id"],
                "site": {
                    "site_id": participant["site_id"],
                    "name": participant["site_name"],
                    "country": participant["site_country"],
                },
                "cohort": participant["cohort"],
                "profile": {
                    "age": participant["age"],
                    "sex": participant["sex"],
                    "risk_group": participant["risk_group"],
                },
                "devices": devices,
                "visits": visits,
            }
