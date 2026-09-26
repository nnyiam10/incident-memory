const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

export type ApiHealth = { status: string; mode: string };
export type DemoIncident = { id: string; title: string; description: string; service: string; severity: string; symptoms: string[] };
export type InvestigationEvidence = { id: string; source: string; summary: string; supports: string[]; contradicts: string[] };
export type InvestigationHypothesis = { id: string; statement: string; confidence: number; status: string; evidence_ids: string[] };
export type InvestigationResult = {
  investigation_id: string | null;
  incident_id: string;
  observation: string;
  hypotheses: InvestigationHypothesis[];
  evidence: InvestigationEvidence[];
  consolidated_memory_ids: string[];
  actions: string[];
  correction: string | null;
  correction_memory_ids?: string[];
  complete: boolean;
  diagnosis: string | null;
  remediation: string[];
  reasoning_provider: string;
  reasoning_model: string | null;
};
export type PersistedInvestigation = {
  id: string;
  incident_id: string;
  observation: string;
  scenario: string;
  status: string;
  hypotheses: InvestigationHypothesis[];
  evidence: InvestigationEvidence[];
  retrieved_memory_ids: string[];
  consolidated_memory_ids: string[];
  actions: string[];
  action_count: number;
  correction: string | null;
  correction_memory_ids: string[];
  complete: boolean;
  diagnosis: string | null;
  remediation: string[];
  reasoning_provider: string;
  reasoning_model: string | null;
  created_at: string;
  completed_at: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `API request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getHealth(): Promise<ApiHealth> { return request('/health'); }
export function getDemoIncident(): Promise<DemoIncident> { return request('/incidents/demo'); }
export function getInvestigations(limit = 20): Promise<PersistedInvestigation[]> { return request(`/investigations?limit=${limit}`); }
export function getInvestigation(id: string): Promise<PersistedInvestigation> { return request(`/investigations/${encodeURIComponent(id)}`); }
export function startInvestigation(observation: string): Promise<InvestigationResult> {
  return request('/investigations', {
    method: 'POST',
    body: JSON.stringify({ incident_id: `INC-${Date.now()}`, observation, scenario: 'auto' }),
  });
}

export type CorrectionResult = { investigation_id: string; memory_id: string; memory_type: string; embedding_model: string; indexed_by: string };
export function submitCorrection(investigationId: string, correction: string): Promise<CorrectionResult> {
  return request(`/investigations/${encodeURIComponent(investigationId)}/corrections`, {
    method: 'POST',
    body: JSON.stringify({ correction, author: 'human' }),
  });
}
