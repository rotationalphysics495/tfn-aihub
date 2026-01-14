# Architecture - Web (Next.js Frontend)

## Overview

The web frontend is a Next.js 14 application using the App Router pattern. It provides a manufacturing performance dashboard with AI chat capabilities, OEE monitoring, downtime analysis, and action recommendations.

## Technology Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Framework** | Next.js 14+ | React framework with App Router |
| **Language** | TypeScript 5.x | Type-safe JavaScript |
| **Styling** | Tailwind CSS 3.4+ | Utility-first CSS |
| **UI Library** | Radix UI + Shadcn/UI | Accessible component primitives |
| **Charts** | Recharts 3.6+ | Data visualization |
| **Markdown** | react-markdown + remark-gfm | AI response rendering |
| **Theming** | next-themes | Dark/light mode support |
| **Testing** | Vitest + Testing Library | Unit and component tests |

## Directory Structure

```
apps/web/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx            # Root layout with providers
│   │   ├── page.tsx              # Landing page
│   │   ├── globals.css           # Global styles
│   │   ├── (auth)/
│   │   │   └── login/page.tsx    # Login page
│   │   ├── auth/
│   │   │   └── callback/route.ts # Auth callback handler
│   │   ├── dashboard/
│   │   │   ├── page.tsx          # Main dashboard
│   │   │   ├── logout-button.tsx # Logout component
│   │   │   └── production/
│   │   │       ├── oee/page.tsx      # OEE dashboard
│   │   │       ├── downtime/page.tsx # Downtime analysis
│   │   │       └── throughput/page.tsx # Throughput view
│   │   ├── morning-report/
│   │   │   ├── page.tsx          # Morning report page
│   │   │   └── loading.tsx       # Loading state
│   │   └── api/
│   │       └── health/route.ts   # Health check API route
│   ├── components/               # React components
│   │   ├── ui/                   # Base UI components (Shadcn)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── alert.tsx
│   │   │   ├── tooltip.tsx
│   │   │   ├── sheet.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   └── textarea.tsx
│   │   ├── chat/                 # AI Chat components
│   │   │   ├── ChatSidebar.tsx   # Main chat sidebar
│   │   │   ├── ChatTrigger.tsx   # Trigger button
│   │   │   ├── ChatMessage.tsx   # Message display
│   │   │   ├── MessageList.tsx   # Message list
│   │   │   ├── CitationLink.tsx  # Citation rendering
│   │   │   ├── CitationPanel.tsx # Citation details
│   │   │   ├── FollowUpChips.tsx # Suggested questions
│   │   │   ├── ChatLoadingIndicator.tsx
│   │   │   ├── types.ts          # Chat type definitions
│   │   │   └── index.ts          # Barrel export
│   │   ├── action-engine/        # Action Engine components
│   │   │   ├── ActionCardList.tsx
│   │   │   ├── InsightSection.tsx
│   │   │   ├── EvidenceSection.tsx
│   │   │   ├── InsightEvidenceCard.tsx
│   │   │   ├── PriorityBadge.tsx
│   │   │   ├── transformers.ts
│   │   │   ├── types.ts
│   │   │   └── index.ts
│   │   ├── action-list/          # Action List components
│   │   │   ├── ActionListContainer.tsx
│   │   │   ├── ActionItemCard.tsx
│   │   │   ├── ActionListSkeleton.tsx
│   │   │   ├── EmptyActionState.tsx
│   │   │   ├── MorningSummarySection.tsx
│   │   │   └── index.ts
│   │   ├── dashboard/            # Dashboard components
│   │   ├── oee/                  # OEE-specific components
│   │   ├── downtime/             # Downtime components
│   │   ├── production/           # Production components
│   │   ├── safety/               # Safety components
│   │   ├── financial/            # Financial components
│   │   ├── navigation/           # Navigation components
│   │   └── theme-provider.tsx    # Theme context provider
│   └── lib/
│       ├── utils.ts              # Utility functions (cn)
│       └── supabase/             # Supabase client utilities
├── public/                       # Static assets
├── tailwind.config.ts           # Tailwind configuration
├── tsconfig.json                # TypeScript configuration
├── next.config.js               # Next.js configuration
├── vitest.config.ts             # Vitest configuration
└── package.json                 # Dependencies
```

## Core Architecture Components

### 1. Root Layout

The root layout (`src/app/layout.tsx`) provides:
- Inter font configuration ("Industrial Clarity Design System")
- ThemeProvider for dark/light mode
- Global ChatSidebar component (accessible from anywhere)

```tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <ThemeProvider>
          {children}
          <ChatSidebar />  {/* Global AI chat */}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

### 2. Component Architecture

**Component Categories:**

| Category | Path | Purpose |
|----------|------|---------|
| **UI Primitives** | `components/ui/` | Shadcn/UI base components |
| **Chat** | `components/chat/` | AI chat interface |
| **Action Engine** | `components/action-engine/` | Action recommendations |
| **Action List** | `components/action-list/` | Daily action items |
| **Domain** | `components/{domain}/` | Feature-specific components |

### 3. AI Chat System

The chat system (Story 4.3) provides:
- Slide-out sidebar accessible via floating trigger
- Markdown rendering with citations
- Follow-up question chips
- Citation panel for data source details

**Key Components:**
- `ChatSidebar` - Main container with sheet overlay
- `ChatMessage` - Individual message with markdown support
- `CitationLink` - Inline citation markers
- `CitationPanel` - Expanded citation details
- `FollowUpChips` - Suggested follow-up questions

### 4. Action Engine

Prioritized daily action recommendations (Story 7.3):
- Safety-first prioritization
- Financial impact ranking
- Evidence-based recommendations

### 5. Design System

**Industrial Clarity Design System:**
- Inter font for screen readability
- Tailwind CSS with custom theme
- Dark/light mode support
- Consistent spacing and color palette

**Tailwind Configuration:**
- Custom colors for manufacturing context
- Shadcn/UI component styles
- Responsive breakpoints

## Page Structure

### Authentication
| Route | Page | Description |
|-------|------|-------------|
| `/login` | Login | User authentication |
| `/auth/callback` | Callback | OAuth callback handler |

### Dashboard
| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Root landing page |
| `/dashboard` | Dashboard | Main dashboard |
| `/dashboard/production/oee` | OEE | OEE monitoring |
| `/dashboard/production/downtime` | Downtime | Downtime analysis |
| `/dashboard/production/throughput` | Throughput | Production throughput |

### Reports
| Route | Page | Description |
|-------|------|-------------|
| `/morning-report` | Morning Report | Daily summary report |

## State Management

- **Server Components**: Default for data fetching
- **Client Components**: Interactive UI elements
- **URL State**: Search params for filters
- **React Context**: Theme provider

## API Integration

The frontend communicates with the FastAPI backend via:

```typescript
// Example API call
const response = await fetch(`${API_URL}/api/agent/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: userMessage })
});
```

**Backend Endpoints Used:**
- `/api/agent/query` - AI agent queries
- `/api/chat` - Text-to-SQL chat
- `/api/actions` - Action recommendations
- `/api/oee` - OEE data
- `/api/production` - Production status
- `/api/safety` - Safety events

## Testing

```bash
cd apps/web
npm run test        # Run Vitest tests
npm run test:run    # Single run
```

**Test Files:**
- `src/components/chat/__tests__/ChatMessage.test.tsx`
- `src/components/chat/__tests__/FollowUpChips.test.tsx`
- `src/app/api/health/route.test.ts`

## Build & Development

```bash
# Development
npm run dev         # Start dev server (port 3000)

# Production
npm run build       # Build for production
npm run start       # Start production server

# Linting
npm run lint        # ESLint check
```

## Environment Variables

```bash
# apps/web/.env.example
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---
*Generated by BMAD Document Project Workflow on 2026-01-10*
