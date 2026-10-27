import Button from '../components/Button'
import Eyebrow from '../components/Eyebrow'
import Reveal from '../components/Reveal'
import { tiers } from '../lib/data'

const Check = () => <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 text-lime"><path d="M3 8.5l3 3 7-7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>
const Cross = () => <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 text-ink-2/50"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>

export default function Pricing() {
  return (
    <section id="pricing" className="section border-t border-line">
      <div className="container-x">
        <Reveal className="mb-14 text-center">
          <Eyebrow>Pricing</Eyebrow>
          <h2 className="mt-4 text-h1">Pay once. <span className="serif-i font-normal">Ship forever.</span></h2>
        </Reveal>
        <Reveal stagger="[data-card]" className="grid gap-6 md:grid-cols-3">
          {tiers.map((t) => (
            <article key={t.name} data-card className={`card flex flex-col p-7 ${t.highlight ? 'border-lime/60 shadow-glow' : ''}`}>
              <Eyebrow className={t.highlight ? '' : '!text-ink-2'}>{t.eyebrow}</Eyebrow>
              <h3 className="mt-5 text-h3 font-medium">{t.name}</h3>
              <p className="mt-2 text-[15px] text-ink-2">{t.blurb}</p>
              <p className="mt-6 text-[44px] font-medium leading-none tracking-tight">{t.price}</p>
              <ul className="mt-8 space-y-3 text-[15px]">
                {t.features.map((f) => (
                  <li key={f.label} className={`flex items-center gap-3 ${f.included ? '' : 'text-ink-2/60'}`}>
                    {f.included ? <Check /> : <Cross />}<span>{f.label}</span>
                  </li>
                ))}
              </ul>
              <Button href="#" variant={t.highlight ? 'primary' : 'ghost'} className="mt-10 w-full">{t.cta}</Button>
            </article>
          ))}
        </Reveal>
        <p className="mt-10 text-center font-mono text-mono text-ink-2">All prices one-shot, no subscription</p>
      </div>
    </section>
  )
}
