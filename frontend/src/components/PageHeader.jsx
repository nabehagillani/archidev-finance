export default function PageHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between px-8 pt-8 pb-6 border-b border-ink-950/10">
      <div>
        <h1 className="font-serif text-2xl text-ink-950">{title}</h1>
        {subtitle && <p className="text-sm text-ink-600 mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
