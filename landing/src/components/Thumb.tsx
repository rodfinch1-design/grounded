/** Procedural 16:10 thumbnail so the demo ships without image assets. Swap for <picture> with AVIF/WebP sources. */
export default function Thumb({ hue, label, eager = false }: { hue: number; label: string; eager?: boolean }) {
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 100'>
    <defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0' stop-color='hsl(${hue} 60% 14%)'/><stop offset='1' stop-color='hsl(${(hue + 40) % 360} 50% 6%)'/></linearGradient></defs>
    <rect width='160' height='100' fill='url(#g)'/>
    <rect x='18' y='18' width='70' height='6' rx='3' fill='white' fill-opacity='.7'/>
    <rect x='18' y='30' width='48' height='4' rx='2' fill='white' fill-opacity='.35'/>
    <rect x='18' y='56' width='124' height='26' rx='6' fill='white' fill-opacity='.08'/>
    <circle cx='134' cy='24' r='7' fill='hsl(${hue} 90% 70%)'/>
  </svg>`
  const src = `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
  return (
    <img src={src} alt={`${label} template preview`} width={1600} height={1000}
      loading={eager ? 'eager' : 'lazy'} decoding="async"
      className="aspect-[16/10] w-full rounded-[12px] object-cover" />
  )
}
