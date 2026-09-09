"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const NAV_ITEMS = [
  { href: "/", label: "홈" },
  { href: "/farm", label: "농가 대시보드" },
  { href: "/distributor", label: "유통업체 대시보드" },
  { href: "/idle-land", label: "유휴토지 지도" },
]

// Every <Link> in this app sets prefetch={false} -- output: "export" writes
// each route's RSC payload as a static .txt file, but not at the URL/query
// shape Next's client prefetcher requests, so the default hover/viewport
// prefetch just 404s in the console with no functional benefit (every page
// here fetches its own data client-side on mount regardless).

export default function Header() {
  const pathname = usePathname()

  return (
    <header className="border-b border-line bg-paper-raised">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" prefetch={false} className="flex items-baseline gap-2">
          <span className="font-display text-lg font-bold tracking-tight text-forest-deep">
            울퉁불퉁 농장 AI
          </span>
          <span className="hidden text-xs text-ink-muted sm:inline">FarmFlow AI</span>
        </Link>

        <nav aria-label="주요 화면" className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/" ? pathname === "/" : pathname?.startsWith(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                prefetch={false}
                aria-current={isActive ? "page" : undefined}
                className={`rounded px-3 py-1.5 text-sm transition-colors ${
                  isActive
                    ? "bg-forest text-paper-raised"
                    : "text-ink-muted hover:bg-forest-tint hover:text-forest-deep"
                }`}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
