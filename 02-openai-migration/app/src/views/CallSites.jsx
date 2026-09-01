import { useState, useMemo } from 'react'
import { Chip, SectionHead } from '../components/ui.jsx'
import { callSites, ruleById, siteStatus, summarise } from '../data.js'

export default function CallSites({ modes }) {
  const [q, setQ] = useState('')
  const [filter, setFilter] = useState('all')
  const s = summarise(modes)

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return callSites.filter((c) => {
      const status = siteStatus(c, modes)
      if (filter !== 'all' && status !== filter) return false
      if (!needle) return true
      return (
        c.file.toLowerCase().includes(needle) ||
        c.symbol.toLowerCase().includes(needle) ||
        c.rule.toLowerCase().includes(needle) ||
        ruleById[c.rule].construct.toLowerCase().includes(needle)
      )
    })
  }, [q, filter, modes])

  return (
    <div className="content">
      <div>
        <SectionHead
          title="Call sites"
          count={s.total}
          sub="Every place the OpenAI SDK is used. Status follows the rulebook decision the site is bound to."
        />
        <div className="filters" style={{ marginTop: 12 }}>
          <input
            className="search"
            placeholder="Filter by file, symbol, or rule…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          {[
            ['all', `All ${s.total}`],
            ['auto', `Auto ${s.auto}`],
            ['decide', `Needs a decision ${s.decide}`],
          ].map(([k, label]) => (
            <button
              key={k}
              className={`btn btn-sm${filter === k ? ' btn-primary' : ''}`}
              onClick={() => setFilter(k)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="card tw">
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Line</th>
              <th>Symbol</th>
              <th>Construct</th>
              <th>Rule</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c, i) => {
              const rule = ruleById[c.rule]
              const status = siteStatus(c, modes)
              return (
                <tr key={`${c.file}:${c.line}:${i}`}>
                  <td className="mono">{c.file}</td>
                  <td className="mono num dim">{c.line}</td>
                  <td className="mono dim">{c.symbol}</td>
                  <td>{rule.construct}</td>
                  <td><Chip kind="mute">{c.rule}</Chip></td>
                  <td>
                    {status === 'decide'
                      ? <Chip kind="crit">Needs a decision</Chip>
                      : rule.gain
                        ? <Chip kind="acc">Auto · gain</Chip>
                        : <Chip kind="ok">Auto</Chip>}
                  </td>
                </tr>
              )
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="dim" style={{ padding: '22px 14px' }}>
                  No call sites match “{q}”.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
