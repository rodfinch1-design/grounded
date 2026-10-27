export default function Marquee({ text, repeat = 10 }: { text: string; repeat?: number }) {
  const items = Array.from({ length: repeat }, (_, i) => (
    <span key={i} className="font-mono text-mono uppercase tracking-eyebrow text-ink-2 px-6">{text}</span>
  ))
  return (
    <div className="marquee overflow-hidden border-y border-line py-5" aria-label={text}>
      <div className="marquee-track" aria-hidden="true">{items}{items}</div>
    </div>
  )
}
