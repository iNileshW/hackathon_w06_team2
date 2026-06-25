import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useDecide, useProcess, useRequest } from "../api/queries";
import StatusTag from "../components/StatusTag";
import type { Decision, FoiRequest } from "../types";

export default function RequestDetail() {
  const { id = "" } = useParams();
  const { data, isLoading, isError, error } = useRequest(id);

  if (isLoading) return <p className="govuk-body">Loading&hellip;</p>;
  if (isError)
    return (
      <p className="govuk-body">Error: {(error as Error).message}</p>
    );
  if (!data) return <p className="govuk-body">Not found.</p>;

  return (
    <>
      <Link to="/" className="govuk-back-link">Back to requests</Link>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <span className="govuk-caption-l">{data.filename}</span>
          <h1 className="govuk-heading-xl">
            {data.id} <StatusTag status={data.status} />
          </h1>
        </div>
      </div>

      <RequestText text={data.request_text} />
      <PipelineSection record={data} id={id} />
    </>
  );
}

function RequestText({ text }: { text: string }) {
  return (
    <details className="govuk-details">
      <summary className="govuk-details__summary">
        <span className="govuk-details__summary-text">View original request</span>
      </summary>
      <div className="govuk-details__text">
        <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0 }}>
          {text}
        </pre>
      </div>
    </details>
  );
}

function PipelineSection({ record, id }: { record: FoiRequest; id: string }) {
  const process = useProcess(id);

  if (record.status === "pending") {
    return (
      <>
        <p className="govuk-body">
          This request has not been processed. Run the multi-agent pipeline to
          classify it, check exemptions, and draft a response.
        </p>
        <button
          className="govuk-button"
          data-module="govuk-button"
          disabled={process.isPending}
          onClick={() => process.mutate()}
        >
          {process.isPending ? "Processing…" : "Process request"}
        </button>
        {process.isError && (
          <p className="govuk-error-message">
            {(process.error as Error).message}
          </p>
        )}
      </>
    );
  }

  return (
    <>
      <Classification record={record} />
      <CompliancePanel record={record} />
      <DraftPanel record={record} />
      <CostPanel record={record} />
      {record.status === "awaiting_decision" ? (
        <DecisionGate id={id} />
      ) : (
        <DecisionBanner record={record} />
      )}
    </>
  );
}

function Classification({ record }: { record: FoiRequest }) {
  const c = record.classification;
  if (!c) return null;
  return (
    <>
      <h2 className="govuk-heading-l">Triage classification</h2>
      <dl className="govuk-summary-list">
        <Row k="Topic" v={c.topic} />
        <Row k="Complexity" v={c.complexity} />
        <Row k="Summary" v={c.summary} />
      </dl>
    </>
  );
}

function CompliancePanel({ record }: { record: FoiRequest }) {
  const c = record.compliance;
  if (!c) return null;
  return (
    <>
      <h2 className="govuk-heading-l">Compliance &amp; exemptions</h2>
      <dl className="govuk-summary-list">
        <Row
          k="Exemptions"
          v={c.exemptions_found.length ? c.exemptions_found.join(", ") : "None"}
        />
        <Row k="Recommendation" v={c.recommendation} />
        <Row k="Reasoning" v={c.reasoning} />
        <Row
          k="Policy sources (RAG)"
          v={c.policy_sources.length ? c.policy_sources.join(", ") : "None"}
        />
      </dl>
    </>
  );
}

function DraftPanel({ record }: { record: FoiRequest }) {
  if (!record.draft_response) return null;
  return (
    <>
      <h2 className="govuk-heading-l">Draft response</h2>
      <div className="govuk-inset-text">
        <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0 }}>
          {record.draft_response}
        </pre>
      </div>
    </>
  );
}

function CostPanel({ record }: { record: FoiRequest }) {
  const cb = record.cost_breakdown;
  if (!cb) return null;
  return (
    <>
      <h2 className="govuk-heading-l">Cost breakdown</h2>
      <table className="govuk-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header">Agent</th>
            <th scope="col" className="govuk-table__header">Model</th>
            <th scope="col" className="govuk-table__header govuk-table__header--numeric">Tokens</th>
            <th scope="col" className="govuk-table__header govuk-table__header--numeric">Cost (USD)</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          {cb.calls.map((call) => (
            <tr className="govuk-table__row" key={call.agent}>
              <td className="govuk-table__cell">{call.agent}</td>
              <td className="govuk-table__cell">{call.model}</td>
              <td className="govuk-table__cell govuk-table__cell--numeric">{call.total_tokens}</td>
              <td className="govuk-table__cell govuk-table__cell--numeric">${call.estimated_cost_usd.toFixed(4)}</td>
            </tr>
          ))}
          <tr className="govuk-table__row">
            <td className="govuk-table__cell"><strong>Total</strong></td>
            <td className="govuk-table__cell"></td>
            <td className="govuk-table__cell govuk-table__cell--numeric"><strong>{cb.total_tokens}</strong></td>
            <td className="govuk-table__cell govuk-table__cell--numeric"><strong>${cb.total_cost_usd.toFixed(4)}</strong></td>
          </tr>
        </tbody>
      </table>
    </>
  );
}

function DecisionGate({ id }: { id: string }) {
  const decide = useDecide(id);
  const [decision, setDecision] = useState<Decision>("approve");
  const [notes, setNotes] = useState("");

  return (
    <>
      <h2 className="govuk-heading-l">Approval gate</h2>
      <p className="govuk-body">
        No response is released without a recorded decision. Your choice is
        written to the timestamped decision log.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          decide.mutate({ decision, notes });
        }}
      >
        <div className="govuk-form-group">
          <fieldset className="govuk-fieldset">
            <legend className="govuk-fieldset__legend govuk-fieldset__legend--m">
              Decision
            </legend>
            <div className="govuk-radios" data-module="govuk-radios">
              {(["approve", "reject", "modify"] as Decision[]).map((d) => (
                <div className="govuk-radios__item" key={d}>
                  <input
                    className="govuk-radios__input"
                    id={`decision-${d}`}
                    name="decision"
                    type="radio"
                    value={d}
                    checked={decision === d}
                    onChange={() => setDecision(d)}
                  />
                  <label
                    className="govuk-label govuk-radios__label"
                    htmlFor={`decision-${d}`}
                  >
                    {d.charAt(0).toUpperCase() + d.slice(1)}
                  </label>
                </div>
              ))}
            </div>
          </fieldset>
        </div>

        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="notes">
            Notes {decision === "modify" ? "(required for modify)" : "(optional)"}
          </label>
          <textarea
            className="govuk-textarea"
            id="notes"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        <button
          className="govuk-button"
          data-module="govuk-button"
          disabled={decide.isPending || (decision === "modify" && !notes.trim())}
        >
          {decide.isPending ? "Recording…" : "Record decision"}
        </button>
        {decide.isError && (
          <p className="govuk-error-message">{(decide.error as Error).message}</p>
        )}
      </form>
    </>
  );
}

function DecisionBanner({ record }: { record: FoiRequest }) {
  const d = record.human_decision;
  if (!d) return null;
  return (
    <div
      className="govuk-notification-banner govuk-notification-banner--success"
      role="alert"
      data-module="govuk-notification-banner"
    >
      <div className="govuk-notification-banner__header">
        <h2 className="govuk-notification-banner__title">Decision recorded</h2>
      </div>
      <div className="govuk-notification-banner__content">
        <p className="govuk-notification-banner__heading">
          {d.decision.toUpperCase()} &mdash; logged {new Date(d.timestamp).toLocaleString()}
        </p>
        {d.notes && <p className="govuk-body">Notes: {d.notes}</p>}
        {d.evidence_refs.length > 0 && (
          <p className="govuk-body">Evidence: {d.evidence_refs.join(", ")}</p>
        )}
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="govuk-summary-list__row">
      <dt className="govuk-summary-list__key">{k}</dt>
      <dd className="govuk-summary-list__value">{v}</dd>
    </div>
  );
}
