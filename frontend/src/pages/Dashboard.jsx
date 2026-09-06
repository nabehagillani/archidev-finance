import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import KpiCard from '../components/KpiCard'

const currency = (n) => `$${Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

export default function Dashboard() {
  const [kpis, setKpis] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/dashboard/kpis').then(setKpis).catch((e) => setError(e.message))
    api.get('/forecasting/profit', { months_forward: 2 }).catch(() => null).then(setForecast)
  }, [])

  if (error) return <div className="p-8 text-rust-600 text-sm">{error}</div>
  if (!kpis) return <div className="p-8 text-ink-600 text-sm">Loading dashboard…</div>

  const health = kpis.financial_health
  const trendData = forecast ? [...forecast.history, ...forecast.forecast] : []

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Live figures computed directly from your ledger." />
      <div className="p-8">
        <div className="grid grid-cols-4 gap-4 mb-8">
          <KpiCard label="Total Revenue" value={currency(kpis.total_revenue)} tone="positive" />
          <KpiCard label="Total Expenses" value={currency(kpis.total_expenses)} />
          <KpiCard label="Net Profit" value={currency(kpis.net_profit)} tone={kpis.net_profit >= 0 ? 'positive' : 'negative'} />
          <KpiCard label="Cash Balance" value={currency(kpis.cash_balance)} />
          <KpiCard label="Accounts Receivable" value={currency(kpis.accounts_receivable)} />
          <KpiCard label="Accounts Payable" value={currency(kpis.accounts_payable)} />
          <KpiCard label="Pending Invoices" value={kpis.pending_invoices} />
          <KpiCard label="Overdue Payments" value={currency(kpis.overdue_payments)} tone={kpis.overdue_payments > 0 ? 'negative' : 'neutral'} />
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 border border-ink-950/10 bg-white p-5">
            <div className="text-sm text-ink-950 mb-4">Profit trend (actual vs forecast)</div>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={trendData}>
                  <CartesianGrid stroke="#0B122010" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => currency(v)} />
                  <Line type="monotone" dataKey="value" stroke="#186142" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-sm text-ink-600 py-16 text-center">Not enough history yet to plot a trend.</div>
            )}
            <div className="text-[11px] text-ink-600 mt-2">Shaded points beyond today are linear-trend estimates, not actuals.</div>
          </div>

          <div className="border border-ink-950/10 bg-white p-5">
            <div className="text-sm text-ink-950 mb-1">Financial Health Score</div>
            <div className="font-serif text-4xl text-ledger-600 mb-4">{health.score}<span className="text-lg text-ink-600">/100</span></div>
            <div className="space-y-2">
              {Object.entries(health.factors).map(([key, val]) => (
                <div key={key}>
                  <div className="flex justify-between text-xs text-ink-600 mb-0.5">
                    <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="tabular">{val}</span>
                  </div>
                  <div className="h-1.5 bg-ink-950/5">
                    <div className="h-1.5 bg-ledger-500" style={{ width: `${val}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
