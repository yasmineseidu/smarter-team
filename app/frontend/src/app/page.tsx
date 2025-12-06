export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold text-primary-600">Smarter Team</h1>
      <p className="mt-4 text-lg text-gray-600">
        Multi-Agent AI Agency Automation
      </p>
      <div className="mt-8 flex gap-4">
        <a
          href="/dashboard"
          className="rounded-lg bg-primary-600 px-6 py-3 text-white hover:bg-primary-700"
        >
          Dashboard
        </a>
        <a
          href="/docs"
          className="rounded-lg border border-gray-300 px-6 py-3 hover:bg-gray-50"
        >
          Documentation
        </a>
      </div>
    </main>
  );
}
