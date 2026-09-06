const TONE = {
  paid: 'bg-ledger-50 text-ledger-700',
  cleared: 'bg-ledger-50 text-ledger-700',
  approved: 'bg-ledger-50 text-ledger-700',
  matched: 'bg-ledger-50 text-ledger-700',
  sent: 'bg-amber-500/10 text-amber-500',
  pending: 'bg-amber-500/10 text-amber-500',
  submitted: 'bg-amber-500/10 text-amber-500',
  partially_paid: 'bg-amber-500/10 text-amber-500',
  unmatched: 'bg-amber-500/10 text-amber-500',
  overdue: 'bg-rust-500/10 text-rust-600',
  rejected: 'bg-rust-500/10 text-rust-600',
  void: 'bg-rust-500/10 text-rust-600',
  cancelled: 'bg-ink-950/5 text-ink-600',
  draft: 'bg-ink-950/5 text-ink-600',
}

export default function StatusPill({ status }) {
  const cls = TONE[status] || 'bg-ink-950/5 text-ink-600'
  return <span className={`px-2 py-0.5 rounded text-xs capitalize ${cls}`}>{status?.replace('_', ' ')}</span>
}
