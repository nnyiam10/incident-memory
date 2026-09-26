const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

export type ApiHealth = { status: string; mode: string };
export type DemoIncident = { id: string; title: string; description: string; service: string; severity: string; symptoms: string[] };
export type InvestigationEvidence = { id: string; source: string; summary: string; supports: string[]; contradicts: string[] };
export type InvestigationHypothesis = { id: string; statement: string; confidence: number; status: string; evidence_ids: string[] };
export type RetrievedMemory = { id: string; type: string; title: string; content: string; score?: number };
export type InvestigationResult = {
  investigation_id: string | null;
  incident_id: string;
  observation: string;
  hypotheses: InvestigationHypothesis[];
  evidence: InvestigationEvidence[];
  memories: RetrievedMemory[];
  consolidated_memory_ids: string[];
  baseline_investigation_id: string | null;
  actions: string[];
  correction: string | null;
  correction_memory_ids?: string[];
  complete: boolean;
  diagnosis: string | null;
  remediation: string[];
  reasoning_provider: string;
  reasoning_model: string | null;
  duration_ms: number;
  dead_end_count: number;
  harness_version: string;
  harness_config: Record<string, unknown>;
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
  baseline_investigation_id: string | null;
  actions: string[];
  action_count: number;
  correction: string | null;
  correction_memory_ids: string[];
  complete: boolean;
  diagnosis: string | null;
  remediation: string[];
  reasoning_provider: string;
  reasoning_model: string | null;
  duration_ms: number;
  dead_end_count: number;
  harness_version: string;
  harness_config: Record<string, unknown>;
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
export function startInvestigation(observation: string, baselineInvestigationId?: string | null): Promise<InvestigationResult> {
  return request('/investigations', {
    method: 'POST',
    body: JSON.stringify({ incident_id: `INC-${Date.now()}`, observation, scenario: 'auto', baseline_investigation_id: baselineInvestigationId ?? null }),
  });
}

export type CorrectionResult = { investigation_id: string; memory_id: string; memory_type: string; embedding_model: string; indexed_by: string };
export function submitCorrection(investigationId: string, correction: string): Promise<CorrectionResult> {
  return request(`/investigations/${encodeURIComponent(investigationId)}/corrections`, {
    method: 'POST',
    body: JSON.stringify({ correction, author: 'human' }),
  });
}

export type HarnessVersion = {
  version: string;
  status: 'active' | 'candidate' | 'retired';
  reasoning_model: string;
  allowed_tools: string[];
  tool_order_policy: string;
  context_policy: { types: string[]; limit: number; minimum_score: number; baseline_feedback_only: boolean };
  minimum_evidence_without_memory: number;
  minimum_evidence_with_feedback: number;
  max_actions: number;
  parent_version: string | null;
  created_by: string;
  promoted_by: string | null;
  evaluation_status: 'not_run' | 'running' | 'passed' | 'failed';
  latest_evaluation_id: string | null;
  created_at: string;
  promoted_at: string | null;
};
export type CreateHarnessCandidate = Omit<HarnessVersion, 'status' | 'promoted_by' | 'created_at' | 'promoted_at'>;
export function getHarnessVersions(): Promise<HarnessVersion[]> { return request('/harnesses'); }
export function createHarnessCandidate(candidate: CreateHarnessCandidate): Promise<HarnessVersion> {
  return request('/harnesses', { method: 'POST', body: JSON.stringify(candidate) });
}
export function promoteHarnessVersion(version: string): Promise<HarnessVersion> {
  return request(`/harnesses/${encodeURIComponent(version)}/promote`, { method: 'POST', body: JSON.stringify({ confirmed: true, approved_by: 'human' }) });
}
export type EvaluationCase = { scenario: string; observation: string; expected_terms: string[]; diagnosis: string; accurate: boolean; action_count: number; duration_ms: number };
export type EvaluationMetrics = { version: string; accuracy: number; total_actions: number; total_duration_ms: number; cases: EvaluationCase[] };
export type HarnessEvaluation = { id: string; active_version: string; candidate_version: string; baseline: EvaluationMetrics; candidate: EvaluationMetrics; passed: boolean; reasons: string[]; created_at: string };
export function runHarnessEvaluation(version: string): Promise<HarnessEvaluation> {
  return request(`/evaluations/harnesses/${encodeURIComponent(version)}`, { method: 'POST' });
}
