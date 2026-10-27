export type Template = { id: string; title: string; subtitle: string; span: string; hue: number; featured?: boolean }

export const templates: Template[] = [
  { id: 'aurora', title: 'Aurora', subtitle: 'SaaS launch page with motion-led hero', span: 'col-span-12 md:col-span-8', hue: 84, featured: true },
  { id: 'monolith', title: 'Monolith', subtitle: 'Agency portfolio, editorial grid', span: 'col-span-12 md:col-span-4', hue: 210 },
  { id: 'ledger', title: 'Ledger', subtitle: 'Fintech product page with data cards', span: 'col-span-12 md:col-span-4', hue: 160 },
  { id: 'atelier', title: 'Atelier', subtitle: 'Studio showcase, serif-heavy', span: 'col-span-12 md:col-span-4', hue: 20 },
  { id: 'signal', title: 'Signal', subtitle: 'Dev tool docs + marketing in one', span: 'col-span-12 md:col-span-4', hue: 260 },
  { id: 'orbit', title: 'Orbit', subtitle: 'Mobile app landing with device mock', span: 'col-span-12 md:col-span-6', hue: 300 },
  { id: 'harbor', title: 'Harbor', subtitle: 'E-commerce drop page, grid-first', span: 'col-span-12 md:col-span-6', hue: 40 },
  { id: 'vantage', title: 'Vantage', subtitle: 'Founder / personal site, single column', span: 'col-span-12 md:col-span-12', hue: 120 },
]

export const steps = [
  { n: '01', title: 'Pick a template.', body: 'Eight starting points, each a finished site rather than a kit of parts. Every one is tuned for Cursor, v0 and Lovable so the AI edits what you mean, not what it guesses.', hue: 84 },
  { n: '02', title: 'Describe the change.', body: 'The templates carry a design system in code: tokens, type scale, spacing, motion. Ask for a new section and the model has the vocabulary to build one that belongs.', hue: 210 },
  { n: '03', title: 'Ship it.', body: 'Static output, no runtime surprises. Deploy to Vercel, Netlify or a bucket. Lighthouse budget is enforced in CI, so the thing you ship is the thing you saw.', hue: 300 },
]

export const logos = ['Northwind', 'Halcyon', 'Fermata', 'Oblique', 'Tessellate', 'Kestrel']

export const testimonials = [
  { quote: 'First template I bought that I didn\'t immediately rip apart. The type scale alone saved me a week.', name: 'Mara Lindqvist', role: 'Founder, Halcyon' },
  { quote: 'Pointed Cursor at it, asked for a pricing page, got one that matched. That has never happened before.', name: 'Devon Achebe', role: 'Indie dev' },
  { quote: 'Our agency uses Monolith as the base for every portfolio pitch now.', name: 'Sofia Reyes', role: 'Creative Director, Oblique' },
  { quote: 'The motion is restrained. That\'s the whole point and nobody else gets it.', name: 'Jonas Weber', role: 'Design Engineer' },
  { quote: 'Lighthouse 98 out of the box. I didn\'t touch a thing.', name: 'Priya Natarajan', role: 'CTO, Fermata' },
  { quote: 'It reads like a human designed it. Clients can tell the difference even if they can\'t say why.', name: 'Elliot Park', role: 'Freelance' },
]

export type Tier = { eyebrow: string; name: string; price: string; blurb: string; features: { label: string; included: boolean }[]; cta: string; highlight?: boolean }

export const tiers: Tier[] = [
  {
    eyebrow: 'For one launch', name: 'Express', price: '€297', blurb: 'One template, ready to deploy.',
    features: [
      { label: 'Any single template', included: true },
      { label: 'Source + design tokens', included: true },
      { label: 'Cursor / v0 / Lovable prompts', included: true },
      { label: 'All 8 templates', included: false },
      { label: 'Lifetime updates', included: false },
      { label: 'Custom section build', included: false },
    ],
    cta: 'Get Express',
  },
  {
    eyebrow: 'Most picked', name: 'Standard', price: '€597', blurb: 'The full set, kept current.',
    features: [
      { label: 'All 8 templates', included: true },
      { label: 'Source + design tokens', included: true },
      { label: 'Cursor / v0 / Lovable prompts', included: true },
      { label: 'Lifetime updates', included: true },
      { label: 'Private Discord', included: true },
      { label: 'Custom section build', included: false },
    ],
    cta: 'Get Standard', highlight: true,
  },
  {
    eyebrow: 'Done with you', name: 'Custom', price: '€1,499', blurb: 'Standard, plus a section built for you.',
    features: [
      { label: 'Everything in Standard', included: true },
      { label: 'One custom section, designed + built', included: true },
      { label: 'Brand token pass', included: true },
      { label: '60-min working session', included: true },
      { label: 'Priority support, 30 days', included: true },
      { label: 'White-label rights', included: true },
    ],
    cta: 'Book Custom',
  },
]

export const faqs = [
  { q: 'What do I actually get?', a: 'A Vite + React + Tailwind project per template, with the design system expressed as tokens, a components folder, and a prompts file tuned for Cursor, v0 and Lovable.' },
  { q: 'Which AI tools are supported?', a: 'Cursor, v0 and Lovable are tested on every release. Anything that reads a repo and writes TypeScript will work; those three are the ones we keep green.' },
  { q: 'Can I use a template for client work?', a: 'Yes. Express and Standard cover unlimited projects for you or your clients. Custom adds white-label rights so you can strip the attribution.' },
  { q: 'Is it a subscription?', a: 'No. Every tier is a one-time payment. Standard and Custom include lifetime updates to the templates you bought.' },
  { q: 'What about Next.js or Astro?', a: 'The templates are plain Vite today. Each one is a single-page static site with no server dependencies, so porting is mostly moving files. Astro ports ship for Standard buyers early next year.' },
  { q: 'Do the fonts cost extra?', a: 'No. Geist, Geist Mono and Instrument Serif are open licences and load from Google Fonts. Swap them for your own in one file.' },
  { q: 'How are refunds handled?', a: '14 days, no questions, as long as you haven\'t deployed a site built from the template. Email us the order number.' },
  { q: 'Will the next template be free for me?', a: 'If you own Standard or Custom, yes. New templates are added to the set and show up in your account.' },
]

export const footerColumns = [
  { title: 'Templates', links: ['Browse all', 'Aurora', 'Monolith', 'Ledger', 'Changelog'] },
  { title: 'Method', links: ['How it works', 'Design tokens', 'AI prompts', 'Lighthouse budget'] },
  { title: 'Company', links: ['About', 'Licence', 'Refunds', 'Contact'] },
]
