import Link from "next/link";

const examples = [
  {
    title: "Instagram Post",
    size: "1:1",
    product: "Erdbeeren",
    price: "2,99",
    style: "EDEKA Style",
    image: "/landing-examples/erdbeeren-post.png",
    imageClassName: "aspect-square",
  },
  {
    title: "Story",
    size: "9:16",
    product: "Frische Pasta",
    price: "1,79",
    style: "Editorial",
    image: "/landing-examples/pasta-story.png",
    imageClassName: "aspect-[9/16]",
  },
  {
    title: "Plakat",
    size: "A4/A5",
    product: "Rispentomaten",
    price: "1,99",
    style: "Color Block",
    image: "/landing-examples/tomaten-plakat.png",
    imageClassName: "aspect-[1/1.414]",
  },
];

const features = [
  "Aktionsmotive für Post, Story und Plakat erstellen",
  "Produkt, Preis, Zeitraum und Stil direkt im Browser eingeben",
  "Eigene Produktfotos und gespeicherte Motive nutzen",
  "KI-Texte optional verwenden oder lokal im Profi-Modus arbeiten",
];

const steps = [
  { number: "1", title: "Einloggen", text: "Mit Zugangscode anmelden und direkt im Studio starten." },
  { number: "2", title: "Angebot eintragen", text: "Produkt, Preis, Zeitraum und Format auswählen." },
  { number: "3", title: "Motiv speichern", text: "Promotion prüfen und als fertige PNG-Datei exportieren." },
];

function ArrowIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M5 12h14m-6-6l6 6-6 6" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.4} d="M5 13l4 4L19 7" />
    </svg>
  );
}

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-app">
      <header className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-5 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3">
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-white shadow-card">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/waschbaer_logo.png" alt="EDEKA Waschbär" className="h-10 w-10 object-contain" />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-base font-extrabold leading-tight text-slate-950 sm:text-lg">EDEKA Mühlenbein</span>
            <span className="block text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Promo Studio</span>
          </span>
        </Link>

        <Link href="/login?next=/studio" className="btn-primary w-auto px-4">
          <span>Anmelden</span>
          <span className="hidden sm:inline">/ Registrieren</span>
        </Link>
      </header>

      <section className="mx-auto grid max-w-7xl gap-8 px-5 pb-10 pt-4 lg:grid-cols-[minmax(0,0.92fr)_minmax(460px,1.08fr)] lg:px-8 lg:pb-16 lg:pt-10">
        <div className="flex flex-col justify-center">
          <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-edeka-blue">Webbasiertes Promotion-Tool</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-extrabold leading-tight text-slate-950 sm:text-5xl lg:text-6xl">
            Aktionswerbung direkt im Browser erstellen.
          </h1>
          <p className="mt-5 max-w-2xl text-base font-medium leading-7 text-slate-600 sm:text-lg">
            Das Promo Studio macht aus Produkt, Preis und Aktionszeitraum ein fertiges EDEKA-Motiv für Social Media oder Plakat. Alles läuft in drei einfachen Schritten.
          </p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <Link href="/login?next=/studio" className="btn-primary sm:w-auto">
              <span>Anmelden / Registrieren</span>
              <ArrowIcon />
            </Link>
            <a href="#beispiele" className="btn-ghost sm:w-auto">
              Beispiele ansehen
            </a>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-[0.9fr_1.1fr]">
          <div className="panel flex flex-col justify-between overflow-hidden p-5">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">Workflow</p>
              <h2 className="mt-3 text-2xl font-extrabold leading-tight text-slate-950">Von Angebot zu fertiger Promotion</h2>
            </div>
            <ul className="mt-6 space-y-3">
              {features.map((feature) => (
                <li key={feature} className="flex gap-3 text-sm font-semibold leading-6 text-slate-700">
                  <span className="mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-edeka-yellow text-edeka-blue">
                    <CheckIcon />
                  </span>
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="grid gap-3">
            {examples.slice(0, 2).map((example) => (
              <div key={example.title} className="relative overflow-hidden rounded-lg bg-slate-950 p-3 shadow-elevated">
                <div className="absolute right-5 top-5 z-10 rounded-pill bg-white/95 px-3 py-1 text-xs font-extrabold text-edeka-blue shadow-sm">{example.size}</div>
                <div className={`mx-auto max-h-[360px] overflow-hidden rounded-md ${example.imageClassName}`}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={example.image} alt={`${example.title} Beispiel aus dem Promo Studio`} className="h-full w-full object-contain" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white py-12">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <div className="grid gap-4 md:grid-cols-3">
            {steps.map((step) => (
              <article key={step.number} className="rounded-lg border border-slate-200 bg-white p-5 shadow-card">
                <span className="grid h-10 w-10 place-items-center rounded-full bg-edeka-yellow text-sm font-extrabold text-edeka-blue">
                  {step.number}
                </span>
                <h2 className="mt-4 text-xl font-extrabold text-slate-950">{step.title}</h2>
                <p className="mt-2 text-sm font-medium leading-6 text-slate-600">{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="beispiele" className="bg-slate-50 py-12">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-edeka-blue">Beispiele</p>
              <h2 className="mt-2 text-3xl font-extrabold text-slate-950">Formate für jede Aktion</h2>
            </div>
            <p className="max-w-xl text-sm font-medium leading-6 text-slate-600">
              Die Beispiele zeigen die Art von Motiven, die das Studio aus Briefingdaten und Stilwahl erzeugt.
            </p>
          </div>

          <div className="mt-7 grid gap-4 md:grid-cols-3">
            {examples.map((example) => (
              <article key={example.title} className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-card">
                <div className="relative grid min-h-[340px] place-items-center bg-slate-100 p-4">
                  <span className="absolute left-4 top-4 z-10 rounded-pill bg-white/95 px-3 py-1 text-xs font-extrabold text-edeka-blue shadow-sm">{example.size}</span>
                  <div className={`max-h-[460px] overflow-hidden rounded-md bg-white shadow-sm ${example.imageClassName}`}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={example.image} alt={`${example.title} Beispiel aus dem Promo Studio`} className="h-full w-full object-contain" />
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="text-sm font-extrabold text-slate-950">{example.title}</h3>
                  <p className="mt-1 text-sm font-medium text-slate-500">
                    Echtes Beispiel aus dem Promo Studio: {example.product}, {example.style}, {example.size}.
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
