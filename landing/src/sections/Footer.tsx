import { footerColumns } from '../lib/data'

export default function Footer() {
  return (
    <footer className="border-t border-line py-16">
      <div className="container-x grid gap-12 md:grid-cols-12">
        <div className="md:col-span-3">
          <span className="serif-i text-5xl text-lime">H</span>
          <p className="mt-4 max-w-[220px] text-[14px] text-ink-2">Templates that read like a person designed them.</p>
        </div>
        {footerColumns.map((c) => (
          <nav key={c.title} aria-label={c.title} className="md:col-span-3">
            <h3 className="eyebrow !text-ink-2">{c.title}</h3>
            <ul className="mt-5 space-y-3 text-[14px]">
              {c.links.map((l) => <li key={l}><a href="#" className="text-ink-2 transition-colors hover:text-ink">{l}</a></li>)}
            </ul>
          </nav>
        ))}
      </div>
      <div className="container-x mt-16 flex flex-wrap items-center justify-between gap-4 font-mono text-[12px] text-ink-2">
        <span>© 2026 Hyliox</span>
        <a href="#top" aria-label="Back to top" className="transition-colors hover:text-ink">↑ Top</a>
      </div>
    </footer>
  )
}
