import { useEffect, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import KpiCard from '../components/KpiCard'

export default function Receivables() {
  const [data, setData] = useState(null)
  useEffect(() => { api.get('/receivables/aging').then(setData) }, [])
  if (!data) return <div className="p-8 text-sm text-ink-600">Loading…</div>

  return (
    <div>
      <PageHeader title="Accounts Receivable" subtitle="Aging buckets computed live from open invoices." />
      <div className="p-8">
        <div className="grid grid-cols-4 gap-4 mb-8">
          <KpiCard label="0–30 days" value={`$${data.buckets['0-30'].toLocaleString()}`} />
          <KpiCard label="31–60 days" value={`$${data.buckets['31-60'].toLocaleString()}`} tone={data.buckets['31-60'] > 0 ? 'negative' : 'neutral'} />
          <KpiCard label="61–90 days" value={`$${data.buckets['61-90'].toLocaleString()}`} tone={data.buckets['61-90'] > 0 ? 'negative' : 'neutral'} />
          <KpiCard label="90+ days" value={`$${data.buckets['90+'].toLocaleString()}`} tone={data.buckets['90+'] > 0 ? 'negative' : 'neutral'} />
        </div>
        {data.high_risk_overdue.length > 0 && (
          <div className="border border-rust-500/20 bg-rust-500/5 p-5">
            <div className="text-sm text-rust-600 mb-3">High-risk overdue (90+ days)</div>
            <ul className="text-sm space-y-1">
              {data.high_risk_overdue.map((r) => (
                <li key={r.invoice_number}>{r.invoice_number} — {r.days_overdue} days overdue — ${r.balance_due.toLocaleString()}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
