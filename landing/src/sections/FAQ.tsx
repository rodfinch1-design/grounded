import Accordion from '../components/Accordion'
import Eyebrow from '../components/Eyebrow'
import Reveal from '../components/Reveal'
import { faqs } from '../lib/data'

export default function FAQ() {
  return (
    <section id="faq" className="section border-t border-line">
      <div className="container-x grid gap-12 lg:grid-cols-12">
        <Reveal className="lg:col-span-4">
          <Eyebrow>FAQ</Eyebrow>
          <h2 className="mt-4 text-h1">Questions, <span className="serif-i font-normal">answered.</span></h2>
        </Reveal>
        <Reveal className="lg:col-span-8"><Accordion items={faqs} /></Reveal>
      </div>
    </section>
  )
}
