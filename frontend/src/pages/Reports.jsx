import { useState } from 'react'
import { api, API_BASE } from '../services/api'
import PageHeader from '../components/PageHeader'

function firstOfMonth() {
  const d = new Date(); d.setDate(1)
  return d.toISOString().slice(0, 10)
}

export default function Reports() {
  const [start, setStart] = useState(firstOfMonth())
  const [end, setEnd] = useState(new Date().toISOString().slice(0, 10))
  const [pl, setPl] = useState(null)
  const [bs, setBs] = useState(null)

  async function runReports() {
    const p = await api.get('/reports/profit-loss', { start: `${start}T00:00:00`, end: `${end}T23:59:59` })
    setPl(p)
    const b = await api.get('/reports/balance-sheet')
    setBs(b)
  }

  function exportCsv() {
    const token = api.getToken()
    const url = `${API_BASE}/reports/export?report=profit-loss&start=${start}T00:00:00&end=${end}T23:59:59&fmt=csv`
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob); a.download = 'profit-loss.csv'; a.click()
      })
  }

  return (
    <div>
      <PageHeader title="Reports" subtitle="Profit & Loss and Balance Sheet, derived directly from the ledger." />
      <div className="p-8">
        <div className="flex items-end gap-3 mb-6">
          <div>
            <label className="block text-xs text-ink-600 mb-1">Start</label>
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="border border-ink-950/15 px-3 py-1.5 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-ink-600 mb-1">End</label>
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="border border-ink-950/15 px-3 py-1.5 text-sm" />
          </div>
          <button onClick={runReports} className="bg-ledger-600 text-white text-sm px-4 py-1.5 hover:bg-ledger-700">Run</button>
          {pl && <button onClick={exportCsv} className="border border-ink-950/15 text-sm px-4 py-1.5 hover:bg-ink-950/5">Export CSV</button>}
        </div>

        {pl && (
          <div className="border border-ink-950/10 bg-white p-5 mb-6">
            <div className="font-serif text-lg mb-4">Profit & Loss</div>
            <Row label="Revenue" value={pl.revenue} />
            <Row label="Operating Expenses" value={-pl.operating_expenses} />
            <div className="border-t border-ink-950/10 mt-2 pt-2">
              <Row label="Net Profit" value={pl.net_profit} bold />
            </div>
            <div className="mt-4 text-xs text-ink-600">By category</div>
            {Object.entries(pl.operating_expenses_by_category).map(([k, v]) => (
              <div key={k} className="flex justify-between text-xs text-ink-600 py-0.5">
                <span>{k}</span><span className="tabular">${v.toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}

        {bs && (
          <div className="border border-ink-950/10 bg-white p-5">
            <div className="font-serif text-lg mb-1">Balance Sheet</div>
            <div className="text-xs text-ink-600 mb-4">As of {new Date(bs.as_of).toLocaleDateString()}</div>
            <Row label="Assets" value={bs.assets} />
            <Row label="Liabilities" value={bs.liabilities} />
            <Row label="Equity" value={bs.equity} />
            <Row label="Retained Earnings (YTD)" value={bs.retained_earnings_ytd} />
            <div className="border-t border-ink-950/10 mt-2 pt-2 text-[11px] text-ink-600">
              Balance check: {bs.balances === 0 ? 'Books are balanced ✓' : `Off by $${bs.balances.toLocaleString()}`}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Row({ label, value, bold }) {
  return (
    <div className={`flex justify-between py-1 text-sm ${bold ? 'font-medium text-ink-950' : 'text-ink-700'}`}>
      <span>{label}</span>
      <span className="tabular">${Number(value).toLocaleString()}</span>
    </div>
  )
}
