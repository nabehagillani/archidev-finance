import { useEffect, useState } from 'react'
import { api, API_BASE } from '../services/api'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'
import StatusPill from '../components/StatusPill'

export default function Invoices() {
  const [invoices, setInvoices] = useState(null)

  function load() {
    api.get('/invoices').then(setInvoices)
  }
  useEffect(load, [])

  async function send(id) {
    await api.post(`/invoices/${id}/send`)
    load()
  }

  function downloadPdf(id, number) {
    const token = api.getToken()
    fetch(`${API_BASE}/invoices/${id}/pdf`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url; a.download = `${number}.pdf`; a.click()
        URL.revokeObjectURL(url)
      })
  }

  return (
    <div>
      <PageHeader title="Invoices" subtitle="Sending an invoice posts the AR journal entry; a draft has no accounting impact yet." />
      <div className="p-8">
        {!invoices ? (
          <div className="text-sm text-ink-600">Loading…</div>
        ) : invoices.length === 0 ? (
          <EmptyState title="No invoices yet" description="Invoices you create will appear here, with status tracking from Draft through Paid." />
        ) : (
          <table className="w-full text-sm bg-white border border-ink-950/10">
            <thead>
              <tr className="border-b border-ink-950/10 text-left text-xs text-ink-600">
                <th className="px-4 py-2 font-normal">Invoice #</th>
                <th className="px-4 py-2 font-normal">Due</th>
                <th className="px-4 py-2 font-normal text-right">Total</th>
                <th className="px-4 py-2 font-normal text-right">Balance Due</th>
                <th className="px-4 py-2 font-normal">Status</th>
                <th className="px-4 py-2 font-normal">Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-ink-950/5">
                  <td className="px-4 py-2">{inv.invoice_number}</td>
                  <td className="px-4 py-2">{new Date(inv.due_date).toLocaleDateString()}</td>
                  <td className="px-4 py-2 text-right tabular">${inv.total.toLocaleString()}</td>
                  <td className="px-4 py-2 text-right tabular">${inv.balance_due.toLocaleString()}</td>
                  <td className="px-4 py-2"><StatusPill status={inv.status} /></td>
                  <td className="px-4 py-2 space-x-3">
                    {inv.status === 'draft' && (
                      <button onClick={() => send(inv.id)} className="text-ledger-600 text-xs hover:underline">Send</button>
                    )}
                    <button onClick={() => downloadPdf(inv.id, inv.invoice_number)} className="text-ink-600 text-xs hover:underline">PDF</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
