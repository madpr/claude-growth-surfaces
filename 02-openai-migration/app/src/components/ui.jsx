// Shared primitives.
//
// Every visual here encodes a value the surface already knows, and recomputes
// with the rulebook. Nothing is a decorative trendline: a migration is a
// project with a composition, not a service with a time series.

export function Metric({ label, value, sub, tone, children }) {
  return (
    <div className="card metric">
      <span className="k">{label}</span>
      <span className="v" style={tone ? { color: `var(--${tone})` } : undefined}>{value}</span>
      {sub && <span className="s">{sub}</span>}
      {children && <div className="viz">{children}</div>}
    </div>
  )
}

// Composition of a whole, in proportion. Segments are [count, token, title].
export function SegBar({ segments }) {
  const total = segments.reduce((n, [c]) => n + c, 0) || 1
  return (
    <div className="segbar" role="img" aria-label={segments.map(([c, , t]) => `${c} ${t}`).join(', ')}>
      {segments.map(([count, token, title]) =>
        count > 0 ? (
          <span
            key={title}
            title={`${count} ${title}`}
            style={{ width: `${(count / total) * 100}%`, background: `var(--${token})` }}
          />
        ) : null,
      )}
    </div>
  )
}

// A filled proportion of a known whole.
export function Meter({ value, total, token = 'ok' }) {
  const pct = total ? (value / total) * 100 : 0
  return (
    <div className="meter" role="img" aria-label={`${value} of ${total}`}>
      <span style={{ width: `${pct}%`, background: `var(--${token})` }} />
    </div>
  )
}

// One cell per case, so the count on the card can be checked by eye.
export function Waffle({ cells }) {
  return (
    <div className="waffle" role="img" aria-label={cells.map((c) => c.title).join(', ')}>
      {cells.map((c, i) => (
        <span key={i} className={`cell cell-${c.state}`} title={c.title} />
      ))}
    </div>
  )
}

// Two bars on one scale, so the drop is the length difference.
export function CompareBars({ rows }) {
  const max = Math.max(...rows.map((r) => r.value)) || 1
  return (
    <div className="cmp">
      {rows.map((r) => (
        <div className="cmp-row" key={r.label}>
          <span className="cmp-label">{r.label}</span>
          <span className="cmp-track">
            <span style={{ width: `${(r.value / max) * 100}%`, background: `var(--${r.token})` }} />
          </span>
        </div>
      ))}
    </div>
  )
}

export function Chip({ kind = 'mute', children }) {
  return <span className={`chip chip-${kind}`}>{children}</span>
}

export function SectionHead({ title, count, right, sub }) {
  return (
    <div>
      <div className="sec-head">
        <h2>{title}</h2>
        {count != null && <span className="count">({count})</span>}
        {right && <span className="right">{right}</span>}
      </div>
      {sub && <p className="sub">{sub}</p>}
    </div>
  )
}
