import { useEffect, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'

const SEVERITY_STYLE = {
  info: 'border-ink-950/10',
  warning: 'border-amber-500/40',
  critical: 'border-rust-500/40',
}
const SEVERITY_DOT = { info: 'bg-ink-600', warning: 'bg-amber-500', critical: 'bg-rust-500' }

export default function Insights() {
  const [insights, setInsights] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  function load() {
    api.get('/insights').then(setInsights)
  }
  useEffect(load, [])

  async function refresh() {
    setRefreshing(true)
    try {
      await api.post('/insights/generate')
      load()
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="AI Insights"
        subtitle="Every insight is generated from a real threshold crossed in your data — never invented."
        action={<button onClick={refresh} className="bg-ledger-600 text-white text-sm px-4 py-2 hover:bg-ledger-700">{refreshing ? 'Analyzing…' : 'Refresh insights'}</button>}
      />
      <div className="p-8 space-y-4">
        {!insights ? (
          <div className="text-sm text-ink-600">Loading…</div>
        ) : insights.length === 0 ? (
          <EmptyState title="No insights yet" description="Click Refresh insights to analyze your current financial data." />
        ) : (
          insights.map((ins) => (
            <div key={ins.id} className={`border bg-white p-5 ${SEVERITY_STYLE[ins.severity]}`}>
              <div className="flex items-center gap-2 mb-2">
                <span className={`w-1.5 h-1.5 rounded-full ${SEVERITY_DOT[ins.severity]}`} />
                <span className="text-xs text-ink-600 capitalize">{ins.category.replace(/_/g, ' ')}</span>
              </div>
              <div className="text-sm text-ink-950 mb-2">{ins.explanation}</div>
              {ins.recommended_action && <div className="text-xs text-ink-600 mb-2">Recommended: {ins.recommended_action}</div>}
              {Object.keys(ins.supporting_data || {}).length > 0 && (
                <pre className="text-[11px] text-ink-600 bg-ink-950/[0.03] p-2 mt-2 overflow-x-auto">{JSON.stringify(ins.supporting_data, null, 2)}</pre>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
