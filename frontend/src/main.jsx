import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, Database, FileJson, Plus, RefreshCw, Table2 } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function JsonBlock({ value }) {
  return <pre>{JSON.stringify(value, null, 2)}</pre>;
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Panel({ title, icon, children }) {
  return (
    <section className="panel">
      <div className="panel-title">
        {icon}
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function App() {
  const [comparison, setComparison] = useState(null);
  const [mongoStudy, setMongoStudy] = useState(null);
  const [postgresStudy, setPostgresStudy] = useState(null);
  const [mongoParticipant, setMongoParticipant] = useState(null);
  const [postgresParticipant, setPostgresParticipant] = useState(null);
  const [modelComparison, setModelComparison] = useState(null);
  const [queryExamples, setQueryExamples] = useState(null);
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState("loading");
  const [selectedParticipant, setSelectedParticipant] = useState("P-1001");

  async function loadData(participantId = selectedParticipant) {
    setStatus("loading");
    const [
      comparisonRes,
      modelComparisonRes,
      mongoStudiesRes,
      postgresStudiesRes,
      mongoParticipantRes,
      postgresParticipantRes,
      queryRes,
      reportRes,
    ] = await Promise.all([
        fetch(`${API_URL}/api/comparison`),
        fetch(`${API_URL}/api/model-comparison`),
        fetch(`${API_URL}/api/mongo/studies`),
        fetch(`${API_URL}/api/postgres/studies`),
        fetch(`${API_URL}/api/mongo/participants/${participantId}`),
        fetch(`${API_URL}/api/postgres/participants/${participantId}`),
        fetch(`${API_URL}/api/query-examples`),
        fetch(`${API_URL}/api/reports/systolic-by-cohort`),
      ]);

    setComparison(await comparisonRes.json());
    setModelComparison(await modelComparisonRes.json());
    setMongoStudy((await mongoStudiesRes.json())[0]);
    setPostgresStudy((await postgresStudiesRes.json())[0]);
    setMongoParticipant(await mongoParticipantRes.json());
    setPostgresParticipant(await postgresParticipantRes.json());
    setQueryExamples(await queryRes.json());
    setReport(await reportRes.json());
    setStatus("ready");
  }

  async function addWeek8Visit(target) {
    setStatus(`adding-${target}`);
    await fetch(`${API_URL}/api/${target}/participants/${selectedParticipant}/visits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visit_code: "week_8",
        completed_at: "2026-03-06",
        mode: target === "mongo" ? "app_follow_up" : "telehealth",
        measurements: {
          systolic_bp: 136,
          diastolic_bp: 84,
          steps_7_day_avg: 5800,
          app_sessions: 19,
          patient_reported_confidence: 8,
        },
        questionnaires: [{ name: "Medication adherence", score: 9 }],
        adverse_events: [],
      }),
    });
    await loadData(selectedParticipant);
  }

  useEffect(() => {
    loadData();
  }, []);

  const visitCounts = useMemo(
    () => ({
      mongo: mongoParticipant?.visits?.length ?? 0,
      postgres: postgresParticipant?.visits?.length ?? 0,
    }),
    [mongoParticipant, postgresParticipant],
  );

  return (
    <main>
      <header className="app-header">
        <div>
          <div className="eyebrow">
            <Activity size={16} />
            eHealth database design lab
          </div>
          <h1>MongoDB vs PostgreSQL for a Remote Clinical Trial</h1>
          <p>
            One healthcare research concept, two backend data models. Compare how document and relational databases
            shape API code, data design, queries, updates, and reporting.
          </p>
        </div>
        <button onClick={() => loadData()} disabled={status === "loading"}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </header>

      <div className="toolbar">
        <label>
          Participant
          <select
            value={selectedParticipant}
            onChange={(event) => {
              setSelectedParticipant(event.target.value);
              loadData(event.target.value);
            }}
          >
            <option value="P-1001">P-1001</option>
            <option value="P-1002">P-1002</option>
          </select>
        </label>
        <Stat label="Mongo visits" value={visitCounts.mongo} />
        <Stat label="Postgres visits" value={visitCounts.postgres} />
      </div>

      {comparison && (
        <section className="comparison-band">
          <div>
            <h2>Document model</h2>
            <ul>{comparison.mongo_strengths.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
          <div>
            <h2>Relational model</h2>
            <ul>{comparison.postgres_strengths.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
        </section>
      )}

      <div className="grid two">
        <Panel title="MongoDB study document" icon={<FileJson size={20} />}>
          <JsonBlock value={mongoStudy} />
        </Panel>
        <Panel title="PostgreSQL study summary" icon={<Table2 size={20} />}>
          <JsonBlock value={postgresStudy} />
        </Panel>
      </div>

      {modelComparison && (
        <Panel title="Model tradeoffs" icon={<Table2 size={20} />}>
          <JsonBlock value={modelComparison} />
        </Panel>
      )}

      <div className="grid two">
        <Panel title="MongoDB participant aggregate" icon={<Database size={20} />}>
          <button className="secondary" onClick={() => addWeek8Visit("mongo")}>
            <Plus size={16} />
            Add week 8 visit
          </button>
          <JsonBlock value={mongoParticipant} />
        </Panel>
        <Panel title="PostgreSQL reconstructed aggregate" icon={<Database size={20} />}>
          <button className="secondary" onClick={() => addWeek8Visit("postgres")}>
            <Plus size={16} />
            Add week 8 visit
          </button>
          <JsonBlock value={postgresParticipant} />
        </Panel>
      </div>

      {report && (
        <Panel title="Cohort-level report" icon={<Activity size={20} />}>
          <p className="question">{report.question}</p>
          <div className="grid two compact">
            <JsonBlock value={report.mongodb} />
            <JsonBlock value={report.postgresql} />
          </div>
        </Panel>
      )}

      {queryExamples && (
        <Panel title="Same requirements, different query shapes" icon={<Activity size={20} />}>
          {queryExamples.examples.map((example) => (
            <section className="example" key={example.name}>
              <h3>{example.name}</h3>
              <p className="question">{example.question}</p>
              <div className="grid two compact">
                <JsonBlock value={example.mongodb} />
                <JsonBlock value={example.postgresql} />
              </div>
            </section>
          ))}
        </Panel>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
