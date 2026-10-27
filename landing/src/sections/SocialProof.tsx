import Eyebrow from '../components/Eyebrow'
import Reveal from '../components/Reveal'
import { logos, testimonials } from '../lib/data'

export default function SocialProof() {
  return (
    <section className="section border-t border-line">
      <div className="container-x">
        <Reveal className="text-center">
          <Eyebrow>Used by</Eyebrow>
          <ul className="mt-8 flex flex-wrap items-center justify-center gap-x-12 gap-y-4">
            {logos.map((l) => <li key={l} className="serif-i text-2xl text-ink-2">{l}</li>)}
          </ul>
        </Reveal>
        <Reveal stagger="[data-card]" className="mt-20 columns-1 gap-6 md:columns-2 lg:columns-3">
          {testimonials.map((t) => (
            <figure key={t.name} data-card className="card mb-6 break-inside-avoid p-6">
              <blockquote className="text-[17px] leading-relaxed">“{t.quote}”</blockquote>
              <figcaption className="mt-5 flex items-center gap-3">
                <span aria-hidden="true" className="grid h-8 w-8 place-items-center rounded-full bg-lime/15 font-mono text-[11px] text-lime">{t.name[0]}</span>
                <span className="text-[14px]"><span className="text-ink">{t.name}</span><span className="text-ink-2"> · {t.role}</span></span>
              </figcaption>
            </figure>
          ))}
        </Reveal>
      </div>
    </section>
  )
}
