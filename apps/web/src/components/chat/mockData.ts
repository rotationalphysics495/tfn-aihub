/**
 * Mock Data for Chat UI Development
 *
 * Placeholder messages for developing and demonstrating the chat interface.
 * Will be replaced with real AI responses in Stories 4.1, 4.2, 4.4, 4.5.
 *
 * @see Story 4.3 - Chat Sidebar UI
 */

import type { Message } from './types'

/**
 * Mock conversation demonstrating chat features:
 * - User query about production data
 * - AI response with citations (AC #6)
 * - Follow-up question
 * - Response with multiple citations
 */
export const MOCK_MESSAGES: Message[] = [
  {
    id: '1',
    role: 'user',
    content: 'What was the OEE for Grinder 5 yesterday?',
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
  },
  {
    id: '2',
    role: 'assistant',
    content:
      'Grinder 5 had an OEE of 78.3% yesterday, which is 6.7% below the target of 85%. The main contributing factor was a 45-minute unplanned stop due to bearing overheating.',
    timestamp: new Date(Date.now() - 4 * 60 * 1000), // 4 minutes ago
    citations: [
      { source: 'daily_summaries', dataPoint: 'OEE: 78.3%', timestamp: '2024-01-15' },
      { source: 'downtime_events', dataPoint: 'Bearing overheat - 45min', timestamp: '2024-01-15 10:23' },
    ],
  },
  {
    id: '3',
    role: 'user',
    content: 'How does this compare to last week?',
    timestamp: new Date(Date.now() - 3 * 60 * 1000), // 3 minutes ago
  },
  {
    id: '4',
    role: 'assistant',
    content:
      "Last week, Grinder 5 averaged 82.1% OEE, so yesterday's performance was 3.8% below the weekly average. The bearing issue appears to be recurring - this is the third heat-related stop this month.",
    timestamp: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
    citations: [
      { source: 'weekly_trends', dataPoint: 'Avg OEE: 82.1%', timestamp: 'Week 2, 2024' },
      { source: 'maintenance_logs', dataPoint: '3 bearing heat events in Jan', timestamp: '2024-01' },
    ],
  },
]

/**
 * Empty state messages for initial welcome
 */
export const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content:
    "Hello! I'm your AI factory analyst. Ask me about production metrics, equipment performance, downtime analysis, or any other factory data. I'll provide insights backed by your actual data.",
  timestamp: new Date(),
}
