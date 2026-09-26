const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

export type ApiHealth = { status: string; mode: string };
export type DemoIncident = { id: string; title: string; description: string; service: string; severity: string; symptoms: string[] };
export type InvestigationResult = { investigation_id: string | null; incident_id: string; observation: string; actions: string[]; correction: string | null; complete: boolean };

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
export function startInvestigation(observation: string): Promise<InvestigationResult> {
  return request('/investigations', {
    method: 'POST',
    body: JSON.stringify({ incident_id: `INC-${Date.now()}`, observation, scenario: 'bad_deployment' }),
  });
}
