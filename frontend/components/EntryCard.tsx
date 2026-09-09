import Link from "next/link"

interface EntryCardProps {
  href: string
  title: string
  description: string
  accent: string
}

export default function EntryCard({ href, title, description, accent }: EntryCardProps) {
  return (
    <Link
      href={href}
      prefetch={false}
      className="group flex flex-col justify-between rounded border border-line bg-paper-raised p-6 transition-colors hover:border-forest"
      style={{ borderLeftWidth: 4, borderLeftColor: accent }}
    >
      <div>
        <h2 className="font-display text-lg font-bold text-ink">{title}</h2>
        <p className="mt-2 text-sm text-ink-muted">{description}</p>
      </div>
      <span className="mt-6 inline-block w-fit rounded border border-forest px-3 py-1.5 text-sm font-medium text-forest-deep transition-colors group-hover:bg-forest group-hover:text-paper-raised">
        열기
      </span>
    </Link>
  )
}
