import { useEffect, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'
import KpiCard from '../components/KpiCard'
import EmptyState from '../components/EmptyState'
import StatusPill from '../components/StatusPill'

export default function Payables() {
  const [data, setData] = useState(null)
  const [vendors, setVendors] = useState([])
  const [categories, setCategories] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [payingId, setPayingId] = useState(null)
  const [payAmount, setPayAmount] = useState('')
  const [form, setForm] = useState({ vendor_id: '', category_id: '', total: '', bill_date: '', due_date: '', priority: 'normal' })
  const [error, setError] = useState(null)

  function load() {
    api.get('/payables').then(setData)
  }
  useEffect(() => {
    load()
    api.get('/settings/vendors').catch(() => []).then((v) => setVendors(v || []))
    api.get('/settings/expense-categories').catch(() => []).then((c) => setCategories(c || []))
  }, [])

  async function submitBill(e) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/payables', {
        ...form, total: parseFloat(form.total),
        bill_date: `${form.bill_date}T00:00:00`, due_date: `${form.due_date}T00:00:00`,
      })
      setShowForm(false)
      setForm({ vendor_id: '', category_id: '', total: '', bill_date: '', due_date: '', priority: 'normal' })
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function submitPayment(billId) {
    await api.post(`/payables/${billId}/payments?amount=${parseFloat(payAmount)}`)
    setPayingId(null)
    setPayAmount('')
    load()
  }

  if (!data) return <div className="p-8 text-sm text-ink-600">Loading…</div>

  return (
    <div>
      <PageHeader
        title="Accounts Payable"
        subtitle="What you owe vendors. Recording a bill posts the AP journal entry immediately."
        action={<button onClick={() => setShowForm((s) => !s)} className="bg-ledger-600 text-white text-sm px-4 py-2 hover:bg-ledger-700">{showForm ? 'Cancel' : 'Record a bill'}</button>}
      />
      <div className="p-8">
        {showForm && (
          <form onSubmit={submitBill} className="border border-ink-950/10 bg-white p-5 mb-6 grid grid-cols-2 gap-4">
            {error && <div className="col-span-2 text-xs text-rust-600 bg-rust-500/5 px-3 py-2">{error}</div>}
            <div>
              <label className="block text-xs text-ink-600 mb-1">Vendor</label>
              <select required value={form.vendor_id} onChange={(e) => setForm({ ...form, vendor_id: e.target.value })} className="w-full border border-ink-950/15 px-3 py-2 text-sm">
                <option value="">Select…</option>
                {vendors.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-ink-600 mb-1">Expense category</label>
              <select required value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="w-full border border-ink-950/15 px-3 py-2 text-sm">
                <option value="">Select…</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-ink-600 mb-1">Bill date</label>
              <input required type="date" value={form.bill_date} onChange={(e) => setForm({ ...form, bill_date: e.target.value })} className="w-full border border-ink-950/15 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-ink-600 mb-1">Due date</label>
              <input required type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="w-full border border-ink-950/15 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-ink-600 mb-1">Amount</label>
              <input required type="number" step="0.01" value={form.total} onChange={(e) => setForm({ ...form, total: e.target.value })} className="w-full border border-ink-950/15 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-ink-600 mb-1">Priority</label>
              <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} className="w-full border border-ink-950/15 px-3 py-2 text-sm">
                <option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option>
              </select>
            </div>
            <div className="col-span-2">
              <button type="submit" className="bg-ledger-600 text-white text-sm px-4 py-2 hover:bg-ledger-700">Save bill</button>
            </div>
          </form>
        )}

        <div className="grid grid-cols-4 gap-4 mb-8">
          <KpiCard label="Total Payable" value={`$${data.total_payable.toLocaleString()}`} />
          <KpiCard label="Paid" value={`$${data.paid.toLocaleString()}`} tone="positive" />
          <KpiCard label="Pending" value={`$${data.pending.toLocaleString()}`} />
          <KpiCard label="Overdue" value={`$${data.overdue.toLocaleString()}`} tone={data.overdue > 0 ? 'negative' : 'neutral'} />
        </div>

        {data.bills.length === 0 ? (
          <EmptyState title="No vendor bills yet" description="Record a bill above to track what you owe." />
        ) : (
          <table className="w-full text-sm bg-white border border-ink-950/10">
            <thead>
              <tr className="border-b border-ink-950/10 text-left text-xs text-ink-600">
                <th className="px-4 py-2 font-normal">Bill #</th>
                <th className="px-4 py-2 font-normal">Due</th>
                <th className="px-4 py-2 font-normal text-right">Balance Due</th>
                <th className="px-4 py-2 font-normal">Priority</th>
                <th className="px-4 py-2 font-normal">Status</th>
                <th className="px-4 py-2 font-normal">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.bills.map((b) => (
                <tr key={b.id} className="border-b border-ink-950/5">
                  <td className="px-4 py-2">{b.bill_number}</td>
                  <td className="px-4 py-2">{new Date(b.due_date).toLocaleDateString()}</td>
                  <td className="px-4 py-2 text-right tabular">${b.balance_due.toLocaleString()}</td>
                  <td className="px-4 py-2 capitalize">{b.priority}</td>
                  <td className="px-4 py-2"><StatusPill status={b.status} /></td>
                  <td className="px-4 py-2">
                    {b.status !== 'paid' && (
                      payingId === b.id ? (
                        <div className="flex gap-2 items-center">
                          <input type="number" step="0.01" autoFocus value={payAmount} onChange={(e) => setPayAmount(e.target.value)} className="w-24 border border-ink-950/15 px-2 py-1 text-xs" />
                          <button onClick={() => submitPayment(b.id)} className="text-ledger-600 text-xs hover:underline">Confirm</button>
                          <button onClick={() => setPayingId(null)} className="text-ink-600 text-xs hover:underline">Cancel</button>
                        </div>
                      ) : (
                        <button onClick={() => { setPayingId(b.id); setPayAmount(String(b.balance_due)) }} className="text-ledger-600 text-xs hover:underline">Record payment</button>
                      )
                    )}
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
