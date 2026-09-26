'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowUpRight,
  BrainCircuit,
  Check,
  CircleDot,
  Database,
  GitCommitHorizontal,
  Lightbulb,
  MessageSquareText,
  MemoryStick,
  Search,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  X,
  Zap,
  ChevronRight,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  getDemoIncident,
  getHealth,
  getInvestigation,
  getInvestigations,
  startInvestigation,
  submitCorrection,
  type InvestigationResult,
} from '@/lib/api';

const toolPresentation = {
  query_metrics: {
    icon: Activity,
    tone: 'blue',
    title: 'Queried service metrics',
  },
  search_logs: {
    icon: TerminalSquare,
    tone: 'amber',
    title: 'Searched production logs',
  },
  get_deployments: {
    icon: GitCommitHorizontal,
    tone: 'violet',
    title: 'Compared recent deployments',
  },
} as const;

function timelineFromResult(result: InvestigationResult) {
  const start = [
    {
      time: 'now',
      icon: Zap,
      tone: 'red',
      title: 'Investigation started',
      detail: result.observation,
    },
  ];
  const actions = result.actions.map((action, index) => {
    const [tool, ...detail] = action.split(': ');
    const presentation = toolPresentation[
      tool as keyof typeof toolPresentation
    ] ?? {
      icon: TerminalSquare,
      tone: 'blue',
      title: tool.replaceAll('_', ' '),
    };
    return {
      time: `+${index + 1}s`,
      ...presentation,
      detail: detail.join(': '),
    };
  });
  const finish = result.complete
    ? [
        {
          time: `+${actions.length + 1}s`,
          icon: Check,
          tone: 'green',
          title: 'Diagnostic pass completed',
          detail: `${actions.length} safe tools executed by FastAPI.`,
        },
      ]
    : [];
  return [...start, ...actions, ...finish];
}

const memories = [
  {
    type: 'EPISODIC',
    color: 'violet',
    score: '91%',
    title: 'INC-031 · Redis connection leak',
    body: 'Same timeout signature and checkout-only impact. Pool waiters are the strongest discriminator.',
    meta: 'Used 4 times · 3 months ago',
  },
  {
    type: 'HUMAN FEEDBACK',
    color: 'cyan',
    score: '88%',
    title: 'Check deploy diffs before provider status',
    body: 'Maya corrected this assumption: provider errors surface as 502s, not pool-wait timeouts.',
    meta: 'Confirmed twice · 12 days ago',
  },
  {
    type: 'PROCEDURAL',
    color: 'amber',
    score: '83%',
    title: 'Checkout timeout triage',
    body: 'Compare latency by dependency, then correlate pool saturation with the latest config changes.',
    meta: 'Success rate 86% · Used 7 times',
  },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<
    'investigation' | 'memory' | 'comparison'
  >('investigation');
  const [query, setQuery] = useState(
    'Checkout requests started timing out after the latest deploy.',
  );
  const [running, setRunning] = useState(false);
  const [backendStatus, setBackendStatus] = useState<
    'checking' | 'connected' | 'offline'
  >('checking');
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [correctionText, setCorrectionText] = useState('');
  const [savingCorrection, setSavingCorrection] = useState(false);
  const [correctionError, setCorrectionError] = useState<string | null>(null);
  const [savedCorrectionId, setSavedCorrectionId] = useState<string | null>(null);
  const [resultOrigin, setResultOrigin] = useState<'live' | 'restored' | null>(
    null,
  );
  const [baselineId, setBaselineId] = useState<string | null>(null);
  const [firstRun, setFirstRun] = useState<InvestigationResult | null>(null);
  const [secondRun, setSecondRun] = useState<InvestigationResult | null>(null);
  const timeline = result ? timelineFromResult(result) : [];

  const evidenceById = useMemo(
    () =>
      new Map(result?.evidence.map((item) => [item.id, item.summary]) ?? []),
    [result],
  );

  useEffect(() => {
    let active = true;
    Promise.all([getHealth(), getDemoIncident(), getInvestigations(1)])
      .then(async ([, , saved]) => {
        if (!active) return;
        setBackendStatus('connected');
        setQuery(
          'Checkout requests started timing out after the latest deploy.',
        );
        if (saved[0]) {
          const latest = { ...saved[0], investigation_id: saved[0].id, memories: saved[0].retrieved_memory_ids.map((id) => ({ id, type: 'human_feedback', title: 'Retrieved correction', content: 'Correction retrieved from Atlas' })) };
          setResult(latest);
          setResultOrigin('restored');
          if (saved[0].baseline_investigation_id) {
            const baseline = await getInvestigation(saved[0].baseline_investigation_id);
            if (!active) return;
            setBaselineId(baseline.id);
            setFirstRun({ ...baseline, investigation_id: baseline.id, memories: baseline.retrieved_memory_ids.map((id) => ({ id, type: 'human_feedback', title: 'Retrieved correction', content: 'Correction retrieved from Atlas' })) });
            setSecondRun(latest);
          } else if (saved[0].correction) {
            setBaselineId(saved[0].id);
            setFirstRun(latest);
          }
        }
      })
      .catch(() => {
        if (active) setBackendStatus('offline');
      });
    return () => {
      active = false;
    };
  }, []);

  async function runInvestigation() {
    if (!query.trim() || running) return;
    setRunning(true);
    setApiError(null);
    try {
      const investigation = await startInvestigation(query.trim(), baselineId);
      setResult(investigation);
      if (baselineId) setSecondRun(investigation);
      setCorrectionText('');
      setSavedCorrectionId(null);
      setResultOrigin('live');
      setBackendStatus('connected');
    } catch (error) {
      setBackendStatus('offline');
      setApiError(
        error instanceof Error
          ? error.message
          : 'The investigation API could not be reached.',
      );
    } finally {
      setRunning(false);
    }
  }

  async function saveCorrection() {
    const investigationId = result?.investigation_id;
    if (!investigationId || !correctionText.trim() || savingCorrection) return;
    setSavingCorrection(true);
    setCorrectionError(null);
    try {
      const saved = await submitCorrection(investigationId, correctionText.trim());
      setFirstRun({ ...result, correction: correctionText.trim(), correction_memory_ids: [...(result.correction_memory_ids ?? []), saved.memory_id] });
      setBaselineId(investigationId);
      setSecondRun(null);
      setSavedCorrectionId(saved.memory_id);
      setResult((current) => current ? {
        ...current,
        correction: correctionText.trim(),
        correction_memory_ids: [...(current.correction_memory_ids ?? []), saved.memory_id],
      } : current);
      setCorrectionText('');
    } catch (error) {
      setCorrectionError(error instanceof Error ? error.message : 'The correction could not be saved.');
    } finally {
      setSavingCorrection(false);
    }
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <BrainCircuit size={19} />
          </div>
          <span>Incident Memory</span>
          <Badge className="beta">BETA</Badge>
        </div>
        <nav className="topnav" aria-label="Primary">
          {(['investigation', 'memory', 'comparison'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={activeTab === tab ? 'active' : ''}
            >
              {tab === 'investigation' ? 'Live investigation' : tab}
            </button>
          ))}
        </nav>
        <div className="system">
          <span
            className={`status-dot ${backendStatus === 'offline' ? 'offline' : ''}`}
          />{' '}
          {backendStatus === 'connected'
            ? 'FastAPI connected'
            : backendStatus === 'offline'
              ? 'FastAPI offline'
              : 'Checking FastAPI'}{' '}
          <span className="divider" /> <Database size={15} /> Atlas connected
        </div>
      </header>
      <section className="alert-strip">
        <div className="alert-icon">
          <Activity size={18} />
        </div>
        <div>
          <p className="eyebrow red">ACTIVE INCIDENT · INC-042</p>
          <h1>Checkout requests timing out after latest deploy</h1>
        </div>
        <div className="alert-meta">
          <span>SEV-2</span>
          <span>checkout</span>
          <span>14:32 EDT</span>
        </div>
      </section>
      <section className="command-wrap">
        <div className="command">
          <Search size={19} />
          <input
            aria-label="Incident description"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Button
            onClick={runInvestigation}
            disabled={running || !query.trim()}
            className="run-button"
          >
            {running ? 'Investigating…' : 'Investigate'}{' '}
            <ArrowUpRight size={16} />
          </Button>
        </div>
        <p>
          <ShieldCheck size={13} /> Read-only diagnostics · fixes run only in
          sandbox
        </p>
        {apiError && (
          <div className="api-error" role="alert">
            <X size={14} />
            <span>
              FastAPI is unavailable. Start it on port 8000 and try again.
            </span>
          </div>
        )}
      </section>

      {activeTab === 'investigation' && (
        <div className="workspace-grid">
          <section className="panel timeline-panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">LIVE INVESTIGATION</p>
                <h2>Evidence trail</h2>
              </div>
              <span className={`live-pill ${result ? 'api-backed' : ''}`}>
                <span />{' '}
                {resultOrigin === 'restored'
                  ? 'Restored from Atlas'
                  : result
                    ? `${result.reasoning_provider === 'openrouter' ? 'OpenRouter' : 'Fallback'} result`
                    : 'Ready'}
              </span>
            </div>
            {timeline.length ? (
              <div className="timeline">
                {timeline.map((item, index) => (
                  <div
                    className="timeline-item"
                    key={`${item.time}-${item.title}`}
                  >
                    <div className={`timeline-icon ${item.tone}`}>
                      <item.icon size={16} />
                    </div>
                    <div className="timeline-copy">
                      <div>
                        <time>{item.time}</time>
                        <strong>{item.title}</strong>
                      </div>
                      <p>{item.detail}</p>
                    </div>
                    {index < timeline.length - 1 && (
                      <div className="timeline-line" />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="timeline-empty">
                <TerminalSquare size={22} />
                <strong>No investigation run yet</strong>
                <p>
                  Describe the production symptom above, then select Investigate
                  to gather read-only evidence.
                </p>
              </div>
            )}
            {result && (
              <div className="diagnosis">
                <div className="diagnosis-title">
                  <Check size={17} />
                  <strong>Evidence-backed diagnosis</strong>
                  <Badge>
                    {Math.round(
                      Math.max(
                        ...result.hypotheses.map((h) => h.confidence),
                        0,
                      ) * 100,
                    )}
                    % confidence
                  </Badge>
                </div>
                <p>
                  {result.diagnosis ??
                    'The diagnostic pass completed without a confirmed root cause.'}
                </p>
                <div className="remedy">
                  <Lightbulb size={16} />
                  <span>
                    <b>Remediation plan:</b>{' '}
                    {result.remediation.length
                      ? result.remediation.join(' ')
                      : 'No remediation has been proposed.'}
                  </span>
                </div>
                <div className="consolidation-status">
                  <MemoryStick size={14} />
                  <span><b>{result.consolidated_memory_ids?.length ?? 0} durable memories created</b> · embedded through OpenRouter and indexed in Atlas</span>
                </div>
              </div>
            )}
            {result?.complete && (
              <div className="correction-card">
                <div className="correction-heading">
                  <MessageSquareText size={17} />
                  <div>
                    <strong>Correct this investigation</strong>
                    <p>Teach the agent what it got wrong or missed. Your correction becomes durable human feedback.</p>
                  </div>
                </div>
                {result.correction ? (
                  <div className="correction-saved" role="status">
                    <Check size={16} />
                    <div><strong>Correction stored in memory</strong><p>{result.correction}</p><small>{savedCorrectionId ?? result.correction_memory_ids?.at(-1)} · embedded and searchable in Atlas</small></div>
                  </div>
                ) : (
                  <>
                    <textarea aria-label="Human correction" value={correctionText} onChange={(event) => setCorrectionText(event.target.value)} placeholder="Example: Provider failures appear as 502s; Redis pool waits indicate connection exhaustion." rows={3} />
                    <div className="correction-actions">
                      <span>Saved as human_feedback with investigation provenance</span>
                      <Button onClick={saveCorrection} disabled={!correctionText.trim() || savingCorrection}>{savingCorrection ? 'Learning…' : 'Save correction'}</Button>
                    </div>
                    {correctionError && <p className="correction-error" role="alert">{correctionError}</p>}
                  </>
                )}
              </div>
            )}
          </section>
          <aside className="side-stack">
            <section className="panel memory-panel">
              <div className="panel-head">
                <div>
                  <p className="eyebrow">RETRIEVED MEMORY</p>
                  <h2>What the team already knows</h2>
                </div>
                <BrainCircuit size={19} />
              </div>
              <div className="memory-list">
                {memories.map((m) => (
                  <article className="memory-card" key={m.title}>
                    <div className="memory-label">
                      <span className={m.color}>{m.type}</span>
                      <b>{m.score}</b>
                    </div>
                    <h3>{m.title}</h3>
                    <p>{m.body}</p>
                    <footer>{m.meta}</footer>
                  </article>
                ))}
              </div>
            </section>
          </aside>
          <section className="panel hypothesis-panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">REASONING STATE</p>
                <h2>Current hypotheses</h2>
              </div>
              <span className="action-count">
                {result?.actions.length ?? 0} / 20 actions
              </span>
            </div>
            {result?.hypotheses.length ? (
              <div className="hypothesis-list">
                {result.hypotheses.map((hypothesis, index) => {
                  const confirmed = hypothesis.status === 'confirmed';
                  const confidence = Math.round(hypothesis.confidence * 100);
                  const evidence = hypothesis.evidence_ids
                    .map((id) => evidenceById.get(id))
                    .filter(Boolean)
                    .join(' ');
                  return (
                    <article className="hypothesis" key={hypothesis.id}>
                      <span className="rank">
                        {String(index + 1).padStart(2, '0')}
                      </span>
                      <div className="hyp-main">
                        <div className="hyp-title">
                          <h3>{hypothesis.statement}</h3>
                          <span className={confirmed ? 'confirmed' : 'ruled'}>
                            {confirmed ? <Check size={12} /> : <X size={12} />}{' '}
                            {hypothesis.status.replaceAll('_', ' ')}
                          </span>
                        </div>
                        <p>{evidence || 'No linked evidence was recorded.'}</p>
                        <Progress
                          value={confidence}
                          className={
                            confirmed ? 'progress-good' : 'progress-muted'
                          }
                        />
                      </div>
                      <strong>{confidence}%</strong>
                    </article>
                  );
                })}
              </div>
            ) : (
              <div className="hypothesis-empty">
                <BrainCircuit size={20} />
                <span>Hypotheses will appear after evidence is gathered.</span>
              </div>
            )}
          </section>
        </div>
      )}
      {activeTab === 'memory' && <MemoryView />}
      {activeTab === 'comparison' && (
        <Comparison first={firstRun} second={secondRun} onReset={() => { setBaselineId(null); setFirstRun(null); setSecondRun(null); setResult(null); setActiveTab('investigation'); }} />
      )}
      <footer className="page-footer">
        <span>
          <CircleDot size={13} /> Investigation checkpoint saved
        </span>
        <span>MongoDB Atlas · agent harness v0.3.1</span>
      </footer>
    </main>
  );
}

function MemoryView() {
  return (
    <section className="memory-page">
      <div className="memory-hero">
        <p className="eyebrow">ORGANIZATIONAL MEMORY</p>
        <h2>Not a transcript archive. A system that revises what it knows.</h2>
        <p>
          Every memory carries provenance, confidence, usage, and contradiction
          history.
        </p>
      </div>
      <div className="memory-types">
        {[
          [
            'Episodic',
            'What happened',
            '12',
            'Individual incidents with symptoms, evidence, root causes, and fixes.',
          ],
          [
            'Semantic',
            'What is true',
            '28',
            'Stable facts about services, dependencies, and failure signatures.',
          ],
          [
            'Procedural',
            'What works',
            '9',
            'Reusable debugging strategies promoted from successful investigations.',
          ],
          [
            'Negative',
            'What failed',
            '17',
            'Dead ends and the evidence that ruled them out.',
          ],
          [
            'Human feedback',
            'What the team taught it',
            '6',
            'Corrections, preferences, and local operational knowledge.',
          ],
        ].map(([title, kicker, count, body]) => (
          <article key={title}>
            <div>
              <MemoryStick size={18} />
              <span>{count}</span>
            </div>
            <p>{kicker}</p>
            <h3>{title}</h3>
            <p>{body}</p>
            <button>
              Explore memories <ChevronRight size={14} />
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

function Comparison({ first, second, onReset }: { first: InvestigationResult | null; second: InvestigationResult | null; onReset: () => void }) {
  const confidence = (run: InvestigationResult | null) => Math.round(Math.max(...(run?.hypotheses.map((item) => item.confidence) ?? [0])) * 100);
  const formatTime = (milliseconds: number | undefined) => milliseconds ? `${(milliseconds / 1000).toFixed(1)}s` : '—';
  const stepsSaved = first && second ? first.actions.length - second.actions.length : 0;
  const correctionApplied = Boolean(second?.memories?.length);
  const improved = Boolean(first && second && correctionApplied && second.actions.length < first.actions.length);
  return (
    <section className="comparison-page">
      <div className="comparison-head">
        <div>
          <p className="eyebrow">MEMORY PAYOFF</p>
          <h2>The second incident is where the agent proves it learned.</h2>
        </div>
        <div className="comparison-actions"><Badge>{improved ? 'Learning demonstrated' : second ? 'Learning not applied' : first ? 'Correction saved · run again' : 'Run → correct → rerun'}</Badge>{second && <Button onClick={onReset}>Start new experiment</Button>}</div>
      </div>
      <div className="metric-grid">
        {[
          ['Investigation steps', second ? String(second.actions.length) : '—', first && second ? `${first.actions.length} → ${second.actions.length}` : 'Awaiting both runs'],
          ['Time to diagnosis', formatTime(second?.duration_ms), first && second ? `${formatTime(first.duration_ms)} → ${formatTime(second.duration_ms)}` : 'Measured by API'],
          ['Dead ends', second ? String(second.dead_end_count) : '—', first && second ? `${first.dead_end_count} → ${second.dead_end_count}` : 'Evidence-backed'],
          ['Final confidence', second ? `${confidence(second)}%` : '—', first && second ? `${confidence(first)}% → ${confidence(second)}%` : 'Awaiting rerun'],
        ].map(([label, value, delta]) => (
          <article key={label}>
            <p>{label}</p>
            <strong>{value}</strong>
            <span>{delta}</span>
          </article>
        ))}
      </div>
      <div className="learning-card">
        <div className="spark">
          <Sparkles size={21} />
        </div>
        <div>
          <p className="eyebrow">CORRECTION REMEMBERED</p>
          <h3>{first?.correction ? `“${first.correction}”` : 'Complete a run and submit a correction to begin the experiment.'}</h3>
          <p>
            {second ? correctionApplied ? `The second investigation retrieved ${second.memories.length} correction and used ${Math.max(0, stepsSaved)} fewer diagnostic actions.` : 'No correction was retrieved, so this run does not demonstrate learning. Start a new experiment or verify the incident belongs to the same service.' : first ? 'Run a related incident now. The harness will retrieve this correction through Atlas Vector Search before planning.' : 'The comparison will use persisted action counts, elapsed time, dead ends, confidence, and retrieved memory provenance.'}
          </p>
        </div>
        <Badge>{correctionApplied ? 'Applied automatically' : second ? 'Not retrieved' : 'Waiting'}</Badge>
      </div>
    </section>
  );
}
