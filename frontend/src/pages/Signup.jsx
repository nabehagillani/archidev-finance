import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ companyName: '', fullName: '', email: '', password: '' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await signup(form.companyName, form.fullName, form.email, form.password)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-ink-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="font-serif text-2xl text-paper">Archidev</div>
          <div className="text-xs text-ink-600 mt-1">Set up your company</div>
        </div>
        <form onSubmit={handleSubmit} className="bg-paper p-7">
          {error && <div className="text-xs text-rust-600 mb-4 bg-rust-500/5 px-3 py-2">{error}</div>}
          {[
            ['Company name', 'companyName', 'text'],
            ['Your full name', 'fullName', 'text'],
            ['Email', 'email', 'email'],
            ['Password', 'password', 'password'],
          ].map(([label, field, type]) => (
            <div key={field} className="mb-4">
              <label className="block text-xs text-ink-600 mb-1">{label}</label>
              <input
                value={form[field]} onChange={update(field)} type={type} required
                className="w-full border border-ink-950/15 px-3 py-2 text-sm bg-white focus:outline-none focus:border-ledger-500"
              />
            </div>
          ))}
          <button
            type="submit" disabled={loading}
            className="w-full bg-ledger-600 text-white py-2 text-sm hover:bg-ledger-700 disabled:opacity-50 mt-1"
          >
            {loading ? 'Creating…' : 'Create company & sign in'}
          </button>
          <div className="text-xs text-ink-600 mt-4 text-center">
            Already set up? <Link to="/login" className="text-ledger-600 underline">Sign in</Link>
          </div>
        </form>
      </div>
    </div>
  )
}
