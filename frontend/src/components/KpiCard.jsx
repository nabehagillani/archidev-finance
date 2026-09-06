export default function KpiCard({ label, value, tone = 'neutral', hint }) {
  const toneClass = {
    neutral: 'text-ink-950',
    positive: 'text-ledger-600',
    negative: 'text-rust-600',
  }[tone]

  return (
    <div className="border border-ink-950/10 bg-white px-5 py-4">
      <div className="text-xs text-ink-600">{label}</div>
      <div className={`font-serif text-2xl mt-1 tabular ${toneClass}`}>{value}</div>
      {hint && <div className="text-[11px] text-ink-600 mt-1">{hint}</div>}
    </div>
  )
}
