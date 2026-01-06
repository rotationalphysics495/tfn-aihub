export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-6 p-8">
        <h1 className="text-4xl font-bold text-foreground">
          Manufacturing Performance Assistant
        </h1>
        <p className="text-lg text-muted-foreground max-w-md mx-auto">
          Plant performance monitoring and insights dashboard.
        </p>
        <div className="flex flex-col items-center gap-4 pt-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-600">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <span>Next.js 14 with App Router</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-600">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <span>Tailwind CSS with Shadcn/UI</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-600">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <span>TypeScript configured</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground pt-6">
          Setup complete. Ready for development.
        </p>
      </div>
    </main>
  )
}
