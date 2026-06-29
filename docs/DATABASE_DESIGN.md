# Database Design Notes

## Purpose

This project compares two ways to model the same eHealth clinical-trial platform:

- MongoDB document model
- PostgreSQL relational model

The goal is not to prove that one database is always better. The goal is to connect database design choices to access patterns, constraints, updates, schema evolution, indexing, and reporting.

## Domain Model

The example is a remote clinical trial for blood pressure coaching. A study has:

- protocol metadata;
- sites;
- participants;
- participant profiles;
- paired home devices;
- visits;
- clinical measurements;
- questionnaires;
- adverse events.

The important design question is the unit of work. In this app, a common operational screen is the participant timeline: profile, devices, visits, measurements, questionnaires, and events together.

## MongoDB Model

Collections:

- `studies`
- `participants`

The participant document embeds the participant timeline:

```json
{
  "participant_id": "P-1001",
  "study_id": "EHEALTH-101",
  "site_id": "S-01",
  "cohort": "coaching_app",
  "profile": {
    "age": 52,
    "sex": "female",
    "risk_group": "high"
  },
  "devices": [
    { "type": "blood_pressure_cuff", "vendor": "Omron", "paired": true }
  ],
  "visits": [
    {
      "visit_code": "baseline",
      "completed_at": "2026-01-10",
      "mode": "telehealth",
      "measurements": {
        "systolic_bp": 151,
        "diastolic_bp": 93,
        "steps_7_day_avg": 4200,
        "phq4_score": 5
      },
      "questionnaires": [
        { "name": "Medication adherence", "score": 7 }
      ],
      "adverse_events": []
    }
  ]
}
```

This is a good document model when the application often reads or updates a whole participant timeline. The API can return the document in almost the same shape that the frontend needs.

### MongoDB Strengths In This Example

- The participant timeline is stored as one aggregate.
- Visits, measurements, questionnaires, and device fields can vary between participants.
- Adding `app_sessions`, `sleep_efficiency`, or another device field does not require a database migration.
- A single-document update is atomic.
- Nested JSON-like structures match REST/React payloads naturally.

### MongoDB Costs In This Example

- Cross-participant reports require aggregation over nested arrays.
- Consistency rules across collections are less visible than relational foreign keys.
- A document can grow too large if too much longitudinal data is embedded.
- Duplicated reference data can become stale if it is copied into many documents.
- Analytics may need separate reporting collections, pipelines, or a warehouse.

## PostgreSQL Model

Tables:

- `studies`
- `sites`
- `protocol_visits`
- `participants`
- `devices`
- `visits`
- `measurements`
- `questionnaires`
- `adverse_events`

The participant timeline is reconstructed by joining rows from several tables.

### PostgreSQL Strengths In This Example

- Foreign keys make relationships explicit.
- Stable entities such as study, site, participant, and visit have clear schemas.
- SQL is strong for cross-participant reports.
- Constraints protect many invalid states before application code runs.
- Normalization reduces duplication.

### PostgreSQL Costs In This Example

- Returning one participant timeline requires several joins and response reconstruction.
- Highly variable measurement payloads need either flexible rows, JSONB columns, or more tables.
- Some schema changes require migrations.
- Backend code may be more verbose for nested API responses.

## Access Pattern Comparison

Participant timeline read:

- MongoDB: one document lookup from `participants`.
- PostgreSQL: join participant, site, devices, visits, measurements, questionnaires, and events.

Population report:

- MongoDB: unwind visit arrays and group nested measurement values.
- PostgreSQL: join normalized tables and group rows.

Add flexible measurement:

- MongoDB: add a new field inside `visits.measurements`.
- PostgreSQL: insert another row into `measurements`, or add a typed column/table if the field becomes stable and important.

Enforce participant-site-study consistency:

- MongoDB: usually application logic, schema validation, or transactions.
- PostgreSQL: foreign keys and constraints.

## Query Comparison

Find participants whose systolic blood pressure was above 145 at any visit.

MongoDB:

```js
db.participants.find({
  visits: {
    $elemMatch: {
      "measurements.systolic_bp": { $gt: 145 }
    }
  }
})
```

PostgreSQL:

```sql
SELECT DISTINCT p.participant_id, p.cohort
FROM participants p
JOIN visits v ON v.participant_id = p.participant_id
JOIN measurements m ON m.visit_id = v.id
WHERE m.name = 'systolic_bp'
  AND m.numeric_value > 145;
```

Average systolic blood pressure by cohort.

MongoDB:

```js
db.participants.aggregate([
  { $unwind: "$visits" },
  { $match: { "visits.measurements.systolic_bp": { $exists: true } } },
  {
    $group: {
      _id: "$cohort",
      average_systolic_bp: { $avg: "$visits.measurements.systolic_bp" },
      measurement_count: { $sum: 1 }
    }
  },
  { $sort: { _id: 1 } }
])
```

PostgreSQL:

```sql
SELECT p.cohort,
       ROUND(AVG(m.numeric_value), 1)::float AS average_systolic_bp,
       COUNT(*)::int AS measurement_count
FROM participants p
JOIN visits v ON v.participant_id = p.participant_id
JOIN measurements m ON m.visit_id = v.id
WHERE m.name = 'systolic_bp'
GROUP BY p.cohort
ORDER BY p.cohort;
```

## Update Comparison

Add a week 8 visit with new flexible measurements.

MongoDB:

```js
db.participants.updateOne(
  { participant_id: "P-1001" },
  {
    $push: {
      visits: {
        visit_code: "week_8",
        completed_at: "2026-03-06",
        mode: "app_follow_up",
        measurements: {
          systolic_bp: 136,
          diastolic_bp: 84,
          app_sessions: 19,
          patient_reported_confidence: 8
        },
        questionnaires: [{ name: "Medication adherence", score: 9 }],
        adverse_events: []
      }
    }
  }
)
```

PostgreSQL:

```sql
INSERT INTO visits (participant_id, visit_code, completed_at, mode)
VALUES ('P-1001', 'week_8', '2026-03-06', 'telehealth')
RETURNING id;

INSERT INTO measurements (visit_id, name, numeric_value)
VALUES
  (:visit_id, 'systolic_bp', 136),
  (:visit_id, 'diastolic_bp', 84),
  (:visit_id, 'app_sessions', 19),
  (:visit_id, 'patient_reported_confidence', 8);
```

In this SQL design, flexible measurements are stored as rows instead of adding one column per measurement. That keeps the schema flexible while preserving relational structure.

## Index Comparison

MongoDB indexes in this app:

```js
db.participants.createIndex({ participant_id: 1 }, { unique: true })
db.participants.createIndex({ study_id: 1, "visits.visit_code": 1 })
db.participants.createIndex({ "visits.measurements.systolic_bp": 1 })
```

PostgreSQL indexes in this app:

```sql
CREATE INDEX idx_visits_participant_id ON visits(participant_id);
CREATE INDEX idx_measurements_name_value ON measurements(name, numeric_value);
CREATE INDEX idx_participants_study_cohort ON participants(study_id, cohort);
```

MongoDB indexes can target nested fields. PostgreSQL indexes target columns and are often paired with joins and foreign keys.

## Embed, Reference, Or Normalize

Embed when:

- child data is usually read with the parent;
- child data is owned by one parent;
- the nested array will not grow without bound;
- atomic updates inside one aggregate are useful.

Reference or normalize when:

- many records point to the same entity;
- duplicated data would become risky;
- the data is queried independently;
- cross-record constraints matter;
- reports need to scan and group many records.

Hybrid designs are common. A healthcare platform might use document-shaped operational records and relational/warehouse models for reporting.

## Practice Exercises

1. Add a new wearable measurement called `sleep_efficiency`.
2. Add a new questionnaire that only exists for one protocol version.
3. Add a participant with no wearable device and compare how both models represent missing optional data.
4. Add a report for average systolic blood pressure by site.
5. Add an adverse event and discuss whether it should remain embedded or become its own collection/table.
6. Add validation so systolic blood pressure must be between realistic clinical bounds.
7. Add a second study with a different visit schedule.
8. Compare how many code and schema changes each task requires.

## Design Rule Of Thumb

Use MongoDB when the main unit of work is a document-shaped aggregate that changes together and is usually read together.

Use PostgreSQL when relationships, constraints, and cross-record reporting are central to the system.

The best database design starts with access patterns and correctness requirements, not with the database brand.
