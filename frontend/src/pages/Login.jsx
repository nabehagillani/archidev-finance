import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@archidev.com')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
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
          <div className="text-xs text-ink-600 mt-1">Finance Operations Platform</div>
        </div>
        <form onSubmit={handleSubmit} className="bg-paper p-7">
          <h1 className="font-serif text-lg text-ink-950 mb-5">Sign in</h1>
          {error && <div className="text-xs text-rust-600 mb-4 bg-rust-500/5 px-3 py-2">{error}</div>}
          <label className="block text-xs text-ink-600 mb-1">Email</label>
          <input
            value={email} onChange={(e) => setEmail(e.target.value)} type="email" required
            className="w-full border border-ink-950/15 px-3 py-2 text-sm mb-4 bg-white focus:outline-none focus:border-ledger-500"
          />
          <label className="block text-xs text-ink-600 mb-1">Password</label>
          <input
            value={password} onChange={(e) => setPassword(e.target.value)} type="password" required
            className="w-full border border-ink-950/15 px-3 py-2 text-sm mb-5 bg-white focus:outline-none focus:border-ledger-500"
          />
          <button
            type="submit" disabled={loading}
            className="w-full bg-ledger-600 text-white py-2 text-sm hover:bg-ledger-700 disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
          <div className="text-xs text-ink-600 mt-4 text-center">
            New here? <Link to="/signup" className="text-ledger-600 underline">Create a company</Link>
          </div>
          <div className="text-[11px] text-ink-600 mt-4 border-t border-ink-950/10 pt-3">
            Demo: admin@archidev.com / demo1234 (run the seed script first)
          </div>
        </form>
      </div>
    </div>
  )
}
