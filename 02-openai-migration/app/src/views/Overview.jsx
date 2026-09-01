import { Metric, Chip, SectionHead, SegBar, Meter, Waffle, CompareBars } from '../components/ui.jsx'
import {
  rules, callSites, summarise, costModel, workload, project,
  parityScore, parityResults, composition, openDecisions,
} from '../data.js'

export default function Overview({ modes, choices, banner, setBanner, go, fixApplied }) {
  const s = summarise(modes)
  const score = parityScore(fixApplied)
  const comp = composition(modes)
  const open = openDecisions(modes)
  const cases = parityResults(fixApplied)
  const cost = costModel(workload)
  const sitesFor = (id) => callSites.filter((c) => c.rule === id).length

  const blocking = rules.filter((r) => modes[r.id] === 'decide')
  const suggestions = rules.filter((r) => r.gain || (r.choice && modes[r.id] === 'auto'))

  return (
    <div className="content">
      {banner && (
        <div className="banner">
          <span aria-hidden="true">◈</span>
          <span>
            <b>Seeded scan.</b> {project.repo} at <code>{project.branch}</code> — {project.files} files,{' '}
            {s.total} OpenAI call sites, scanned {project.scannedAt}. Migrating{' '}
            <b>{project.source}</b> to <b>{project.target}</b>. Every figure here is
            derived from the scan, and rule changes recompute it live.
          </span>
          <span className="acts">
            <button onClick={() => setBanner(false)}>Dismiss</button>
          </span>
        </div>
      )}

      <div className="metrics">
        <Metric label="Call sites" value={s.total} sub={`across ${project.files} files`}>
          <SegBar
            segments={[
              [comp.mechanical, 'ink-3', 'mechanical'],
              [comp.choice, 'warn', 'need a default chosen'],
              [comp.blocking, 'crit', 'blocked'],
            ]}
          />
        </Metric>

        <Metric label="Auto-migratable" value={`${s.autoPct}%`} sub={`${s.auto} of ${s.total} sites`}>
          <Meter value={s.auto} total={s.total} token="ok" />
        </Metric>

        <Metric
          label="Needs a decision"
          value={s.decide}
          sub={open.length ? `${open.length} open rule${open.length === 1 ? '' : 's'}` : 'every rule has a default'}
        >
          <div className="ruletags">
            {open.length === 0
              ? <span className="dim" style={{ fontSize: 11.5 }}>nothing held</span>
              : open.map((o) => (
                  <Chip key={o.id} kind="crit">{o.id} · {o.sites}</Chip>
                ))}
          </div>
        </Metric>

        <Metric
          label="Parity"
          value={`${score.after}/${score.total}`}
          tone={score.regressed ? 'crit' : 'ok'}
          sub={score.regressed
            ? `${score.regressed} regressed · ${score.recovered} recovered`
            : `no regressions · ${score.recovered} recovered`}
        >
          <Waffle
            cells={cases.map((c) => ({
              state: c.result === 'fail'
                ? 'fail'
                : c.before === 'fail' ? 'gain' : 'pass',
              title: `${c.id} ${c.name}: ${c.before} → ${c.result}`,
            }))}
          />
        </Metric>

        <Metric label="Cost per request" value={`${cost.deltaPct}%`} tone="ok" sub="with caching on">
          <CompareBars
            rows={[
              { label: 'now', value: cost.source, token: 'ink-3' },
              { label: 'after', value: cost.target, token: 'accent' },
            ]}
          />
        </Metric>
      </div>

      <div>
        <SectionHead
          title="Blocking decisions"
          count={blocking.length}
          sub="The target is not a superset of the source. These cannot be resolved mechanically."
          right={<button className="btn btn-sm" onClick={() => go('rulebook')}>Open rulebook →</button>}
        />
        <div className="grid3" style={{ marginTop: 12 }}>
          {blocking.map((r) => (
            <div key={r.id} className="card sug">
              <div className="top">
                <Chip kind="crit">{r.id}</Chip>
                <Chip kind="mute">{sitesFor(r.id)} sites</Chip>
              </div>
              <h3>{r.construct}</h3>
              <p>{r.note}</p>
              <div className="foot">
                <button className="btn btn-sm" onClick={() => go('sites')}>View sites</button>
                <button className="btn btn-sm btn-primary" onClick={() => go('rulebook')}>Resolve</button>
              </div>
            </div>
          ))}
          {blocking.length === 0 && (
            <div className="card card-pad note">
              Nothing blocking. Every rule has a decision recorded — the migration can run
              unattended and stop at the parity gate.
            </div>
          )}
        </div>
      </div>

      <div>
        <SectionHead
          title="Suggested changes"
          sub="Applied automatically using the defaults recorded in the rulebook."
        />
        <div className="grid3" style={{ marginTop: 12 }}>
          {suggestions.map((r) => {
            const n = sitesFor(r.id)
            return (
              <div key={r.id} className="card sug">
                <div className="top">
                  <Chip kind={r.gain ? 'acc' : 'ok'}>
                    {r.gain ? `${cost.deltaPct}% cost` : `${n}/${n} fix`}
                  </Chip>
                  <Chip kind="mute">{r.id}</Chip>
                </div>
                <h3>{r.construct}</h3>
                <p><b>{r.equivalent}.</b> {r.note}</p>
                <div className="foot">
                  {r.choice && (
                    <span className="why">
                      {r.choice.label}: <b>{choices[r.id]}</b>
                    </span>
                  )}
                  <button className="btn btn-sm" onClick={() => go('rulebook')}>Open diff →</button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
