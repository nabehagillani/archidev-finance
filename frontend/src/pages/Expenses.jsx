import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'
import StatusPill from '../components/StatusPill'

export default function Expenses() {
  const { can } = useAuth()
  const [expenses, setExpenses] = useState(null)
  const [busyId, setBusyId] = useState(null)

  function load() {
    api.get('/expenses').then(setExpenses)
  }
  useEffect(load, [])

  async function act(id, action) {
    setBusyId(id)
    try {
      await api.post(`/expenses/${id}/${action}`)
      load()
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <PageHeader title="Expenses" subtitle="Submit → review → approve/reject. An approved expense automatically becomes a transaction." />
      <div className="p-8">
        {!expenses ? (
          <div className="text-sm text-ink-600">Loading…</div>
        ) : expenses.length === 0 ? (
          <EmptyState title="No expenses submitted" description="Employee-submitted expenses awaiting approval will appear here." />
        ) : (
          <table className="w-full text-sm bg-white border border-ink-950/10">
            <thead>
              <tr className="border-b border-ink-950/10 text-left text-xs text-ink-600">
                <th className="px-4 py-2 font-normal">Date</th>
                <th className="px-4 py-2 font-normal">Description</th>
                <th className="px-4 py-2 font-normal text-right">Amount</th>
                <th className="px-4 py-2 font-normal">Status</th>
                {can('approve_expense') && <th className="px-4 py-2 font-normal">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {expenses.map((e) => (
                <tr key={e.id} className="border-b border-ink-950/5">
                  <td className="px-4 py-2">{new Date(e.date).toLocaleDateString()}</td>
                  <td className="px-4 py-2">{e.description || '—'}</td>
                  <td className="px-4 py-2 text-right tabular">${Number(e.amount).toLocaleString()}</td>
                  <td className="px-4 py-2"><StatusPill status={e.status} /></td>
                  {can('approve_expense') && (
                    <td className="px-4 py-2">
                      {e.status === 'submitted' && (
                        <div className="flex gap-3">
                          <button disabled={busyId === e.id} onClick={() => act(e.id, 'approve')} className="text-ledger-600 text-xs hover:underline">Approve</button>
                          <button disabled={busyId === e.id} onClick={() => act(e.id, 'reject')} className="text-rust-600 text-xs hover:underline">Reject</button>
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
