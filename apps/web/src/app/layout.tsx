import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@/components/theme-provider'
import { ChatSidebar } from '@/components/chat'
import { ServiceWorkerProvider } from '@/components/offline/ServiceWorkerProvider'
import './globals.css'

/**
 * Inter font configuration for Industrial Clarity Design System
 *
 * Inter is optimized for screen readability and provides:
 * - Excellent legibility at all sizes
 * - Strong x-height for readability from distance
 * - Clear distinction between similar characters
 */
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

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
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <ServiceWorkerProvider>
            {children}
            {/* AI Chat Sidebar - accessible from anywhere in the application */}
            {/* @see Story 4.3 - Chat Sidebar UI, AC #1 */}
            <ChatSidebar />
          </ServiceWorkerProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
