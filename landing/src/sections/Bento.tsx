import Eyebrow from '../components/Eyebrow'
import Reveal from '../components/Reveal'
import Thumb from '../components/Thumb'
import { templates } from '../lib/data'

export default function Bento() {
  return (
    <section id="templates" className="section">
      <div className="container-x">
        <Reveal className="mb-14 max-w-2xl">
          <Eyebrow>The set</Eyebrow>
          <h2 className="mt-4 text-h1">Eight templates. <span className="serif-i font-normal">One standard.</span></h2>
        </Reveal>
        <Reveal stagger="[data-card]" className="grid-12">
          {templates.map((t, i) => (
            <a key={t.id} href={`#${t.id}`} data-card
              className={`card group block p-3 ${t.span} ${t.featured ? 'border-lime/40 shadow-glow' : ''}`}>
              <Thumb hue={t.hue} label={t.title} eager={i < 2} />
              <div className="flex items-end justify-between px-2 pb-2 pt-4">
                <div>
                  <h3 className="text-h3 font-medium">{t.title}</h3>
                  <p className="mt-1 text-[14px] text-ink-2">{t.subtitle}</p>
                </div>
                <span className={`font-mono text-mono ${t.featured ? 'text-lime' : 'text-ink-2'}`}>{t.featured ? 'Featured' : `0${i + 1}`}</span>
              </div>
            </a>
          ))}
        </Reveal>
      </div>
    </section>
  )
}
