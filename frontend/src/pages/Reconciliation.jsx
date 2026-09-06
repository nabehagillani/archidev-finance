import { useRef, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import KpiCard from '../components/KpiCard'
import EmptyState from '../components/EmptyState'

export default function Reconciliation() {
  const [result, setResult] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const fileRef = useRef()

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const res = await api.upload('/reconciliation/upload', file)
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
      fileRef.current.value = ''
    }
  }

  return (
    <div>
      <PageHeader
        title="Bank Reconciliation"
        subtitle="Upload a bank statement (CSV/Excel) to automatically match it against your recorded transactions."
        action={
          <label className="bg-ledger-600 text-white text-sm px-4 py-2 cursor-pointer hover:bg-ledger-700">
            {uploading ? 'Reconciling…' : 'Upload statement'}
            <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={handleUpload} />
          </label>
        }
      />
      <div className="p-8">
        {error && <div className="mb-4 text-sm px-4 py-3 bg-rust-500/5 text-rust-600">{error}</div>}
        {!result ? (
          <EmptyState title="No reconciliation run yet" description="Upload a bank statement to see matched, unmatched, and duplicate transactions." />
        ) : (
          <div>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <KpiCard label="Match rate" value={`${result.match_rate_pct}%`} tone="positive" />
              <KpiCard label="Matched" value={result.matched} />
              <KpiCard label="Unmatched" value={result.unmatched} tone={result.unmatched > 0 ? 'negative' : 'neutral'} />
              <KpiCard label="Duplicates" value={result.duplicates} />
            </div>
            <div className="text-sm text-ink-600">{result.total_lines} total lines processed from the uploaded statement.</div>
          </div>
        )}
      </div>
    </div>
  )
}
