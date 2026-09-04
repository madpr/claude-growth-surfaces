import { useState } from 'react'
import Shell from './components/Shell.jsx'
import Migration from './views/Migration.jsx'
import { decisions, tests, testsAfter, blocking, project } from './data.js'

// Why the merge is blocked, from the data: how many decisions are still open,
// or which settled decision is holding the tests back and which of its options
// recovers them. The button always reads "Open pull request"; only its state
// changes, and the reason sits beside it.
function reason(choices) {
  const open = decisions.filter((d) => !choices[d.id]).length
  if (open > 0) return `${open} decision${open === 1 ? '' : 's'} left before this can merge.`
  const failing = tests.total - testsAfter(choices)
  if (failing === 0) return 'All decisions settled and your tests pass.'
  const held = blocking(choices).map(
    (b) =>
      `Held by ${b.decision.construct}: "${b.picked.label}" leaves ${b.left} failing, ` +
      `"${b.better.label}" recovers ${b.better.recovers}.`,
  )
  return [`${failing} test${failing === 1 ? '' : 's'} still failing.`, ...held].join(' ')
}

function StatusBar({ choices }) {
  const open = decisions.filter((d) => !choices[d.id]).length
  const ready = open === 0 && testsAfter(choices) === tests.total
  return (
    <div className="statusbar">
      <span>{reason(choices)}</span>
      <button className="btn btn-primary" disabled={!ready}>Open pull request</button>
    </div>
  )
}

export default function App() {
  const [choices, setChoices] = useState({})

  return (
    <Shell>
      <div className="topbar">
        <div className="crumbs">
          <span className="muted">Migrations</span>
          <span className="sep">/</span>
          <h1>{project.name}</h1>
          <span className="right">
            <span className="select">
              {project.source} <span className="dim">→</span> {project.target}
            </span>
          </span>
        </div>
      </div>
      <Migration choices={choices} setChoices={setChoices} />
      <StatusBar choices={choices} />
    </Shell>
  )
}
