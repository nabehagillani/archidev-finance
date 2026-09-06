import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'
import StatusPill from '../components/StatusPill'

export default function Transactions() {
  const [data, setData] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [importResult, setImportResult] = useState(null)
  const fileRef = useRef()

  function load() {
    api.get('/transactions').then(setData)
  }

  useEffect(load, [])

  async function handleImport(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setImportResult(null)
    try {
      const res = await api.upload('/transactions/import', file)
      setImportResult(res)
      load()
    } catch (err) {
      setImportResult({ error: err.message })
    } finally {
      setUploading(false)
      fileRef.current.value = ''
    }
  }

  return (
    <div>
      <PageHeader
        title="Transactions"
        subtitle="Every posted transaction, with automatic double-entry postings behind each one."
        action={
          <label className="bg-ledger-600 text-white text-sm px-4 py-2 cursor-pointer hover:bg-ledger-700">
            {uploading ? 'Importing…' : 'Import CSV / Excel'}
            <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={handleImport} />
          </label>
        }
      />
      <div className="p-8">
        {importResult && (
          <div className={`mb-4 text-sm px-4 py-3 ${importResult.error ? 'bg-rust-500/5 text-rust-600' : 'bg-ledger-50 text-ledger-700'}`}>
            {importResult.error || `Imported ${importResult.created} of ${importResult.rows_processed} rows. ${importResult.errors?.length ? `${importResult.errors.length} rows had errors.` : ''}`}
          </div>
        )}
        {!data ? (
          <div className="text-sm text-ink-600">Loading…</div>
        ) : data.items.length === 0 ? (
          <EmptyState title="No transactions yet" description="Import a CSV or Excel export from your bank, or add transactions via the API, to get started." />
        ) : (
          <table className="w-full text-sm bg-white border border-ink-950/10">
            <thead>
              <tr className="border-b border-ink-950/10 text-left text-xs text-ink-600">
                <th className="px-4 py-2 font-normal">Date</th>
                <th className="px-4 py-2 font-normal">Description</th>
                <th className="px-4 py-2 font-normal">Type</th>
                <th className="px-4 py-2 font-normal text-right">Amount</th>
                <th className="px-4 py-2 font-normal">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((t) => (
                <tr key={t.id} className="border-b border-ink-950/5">
                  <td className="px-4 py-2">{new Date(t.date).toLocaleDateString()}</td>
                  <td className="px-4 py-2">{t.description}</td>
                  <td className="px-4 py-2 capitalize">{t.type}</td>
                  <td className={`px-4 py-2 text-right tabular ${t.type === 'income' ? 'text-ledger-600' : 'text-ink-950'}`}>
                    {t.type === 'income' ? '+' : '−'}${Number(t.amount).toLocaleString()}
                  </td>
                  <td className="px-4 py-2"><StatusPill status={t.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
