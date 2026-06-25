import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  decideRequest,
  fetchRequest,
  fetchRequests,
  processRequest,
} from "./client";
import type { Decision, FoiRequest } from "../types";

const keys = {
  all: ["requests"] as const,
  one: (id: string) => ["requests", id] as const,
};

export function useRequests() {
  return useQuery({ queryKey: keys.all, queryFn: fetchRequests });
}

export function useRequest(id: string) {
  return useQuery({ queryKey: keys.one(id), queryFn: () => fetchRequest(id) });
}

/** Write the freshly returned record into both the list and detail caches. */
function syncCaches(qc: ReturnType<typeof useQueryClient>, record: FoiRequest) {
  qc.setQueryData<FoiRequest>(keys.one(record.id), record);
  qc.setQueryData<FoiRequest[]>(keys.all, (prev) =>
    prev?.map((r) => (r.id === record.id ? record : r)),
  );
}

export function useProcess(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => processRequest(id),
    onSuccess: (record) => syncCaches(qc, record),
  });
}

export function useDecide(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { decision: Decision; notes: string }) =>
      decideRequest(id, vars.decision, vars.notes),
    onSuccess: (record) => syncCaches(qc, record),
  });
}
