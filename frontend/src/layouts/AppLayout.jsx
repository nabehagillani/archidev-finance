import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV_SECTIONS = [
  {
    label: 'Overview',
    items: [{ to: '/', label: 'Dashboard' }],
  },
  {
    label: 'Money In & Out',
    items: [
      { to: '/transactions', label: 'Transactions' },
      { to: '/expenses', label: 'Expenses' },
      { to: '/invoices', label: 'Invoices' },
      { to: '/receivables', label: 'Receivables' },
      { to: '/payables', label: 'Payables' },
      { to: '/reconciliation', label: 'Bank Reconciliation' },
    ],
  },
  {
    label: 'Plan & Understand',
    items: [
      { to: '/budgets', label: 'Budgets' },
      { to: '/reports', label: 'Reports' },
      { to: '/forecasting', label: 'Forecasting' },
      { to: '/insights', label: 'AI Insights' },
      { to: '/assistant', label: 'AI Assistant' },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/notifications', label: 'Notifications' },
      { to: '/audit-logs', label: 'Audit Logs' },
      { to: '/settings', label: 'Settings' },
    ],
  },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen bg-paper text-ink-900">
      <aside className="w-64 shrink-0 bg-ink-950 text-paper flex flex-col">
        <div className="px-6 py-6 border-b border-ink-800">
          <div className="font-serif text-xl tracking-tight">Archidev</div>
          <div className="text-xs text-ink-600 mt-0.5">Finance Operations</div>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="mb-5">
              <div className="px-6 text-[11px] text-ink-600 mb-1.5">{section.label}</div>
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `block mx-3 px-3 py-1.5 rounded text-sm ${
                      isActive ? 'bg-ledger-700 text-white' : 'text-ink-200 hover:bg-ink-800'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="px-6 py-4 border-t border-ink-800 text-sm">
          <div className="text-paper">{user?.fullName}</div>
          <div className="text-ink-600 text-xs capitalize mb-2">{user?.role?.replace('_', ' ')}</div>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="text-xs text-ink-600 hover:text-paper underline"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
