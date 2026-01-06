import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Manufacturing Performance Assistant',
  description: 'Plant performance monitoring and insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
