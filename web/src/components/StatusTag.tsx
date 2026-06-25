import type { Status } from "../types";

// Map pipeline status -> GOV.UK tag colour + label.
const MAP: Record<Status, { cls: string; label: string }> = {
  pending: { cls: "govuk-tag--grey", label: "Not processed" },
  awaiting_decision: { cls: "govuk-tag--yellow", label: "Awaiting decision" },
  approved: { cls: "govuk-tag--green", label: "Approved" },
  rejected: { cls: "govuk-tag--red", label: "Rejected" },
  modified: { cls: "govuk-tag--blue", label: "Modified" },
};

export default function StatusTag({ status }: { status: Status }) {
  const { cls, label } = MAP[status];
  return <strong className={`govuk-tag ${cls}`}>{label}</strong>;
}
