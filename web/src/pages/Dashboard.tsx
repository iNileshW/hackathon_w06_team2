import { Link } from "react-router-dom";
import { useRequests } from "../api/queries";
import StatusTag from "../components/StatusTag";

export default function Dashboard() {
  const { data, isLoading, isError, error } = useRequests();

  return (
    <>
      <h1 className="govuk-heading-xl">FOI requests</h1>
      <p className="govuk-body-l">
        Incoming Freedom of Information requests processed by the triage,
        compliance, and response agents. Open a request to run the pipeline and
        record an approval decision.
      </p>

      {isLoading && <p className="govuk-body">Loading requests&hellip;</p>}

      {isError && (
        <div className="govuk-error-summary" data-module="govuk-error-summary">
          <h2 className="govuk-error-summary__title">Could not load requests</h2>
          <div className="govuk-error-summary__body">
            <p className="govuk-body">{(error as Error).message}</p>
            <p className="govuk-body">Is the API running on port 8000?</p>
          </div>
        </div>
      )}

      {data && (
        <table className="govuk-table">
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-table__header">Reference</th>
              <th scope="col" className="govuk-table__header">Topic</th>
              <th scope="col" className="govuk-table__header">Status</th>
              <th scope="col" className="govuk-table__header">
                <span className="govuk-visually-hidden">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {data.map((r) => (
              <tr className="govuk-table__row" key={r.id}>
                <th scope="row" className="govuk-table__header">{r.id}</th>
                <td className="govuk-table__cell">
                  {r.classification?.topic ?? "—"}
                </td>
                <td className="govuk-table__cell">
                  <StatusTag status={r.status} />
                </td>
                <td className="govuk-table__cell">
                  <Link className="govuk-link" to={`/requests/${r.id}`}>
                    View<span className="govuk-visually-hidden"> {r.id}</span>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
