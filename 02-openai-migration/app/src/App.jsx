import { useEffect, useState } from 'react'
import Shell from './components/Shell.jsx'
import { Chip, SectionHead } from './components/ui.jsx'
import Overview from './views/Overview.jsx'
import CallSites from './views/CallSites.jsx'
import Rulebook from './views/Rulebook.jsx'
import Parity from './views/Parity.jsx'
import { rules, project, summarise, parityScore } from './data.js'

const TABS = [
  ['overview', 'Overview'],
  ['sites', 'Call sites'],
  ['rulebook', 'Rulebook'],
  ['parity', 'Parity'],
  ['settings', 'Settings'],
]

// Other migrations in the workspace, so the list view is not a single row.
const PROJECTS = [
  { name: 'support-triage', repo: 'acme/support-triage', lang: 'Python', sites: 39, state: 'In review', tone: 'warn' },
  { name: 'billing-copilot', repo: 'acme/billing-copilot', lang: 'TypeScript', sites: 61, state: 'Merged', tone: 'ok' },
  { name: 'docs-search', repo: 'acme/docs-search', lang: 'Python', sites: 14, state: 'Merged', tone: 'ok' },
  { name: 'sales-agent', repo: 'acme/sales-agent', lang: 'TypeScript', sites: 88, state: 'Scanning', tone: 'mute' },
]

// Hash routing keeps deep links working on any static host.
function useHash() {
  const [hash, setHash] = useState(() => window.location.hash || '#/migrations')
  useEffect(() => {
    const on = () => setHash(window.location.hash || '#/migrations')
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return hash
}

export default function App() {
  const hash = useHash()
  const [modes, setModes] = useState(() => Object.fromEntries(rules.map((r) => [r.id, r.mode])))
  const [choices, setChoices] = useState(() =>
    Object.fromEntries(rules.filter((r) => r.choice).map((r) => [r.id, r.choice.value])),
  )
  const [fixApplied, setFixApplied] = useState(false)
  const [banner, setBanner] = useState(true)

  const parts = hash.replace(/^#\/?/, '').split('/').filter(Boolean)
  const inProject = parts[1] === project.name
  const tab = inProject && parts[2] ? parts[2] : 'overview'

  const nav = (h) => { window.location.hash = h }
  const go = (t) => nav(`#/migrations/${project.name}/${t}`)
  const s = summarise(modes)
  const score = parityScore(fixApplied)

  if (!inProject) {
    return (
      <Shell onHome={() => nav('#/migrations')}>
        <div className="topbar">
          <div className="crumbs">
            <h1 style={{ fontFamily: 'var(--sans)', fontSize: 18 }}>Migrations</h1>
            <span className="tag">Preview</span>
            <span className="right">
              <button className="btn btn-sm btn-primary">Scan a repository</button>
            </span>
          </div>
          <div className="tabs"><button className="tab active">Projects</button></div>
        </div>
        <div className="content">
          <SectionHead
            title="Projects"
            count={PROJECTS.length}
            sub="Repositories scanned for OpenAI SDK usage. A migration finds every call site, applies a rulebook, and gates the merge on your own eval cases."
          />
          <div className="card tw">
            <table>
              <thead>
                <tr><th>Project</th><th>Repository</th><th>Language</th><th>Call sites</th><th>State</th></tr>
              </thead>
              <tbody>
                {PROJECTS.map((p) => (
                  <tr
                    key={p.name}
                    style={{ cursor: p.name === project.name ? 'pointer' : 'default' }}
                    onClick={() => p.name === project.name && go('overview')}
                  >
                    <td><b>{p.name}</b></td>
                    <td className="mono dim">{p.repo}</td>
                    <td className="dim">{p.lang}</td>
                    <td className="mono num">{p.name === project.name ? s.total : p.sites}</td>
                    <td><Chip kind={p.tone}>{p.state}</Chip></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <SectionHead
              title="Starting a migration"
              sub="The scan runs in Claude Code, not here. Your source never leaves your machine or your CI — the Console holds the rulebook, the decisions and the parity history."
            />
            <div className="grid3" style={{ marginTop: 12 }}>
              <div className="card run">
                <div>
                  <h3>From the terminal</h3>
                  <p>Run it in the repository you want to migrate. Results appear here when it finishes.</p>
                </div>
                <Cmd lines={[
                  [['$ ', 'p'], ['claude '], ['/migrate-from-openai', 'c'], [' --to ', 'k'], ['claude-sonnet-5']],
                  [],
                  [['  scanning 11 files… 39 call sites', 'k']],
                  [['  rulebook: 34 automatic, 5 held', 'k']],
                  [['  → pushed to Console · Build › Migrations', 'k']],
                ]} />
              </div>

              <div className="card run">
                <div>
                  <h3>In CI</h3>
                  <p>
                    Reuses the Claude GitHub App already installed for Code Review. Opens a pull
                    request and reports the parity gate as a required status check.
                  </p>
                </div>
                <Cmd lines={[
                  [['- uses: ', 'k'], ['anthropics/claude-code-action@v1']],
                  [['  with:', 'k']],
                  [['    prompt: ', 'k'], ['/migrate-from-openai', 'c'], [' --to claude-sonnet-5']],
                ]} />
              </div>
            </div>
          </div>

          <p className="note">
            Prototype — seeded data. No repository is read, no inference is run, and{' '}
            <span className="mono">/migrate-from-openai</span> is proposed, not shipped.
          </p>
        </div>
      </Shell>
    )
  }

  return (
    <Shell onHome={() => nav('#/migrations')}>
      <div className="topbar">
        <div className="crumbs">
          <button
            className="muted"
            style={{ background: 'none', border: 'none', padding: 0 }}
            onClick={() => nav('#/migrations')}
          >
            Migrations
          </button>
          <span className="sep">/</span>
          <h1>{project.name}</h1>
          <span className="tag">{project.language}</span>
          <span className="right">
            <span className="select">{project.source} → {project.target}</span>
            <button className="btn btn-sm">Export patch</button>
            <button className="btn btn-sm btn-primary" disabled={score.after < score.before}>
              {score.after < score.before ? 'Blocked by parity' : 'Open pull request'}
            </button>
          </span>
        </div>
        <div className="tabs">
          {TABS.map(([k, label]) => (
            <button key={k} className={`tab${tab === k ? ' active' : ''}`} onClick={() => go(k)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'overview' && (
        <Overview modes={modes} choices={choices} banner={banner} setBanner={setBanner} go={go} fixApplied={fixApplied} />
      )}
      {tab === 'sites' && <CallSites modes={modes} />}
      {tab === 'rulebook' && (
        <Rulebook modes={modes} setModes={setModes} choices={choices} setChoices={setChoices} />
      )}
      {tab === 'parity' && <Parity fixApplied={fixApplied} setFixApplied={setFixApplied} />}
      {tab === 'settings' && <Settings />}
    </Shell>
  )
}

// JSX collapses literal newlines between elements, so command output is
// described as lines rather than written as a preformatted block.
function Cmd({ lines }) {
  return (
    <div className="cmdline">
      {lines.map((parts, i) => (
        <div key={i} className="cmdline-row">
          {parts.length === 0
            ? '\u00a0'
            : parts.map(([text, cls], j) => (
                <span key={j} className={cls}>{text}</span>
              ))}
        </div>
      ))}
    </div>
  )
}

function Settings() {
  const row = (label, value, note) => (
    <div className="rule-row" style={{ gridTemplateColumns: '1fr 240px' }} key={label}>
      <div>
        <div style={{ fontSize: 13.5, fontWeight: 550 }}>{label}</div>
        <div className="rule-note">{note}</div>
      </div>
      <div className="rule-act"><span className="select">{value}</span></div>
    </div>
  )
  return (
    <div className="content">
      <SectionHead title="Settings" sub="Defaults applied to every scan in this project." />
      <div className="card">
        {row('Target model', project.target, 'Rules are evaluated against this model. Sampling parameters and prefill are rejected on the current generation.')}
        {row('Default effort', 'low', 'Substituted wherever a temperature was removed.')}
        {row('Parity threshold', 'No regressions', 'The pull request stays blocked while any case that passed on the baseline fails after migration.')}
        {row('Prompt caching', 'Insert automatically', 'Adds a cache_control breakpoint after the stable system and tools prefix.')}
        {row('Merge approval', 'Repository admins', 'Who can override a blocked parity gate.')}
      </div>
    </div>
  )
}
