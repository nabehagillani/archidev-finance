import { useEffect, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'

export default function Budgets() {
  const [budgets, setBudgets] = useState(null)
  useEffect(() => { api.get('/budgets').then(setBudgets) }, [])

  return (
    <div>
      <PageHeader title="Budgets" subtitle="Current month spend against budget, by category." />
      <div className="p-8">
        {!budgets ? (
          <div className="text-sm text-ink-600">Loading…</div>
        ) : budgets.length === 0 ? (
          <EmptyState title="No budgets set" description="Set a monthly budget per expense category to track spend against it here." />
        ) : (
          <div className="space-y-4">
            {budgets.map((b) => {
              const over = b.percent_used >= 100
              const warn = b.percent_used >= 85 && !over
              return (
                <div key={b.category} className="border border-ink-950/10 bg-white p-5">
                  <div className="flex justify-between items-baseline mb-2">
                    <div className="text-sm text-ink-950">{b.category}</div>
                    <div className="text-xs text-ink-600 tabular">${b.actual.toLocaleString()} / ${b.budget.toLocaleString()}</div>
                  </div>
                  <div className="h-2 bg-ink-950/5">
                    <div
                      className={`h-2 ${over ? 'bg-rust-500' : warn ? 'bg-amber-500' : 'bg-ledger-500'}`}
                      style={{ width: `${Math.min(100, b.percent_used)}%` }}
                    />
                  </div>
                  <div className="text-[11px] text-ink-600 mt-1">{b.percent_used}% used · ${b.remaining.toLocaleString()} remaining</div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
