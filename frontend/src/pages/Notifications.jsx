import { useEffect, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'

const DOT = { info: 'bg-ink-600', warning: 'bg-amber-500', critical: 'bg-rust-500' }

export default function Notifications() {
  const [items, setItems] = useState(null)

  function load() {
    api.get('/notifications').then(setItems)
  }
  useEffect(load, [])

  async function markRead(id) {
    await api.post(`/notifications/${id}/read`)
    load()
  }

  return (
    <div>
      <PageHeader title="Notifications" subtitle="Overdue invoices, budget thresholds, unusual expenses, and other alerts." />
      <div className="p-8">
        {!items ? (
          <div className="text-sm text-ink-600">Loading…</div>
        ) : items.length === 0 ? (
          <EmptyState title="You're all caught up" description="New alerts will appear here as they're triggered by your financial data." />
        ) : (
          <div className="divide-y divide-ink-950/5 bg-white border border-ink-950/10">
            {items.map((n) => (
              <div key={n.id} className={`flex items-start gap-3 px-5 py-3 ${n.is_read ? 'opacity-50' : ''}`}>
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 ${DOT[n.severity]}`} />
                <div className="flex-1">
                  <div className="text-sm text-ink-950">{n.message}</div>
                  <div className="text-[11px] text-ink-600 mt-0.5">{new Date(n.created_at).toLocaleString()}</div>
                </div>
                {!n.is_read && (
                  <button onClick={() => markRead(n.id)} className="text-xs text-ledger-600 hover:underline shrink-0">Mark read</button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
