# Learn NoSQL with MongoDB, PostgreSQL, FastAPI, and React

This project teaches MongoDB by comparing the same eHealth clinical-trial platform implemented with:

- MongoDB: document model, embedded protocol/site/participant/visit data.
- PostgreSQL: relational model, normalized tables and joins.
- FastAPI: one backend exposing both database implementations.
- React: one UI that shows both results side by side.

## Domain

The example is a remote clinical trial / eHealth study platform. A study has sites, consent requirements, visit schedule, participants, wearable/device readings, questionnaires, adverse events, and follow-up visits.

This domain is useful for teaching document databases because participant records naturally contain nested, variable, time-based data:

- different visits can collect different measurements;
- questionnaire answers may change over protocol versions;
- wearable/device data often arrives as flexible nested payloads;
- a participant timeline is often read as one document-shaped aggregate.

SQL is still very good here when you need strong relational constraints, cross-study reporting, normalized lookup tables, and complex joins across participants, sites, visits, and measurements.

## Run

```bash
docker compose up --build
```

Then open:

- React app: http://localhost:5173
- FastAPI docs: http://localhost:8000/docs

Docker Compose uses the explicit project name `learnnosql`, so its containers, network, and volumes are grouped as `learnnosql-*`. MongoDB is exposed on host port `27018`, and PostgreSQL is exposed on host port `5433`, which avoids the most common conflicts with other local Docker projects.

The backend seeds both MongoDB and PostgreSQL automatically on startup.

## Useful API Routes

- `GET /api/comparison` explains the modeling tradeoffs.
- `GET /api/model-comparison` compares access patterns, schema evolution, consistency, query shape, and indexing.
- `GET /api/mongo/studies` returns study documents from MongoDB.
- `GET /api/postgres/studies` returns equivalent study summaries from PostgreSQL.
- `GET /api/mongo/participants/P-1001` returns a nested participant aggregate from MongoDB.
- `GET /api/postgres/participants/P-1001` reconstructs the same aggregate through SQL joins.
- `POST /api/mongo/participants/P-1001/visits` adds a visit into one participant document.
- `POST /api/postgres/participants/P-1001/visits` adds a visit across relational tables.
- `GET /api/query-examples` compares several MongoDB and PostgreSQL query/update shapes.
- `GET /api/reports/systolic-by-cohort` compares an aggregation/reporting query in both databases.

## Teaching Focus

Use the code to compare:

- where the backend code is simpler with embedded documents;
- where SQL makes constraints and reporting clearer;
- what changes when you add a flexible measurement;
- how MongoDB queries arrays and nested fields;
- how PostgreSQL reconstructs nested API responses from normalized rows;
- how indexing differs for nested document fields and relational joins;
- when to embed, when to reference, and when to normalize.

## Reset The Demo Data

The backend reseeds both databases on startup. To reset the example after changing data in the UI:

```bash
docker compose restart api
```

To remove containers and volumes for this project only:

```bash
docker compose down --volumes
```
