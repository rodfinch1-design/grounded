import { lazy, Suspense, useState } from 'react'
import Loader from './components/Loader'
import Nav from './components/Nav'
import Hero from './sections/Hero'

// Everything below the fold is code-split and deferred.
const Bento = lazy(() => import('./sections/Bento'))
const HowItWorks = lazy(() => import('./sections/HowItWorks'))
const SocialProof = lazy(() => import('./sections/SocialProof'))
const Pricing = lazy(() => import('./sections/Pricing'))
const FAQ = lazy(() => import('./sections/FAQ'))
const FinalCTA = lazy(() => import('./sections/FinalCTA'))
const Footer = lazy(() => import('./sections/Footer'))

export default function App() {
  const [ready, setReady] = useState(false)
  return (
    <>
      <Loader onDone={() => setReady(true)} />
      <Nav />
      <main>
        <Hero ready={ready} />
        <Suspense fallback={null}>
          <Bento />
          <HowItWorks />
          <SocialProof />
          <Pricing />
          <FAQ />
          <FinalCTA />
        </Suspense>
      </main>
      <Suspense fallback={null}><Footer /></Suspense>
    </>
  )
}
