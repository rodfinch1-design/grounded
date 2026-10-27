import Button from './Button'

const links = [['Templates', '#templates'], ['Method', '#method'], ['Pricing', '#pricing'], ['FAQ', '#faq']]

export default function Nav() {
  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="container-x flex h-16 items-center justify-between">
        <a href="#top" className="flex items-center gap-2" aria-label="Hyliox home">
          <span className="serif-i text-2xl leading-none text-lime">H</span>
          <span className="font-mono text-mono uppercase tracking-[0.3em]">Hyliox</span>
        </a>
        <nav aria-label="Primary" className="hidden items-center gap-8 md:flex">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="text-[14px] text-ink-2 transition-colors hover:text-ink">{label}</a>
          ))}
        </nav>
        <Button href="#templates" className="!px-4 !py-2 text-[13px]">Browse →</Button>
      </div>
    </header>
  )
}
