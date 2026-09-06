import { useEffect, useState } from 'react'
import { api } from '../services/api'
import PageHeader from '../components/PageHeader'

export default function Settings() {
  const [company, setCompany] = useState(null)
  const [users, setUsers] = useState(null)
  const [accounts, setAccounts] = useState(null)

  useEffect(() => {
    api.get('/settings/company').then(setCompany)
    api.get('/settings/users').then(setUsers).catch(() => setUsers([]))
    api.get('/settings/chart-of-accounts').then(setAccounts)
  }, [])

  return (
    <div>
      <PageHeader title="Settings" subtitle="Company details, team members, and chart of accounts." />
      <div className="p-8 space-y-8">
        {company && (
          <div className="border border-ink-950/10 bg-white p-5">
            <div className="font-serif text-lg mb-3">Company</div>
            <div className="text-sm text-ink-950">{company.name}</div>
            <div className="text-xs text-ink-600 mt-1">Currency: {company.base_currency}</div>
          </div>
        )}

        {users && (
          <div className="border border-ink-950/10 bg-white p-5">
            <div className="font-serif text-lg mb-3">Team</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-ink-600 border-b border-ink-950/10">
                  <th className="py-2 font-normal">Name</th>
                  <th className="py-2 font-normal">Email</th>
                  <th className="py-2 font-normal">Role</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-ink-950/5">
                    <td className="py-2">{u.full_name}</td>
                    <td className="py-2 text-ink-600">{u.email}</td>
                    <td className="py-2 capitalize">{u.role.replace('_', ' ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {accounts && (
          <div className="border border-ink-950/10 bg-white p-5">
            <div className="font-serif text-lg mb-3">Chart of Accounts</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-ink-600 border-b border-ink-950/10">
                  <th className="py-2 font-normal">Code</th>
                  <th className="py-2 font-normal">Name</th>
                  <th className="py-2 font-normal">Type</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((a) => (
                  <tr key={a.id} className="border-b border-ink-950/5">
                    <td className="py-2 tabular">{a.code}</td>
                    <td className="py-2">{a.name}</td>
                    <td className="py-2 capitalize">{a.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
