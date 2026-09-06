export default function EmptyState({ title, description }) {
  return (
    <div className="border border-dashed border-ink-950/15 py-16 text-center">
      <div className="font-serif text-lg text-ink-950">{title}</div>
      {description && <div className="text-sm text-ink-600 mt-1 max-w-sm mx-auto">{description}</div>}
    </div>
  )
}
