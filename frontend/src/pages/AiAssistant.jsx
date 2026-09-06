import { useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'

const SUGGESTIONS = [
  'What were our biggest expenses last month?',
  'Which customers have overdue payments?',
  'What is our average monthly expense?',
  'Why did profit decrease?',
  'Predict next month\'s cash flow.',
]

export default function AiAssistant() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)

  async function ask(q) {
    const query = q || question
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await api.post(`/ai-assistant/ask?question=${encodeURIComponent(query)}`)
      setHistory((h) => [...h, { question: query, ...res }])
      setQuestion('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader title="AI Finance Assistant" subtitle="Answers are computed from your real data — never invented." />
      <div className="p-8 max-w-3xl">
        <div className="flex flex-wrap gap-2 mb-6">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => ask(s)} className="text-xs border border-ink-950/15 px-3 py-1.5 hover:bg-ink-950/5">{s}</button>
          ))}
        </div>

        <div className="space-y-5 mb-6">
          {history.map((h, i) => (
            <div key={i} className="border border-ink-950/10 bg-white p-5">
              <div className="text-xs text-ink-600 mb-2">{h.question}</div>
              <div className="text-sm text-ink-950 mb-3">{h.answer}</div>
              {Array.isArray(h.supporting_numbers) && h.supporting_numbers.length > 0 && (
                <table className="w-full text-xs">
                  <tbody>
                    {h.supporting_numbers.map((row, j) => (
                      <tr key={j} className="border-t border-ink-950/5">
                        {Object.entries(row).map(([k, v]) => (
                          <td key={k} className="py-1 pr-4 text-ink-600">{typeof v === 'number' ? `$${v.toLocaleString()}` : String(v)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {h.recommendations?.length > 0 && (
                <div className="text-[11px] text-ledger-700 mt-3">{h.recommendations.join(' ')}</div>
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            value={question} onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && ask()}
            placeholder="Ask about your finances…"
            className="flex-1 border border-ink-950/15 px-3 py-2 text-sm focus:outline-none focus:border-ledger-500"
          />
          <button onClick={() => ask()} disabled={loading} className="bg-ledger-600 text-white text-sm px-5 py-2 hover:bg-ledger-700 disabled:opacity-50">
            {loading ? '…' : 'Ask'}
          </button>
        </div>
      </div>
    </div>
  )
}
