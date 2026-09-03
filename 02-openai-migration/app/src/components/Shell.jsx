// The Console frame, transcribed from the live sidebar on platform.claude.com.
//
// Only one entry is invented: Build -> Migrations, the surface this prototype
// proposes. It sits under Build alongside Playground because it is a
// build-time tool, and carries the same "New" badge the Console already uses.

const GROUPS = [
  {
    label: 'Build',
    items: [
      { label: 'Playground', badge: 'New' },
      { label: 'Migrations', badge: 'New', ours: true },
      { label: 'Files' },
      { label: 'Skills' },
      { label: 'Batches' },
    ],
  },
  {
    label: 'Managed Agents',
    items: [
      { label: 'Quickstart' }, { label: 'Agents' }, { label: 'Sessions' },
      { label: 'Deployments' }, { label: 'Environments' },
      { label: 'Credential vaults' }, { label: 'Memory stores' },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { label: 'Usage' }, { label: 'Caching' }, { label: 'Rate limits' },
      { label: 'Cost' }, { label: 'Logs' },
    ],
  },
  {
    label: 'Claude Code',
    items: [{ label: 'Usage' }, { label: 'Settings' }],
  },
  {
    label: 'Manage',
    items: [
      { label: 'Rate limits' }, { label: 'Spend limits' }, { label: 'Service accounts' },
      { label: 'App Integrations', badge: 'Beta' }, { label: 'Privacy controls' },
      { label: 'Security' }, { label: 'Webhooks' }, { label: 'Tags' },
      { label: 'Notifications' },
    ],
  },
]

export default function Shell({ children }) {
  return (
    <div className="app">
      <aside className="side">
        <div className="ws">
          <span className="dot" aria-hidden="true" />
          <span className="ws-name">Default<span>default</span></span>
          <span className="caret">▾</span>
        </div>

        <div className="omni">
          <span>Search Console…</span>
          <kbd>⌘K</kbd>
        </div>

        <nav className="nav">
          <button className="nav-item">Dashboard</button>
          <button className="nav-item">API keys</button>

          {GROUPS.map((g) => (
            <div className="nav-group" key={g.label}>
              <div className="nav-label">{g.label}</div>
              {g.items.map((it) => (
                <button
                  key={g.label + it.label}
                  className={`nav-item${it.ours ? ' active' : ''}`}
                >
                  {it.label}
                  {it.badge && (
                    <span className={it.badge === 'Beta' ? 'badge-beta' : 'badge-new'}>
                      {it.badge}
                    </span>
                  )}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="side-foot">
          <div className="row">Documentation</div>
          <div className="row">
            Credits <span className="val">$11.28</span>
          </div>
          <div className="row">
            <span className="avatar">&nbsp;</span>
            <span className="who">
              Signed in
              <span>Admin · Individual Org</span>
            </span>
          </div>
        </div>
      </aside>

      <main className="main">{children}</main>
    </div>
  )
}
