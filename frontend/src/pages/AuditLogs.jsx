import { useEffect, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'

export default function AuditLogs() {
  const [logs, setLogs] = useState(null)
  useEffect(() => { api.get('/audit-logs').then(setLogs) }, [])

  return (
    <div>
      <PageHeader title="Audit Logs" subtitle="Every approval, edit, and import — who did what, and when." />
      <div className="p-8">
        {!logs ? (
          <div className="text-sm text-ink-600">Loading…</div>
        ) : logs.length === 0 ? (
          <EmptyState title="No activity logged yet" description="Actions like approving an expense or importing transactions will be recorded here." />
        ) : (
          <table className="w-full text-sm bg-white border border-ink-950/10">
            <thead>
              <tr className="border-b border-ink-950/10 text-left text-xs text-ink-600">
                <th className="px-4 py-2 font-normal">Timestamp</th>
                <th className="px-4 py-2 font-normal">Action</th>
                <th className="px-4 py-2 font-normal">Module</th>
                <th className="px-4 py-2 font-normal">Record</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-b border-ink-950/5">
                  <td className="px-4 py-2 text-xs">{new Date(l.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2">{l.action.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-2 capitalize">{l.module}</td>
                  <td className="px-4 py-2 text-xs text-ink-600">{l.record_id?.slice(0, 8) || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
