import Button from '../components/Button'
import Eyebrow from '../components/Eyebrow'
import Marquee from '../components/Marquee'
import Reveal from '../components/Reveal'

export default function FinalCTA() {
  return (
    <section className="relative overflow-hidden border-t border-line">
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 bottom-0 h-[60%] bg-[radial-gradient(ellipse_at_bottom,rgba(212,255,79,0.18),transparent_65%)]" />
      <Reveal className="container-x section relative text-center">
        <Eyebrow>Last call</Eyebrow>
        <h2 className="mx-auto mt-6 max-w-4xl text-display leading-[1.02]">
          <span className="font-sans not-italic text-h1 block">Ready to ship?</span>
          <span className="serif-i font-normal">Or still scrolling references?</span>
        </h2>
        <div className="mt-10"><Button href="#templates">Browse templates →</Button></div>
      </Reveal>
      <Marquee text="Built with AI · Not by AI ·" />
    </section>
  )
}
