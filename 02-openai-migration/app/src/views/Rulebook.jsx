import { Chip, SectionHead } from '../components/ui.jsx'
import { rules, callSites, summarise } from '../data.js'

export default function Rulebook({ modes, setModes, choices, setChoices }) {
  const s = summarise(modes)
  const sitesFor = (id) => callSites.filter((c) => c.rule === id).length

  return (
    <div className="content">
      <SectionHead
        title="Rulebook"
        count={rules.length}
        sub="One row per construct that differs between the two APIs. Mark a rule automatic to let the migration apply it unattended, or hold it for review. Changes recompute the call-site counts immediately."
        right={`${s.auto} automatic · ${s.decide} held`}
      />

      <div className="card">
        {rules.map((r) => (
          <div className="rule-row" key={r.id}>
            <span className="rule-id">{r.id}</span>

            <div>
              <div className="rule-c">{r.construct}</div>
              <div className="rule-note">
                {r.note}{' '}
                <a href={r.docs} target="_blank" rel="noreferrer">Docs ↗</a>
              </div>
            </div>

            <div>
              <div className="rule-e">{r.equivalent}</div>
              <div className="rule-note">
                {sitesFor(r.id)} call site{sitesFor(r.id) === 1 ? '' : 's'}
                {r.gain && <> · <Chip kind="acc">cost gain</Chip></>}
              </div>
            </div>

            <div className="rule-act">
              <div className="seg" role="group" aria-label={`${r.id} handling`}>
                <button
                  className={modes[r.id] === 'auto' ? 'on' : ''}
                  onClick={() => setModes({ ...modes, [r.id]: 'auto' })}
                >
                  Automatic
                </button>
                <button
                  className={modes[r.id] === 'decide' ? 'on' : ''}
                  onClick={() => setModes({ ...modes, [r.id]: 'decide' })}
                >
                  Hold
                </button>
              </div>

              {r.choice && modes[r.id] === 'auto' && (
                <label className="choice">
                  {r.choice.label}
                  <select
                    value={choices[r.id]}
                    onChange={(e) => setChoices({ ...choices, [r.id]: e.target.value })}
                  >
                    {r.choice.options.map((o) => (
                      <option key={o} value={o}>{o}</option>
                    ))}
                  </select>
                </label>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
