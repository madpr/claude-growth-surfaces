import { useState } from 'react'
import { Chip, SectionHead } from '../components/ui.jsx'
import { parityResults, parityScore, parityNote, costModel, workload, project } from '../data.js'

const FIELDS = [
  ['requestsPerDay', 'Requests per day'],
  ['stablePrefixTokens', 'Stable prefix tokens (system + tools)'],
  ['variableInputTokens', 'Variable input tokens'],
  ['outputTokens', 'Output tokens'],
]

export default function Parity({ fixApplied, setFixApplied }) {
  const [w, setW] = useState(workload)
  const rows = parityResults(fixApplied)
  const score = parityScore(fixApplied)
  const cost = costModel(w)
  const regressions = rows.filter((c) => c.before === 'pass' && c.result === 'fail')
  const money = (n) => `$${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}`

  return (
    <div className="content">
      <SectionHead
        title="Parity gate"
        sub="A compiler cannot tell you whether a prompt still works, so the migration is gated on your own eval cases instead. Both runs use the same 12 cases and the same judge."
      />

      <div className="split">
        <div className="card big">
          <span className="k">Baseline · {project.source}</span>
          <span className="v">{score.before}/{score.total}</span>
          <span className="s">passing before the migration</span>
        </div>
        <div className="card big">
          <span className="k">Migrated · {project.target}</span>
          <span className="v" style={{ color: score.after < score.before ? 'var(--crit)' : 'var(--ok)' }}>
            {score.after}/{score.total}
          </span>
          <span className="s">
            {score.regressed
              ? `${score.regressed} regressed, ${score.recovered} recovered — gate holds the merge`
              : `no regressions, ${score.recovered} recovered`}
          </span>
        </div>
        <div className="card big">
          <span className="k">Cost per request</span>
          <span className="v" style={{ color: 'var(--ok)' }}>{cost.deltaPct}%</span>
          <span className="s">{money(cost.monthlySource)} → {money(cost.monthlyTarget)} per month</span>
        </div>
      </div>

      {regressions.length > 0 && (
        <div className="card card-pad" style={{ borderColor: '#EBC9C0', background: 'var(--crit-dim)' }}>
          <div className="sec-head">
            <h2 style={{ color: 'var(--crit)' }}>{regressions.length} regressions, one root cause</h2>
            <span className="right">
              <button className="btn btn-sm btn-primary" onClick={() => setFixApplied(true)}>
                Move constraints into validation
              </button>
            </span>
          </div>
          <p className="note" style={{ marginTop: 8, color: '#7C3D2E' }}>{parityNote}</p>
        </div>
      )}

      {fixApplied && (
        <div className="card card-pad" style={{ borderColor: '#C9E2D5', background: 'var(--ok-dim)' }}>
          <p className="note" style={{ color: '#255F46' }}>
            <b>Remedy applied.</b> The bounds that native structured outputs cannot express
            now run as application validation after parsing. All 12 cases pass, and the
            migration is clear to merge.{' '}
            <button className="btn btn-sm" style={{ marginLeft: 8 }} onClick={() => setFixApplied(false)}>
              Undo
            </button>
          </p>
        </div>
      )}

      <div className="card tw">
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Scenario</th>
              <th>Baseline</th>
              <th>Migrated</th>
              <th>Movement</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => {
              const moved =
                c.before === c.result ? null : c.result === 'pass' ? 'recovered' : 'regressed'
              return (
                <tr key={c.id}>
                  <td className="mono dim">{c.id}</td>
                  <td>{c.name}</td>
                  <td>{c.before === 'pass' ? <Chip kind="ok">Pass</Chip> : <Chip kind="crit">Fail</Chip>}</td>
                  <td>{c.result === 'pass' ? <Chip kind="ok">Pass</Chip> : <Chip kind="crit">Fail</Chip>}</td>
                  <td>
                    {moved === 'recovered' && <Chip kind="ok">Recovered</Chip>}
                    {moved === 'regressed' && <Chip kind="crit">Regressed · R4</Chip>}
                    {!moved && <span className="dim">—</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div>
        <SectionHead
          title="Cost model"
          sub="List prices, 1 September 2026. Prompt caching is unavailable through the OpenAI compatibility layer, so a like-for-like evaluation there never shows this. Edit the workload to match yours."
        />
        <div className="card card-pad" style={{ marginTop: 12, display: 'grid', gap: 18, gridTemplateColumns: 'minmax(240px, 1fr) minmax(240px, 1fr)' }}>
          <div className="calc">
            {FIELDS.map(([key, label]) => (
              <label key={key} style={{ display: 'contents' }}>
                <span>{label}</span>
                <input
                  type="number"
                  value={w[key]}
                  min="0"
                  onChange={(e) => setW({ ...w, [key]: Math.max(0, Number(e.target.value) || 0) })}
                />
              </label>
            ))}
            <label style={{ display: 'contents' }}>
              <span>Cache hit rate</span>
              <input
                type="number"
                step="0.01" min="0" max="1"
                value={w.cacheHitRate}
                onChange={(e) =>
                  setW({ ...w, cacheHitRate: Math.min(1, Math.max(0, Number(e.target.value) || 0)) })
                }
              />
            </label>
          </div>

          <div className="tw">
            <table>
              <thead>
                <tr><th>Path</th><th style={{ textAlign: 'right' }}>Per request</th><th style={{ textAlign: 'right' }}>Per month</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>{project.source} today</td>
                  <td className="mono num">${cost.source.toFixed(5)}</td>
                  <td className="mono num">{money(cost.monthlySource)}</td>
                </tr>
                <tr>
                  <td>{project.target}, no caching</td>
                  <td className="mono num">${cost.uncached.toFixed(5)}</td>
                  <td className="mono num dim">{money(cost.uncached * w.requestsPerDay * 30)}</td>
                </tr>
                <tr>
                  <td><b>{project.target}, caching on</b></td>
                  <td className="mono num"><b>${cost.target.toFixed(5)}</b></td>
                  <td className="mono num"><b>{money(cost.monthlyTarget)}</b></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
