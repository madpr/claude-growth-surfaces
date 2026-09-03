import {
  project, automatic, autoSites, decisions, decisionSites, totalSites,
  tests, testsAfter, cost, callSites,
} from '../data.js'
import { Chip, Detail } from '../components/ui.jsx'

// True when the options differ on effect, which is when the effect is worth showing.
const discriminates = (d) => new Set(d.options.map((o) => o.effect)).size > 1

const money = (n) => `$${Math.round(n).toLocaleString('en-US')}`

export default function Migration({ choices, setChoices }) {
  const open = decisions.filter((d) => !choices[d.id])
  const passing = testsAfter(choices)
  const ready = open.length === 0 && passing === tests.total

  return (
    <div className="page">
      <p className="lede">
        Scanned <b>{project.repo}</b> {project.scannedAt} — {project.files} files,{' '}
        <b>{totalSites} places you call OpenAI</b>.
      </p>

      <div className="split2">
        <div className="card stat">
          <span className="n">{autoSites}</span>
          <span className="l">rewritten for you</span>
        </div>
        <div className="card stat">
          <span className={`n${open.length ? ' hot' : ''}`}>{decisionSites}</span>
          <span className="l">
            need a decision{open.length === 0 && <> — <b>all settled</b></>}
          </span>
        </div>
      </div>

      <section>
        <h2>
          Your decisions
          {open.length > 0 && <span className="count">{open.length} left</span>}
        </h2>
        <p className="sub">
          Claude can't settle these. The target API can't express what your code assumes.
        </p>

        {decisions.map((d) => {
          const picked = choices[d.id]
          return (
            <div className={`card decision${picked ? ' done' : ''}`} key={d.id}>
              <div className="d-head">
                <code className="d-construct">{d.construct}</code>
                <Chip kind={picked ? 'ok' : 'crit'}>
                  {picked ? 'decided' : `${d.sites} sites`}
                </Chip>
              </div>

              <dl className="fields">
                <dt>Held because</dt>
                <dd>{d.reason}</dd>

                <dt>Values</dt>
                <dd className="mono">{d.offending.join('  ·  ')}</dd>

                <dt>Failing tests</dt>
                <dd className="mono">
                  {d.failingTests.length ? d.failingTests.join('  ·  ') : <span className="dim">none</span>}
                </dd>

                <dt>Decision</dt>
                <dd>
                  <div className="d-opts">
                    {d.options.map((o) => (
                      <button
                        key={o.id}
                        className={`opt${picked === o.id ? ' on' : ''}`}
                        onClick={() =>
                          setChoices({ ...choices, [d.id]: picked === o.id ? undefined : o.id })
                        }
                      >
                        {o.label}
                        {/* Shown only where it separates the options. A value
                            identical across every choice tells you nothing. */}
                        {discriminates(d) && <span className="opt-n">{o.effect}</span>}
                      </button>
                    ))}
                  </div>
                </dd>
              </dl>
            </div>
          )
        })}
      </section>

      <section>
        <h2>Does it still work?</h2>
        <p className="sub">
          No compiler tells you whether a prompt still works, so the merge waits on your
          own tests.
        </p>

        <div className="card proof">
          <div className="proof-row">
            <span className="p-k">Your test suite</span>
            <span className="p-v">
              <b>{tests.baseline}/{tests.total}</b> on OpenAI
              <span className="arr">→</span>
              <b className={passing < tests.baseline ? 'bad' : 'good'}>
                {passing}/{tests.total}
              </b> on Claude
            </span>
            <span className="p-n">
              {passing < tests.baseline
                ? `${tests.regressed} regressed — merge blocked`
                : `${tests.recovered} cases recovered`}
            </span>
          </div>
          <div className="proof-row">
            <span className="p-k">Cost per month</span>
            <span className="p-v">
              <b>{money(cost.sourceMonth)}</b>
              <span className="arr">→</span>
              <b className="good">{money(cost.targetMonth)}</b>
              <Chip kind="acc">{cost.deltaPct}%</Chip>
            </span>
            <span className="p-n">Prompt caching, unavailable through the compatibility layer</span>
          </div>
        </div>
      </section>

      <Detail summary={`What gets rewritten without asking (${autoSites} sites)`}>
        <table>
          <tbody>
            {automatic.map((a) => (
              <tr key={a.what}>
                <td>{a.what}</td>
                <td className="num dim">{a.sites}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Detail>

      <Detail summary={`Every call site (${totalSites})`}>
        <table>
          <tbody>
            {callSites.map(([file, line, what, owner], i) => (
              <tr key={i}>
                <td className="mono">{file}</td>
                <td className="num dim mono">{line}</td>
                <td>{what}</td>
                <td>
                  {owner === 'auto'
                    ? <span className="dim">automatic</span>
                    : <Chip kind={choices[owner] ? 'ok' : 'crit'}>{owner}</Chip>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="note">
          Showing {callSites.length} of {totalSites}. Seeded data — no repository is read.
        </p>
      </Detail>

      <p className="note">
        Prototype on seeded data. No repository is read, no inference is run, and{' '}
        <span className="mono">/migrate-from-openai</span> is proposed, not shipped.
      </p>

    </div>
  )
}
