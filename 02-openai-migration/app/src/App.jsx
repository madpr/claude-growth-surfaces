import { useState } from 'react'
import Shell from './components/Shell.jsx'
import Migration from './views/Migration.jsx'
import { decisions, tests, testsAfter, project } from './data.js'

function StatusBar({ choices }) {
  const open = decisions.filter((d) => !choices[d.id]).length
  const passing = testsAfter(choices)
  const ready = open === 0 && passing === tests.total
  return (
    <div className="statusbar">
      <span>
        {ready
          ? 'All decisions settled and your tests pass.'
          : open > 0
            ? `${open} decision${open === 1 ? '' : 's'} left before this can merge.`
            : `${tests.total - passing} tests still failing.`}
      </span>
      <button className="btn btn-primary" disabled={!ready}>
        {ready ? 'Open pull request' : 'Blocked'}
      </button>
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
