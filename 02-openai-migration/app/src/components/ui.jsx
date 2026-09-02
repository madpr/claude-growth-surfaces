export function Chip({ kind = 'mute', children }) {
  return <span className={`chip chip-${kind}`}>{children}</span>
}

// Progressive detail. Everything a demo doesn't need lives behind one of these.
export function Detail({ summary, children }) {
  return (
    <details className="detail">
      <summary>{summary}</summary>
      <div className="detail-body">{children}</div>
    </details>
  )
}
