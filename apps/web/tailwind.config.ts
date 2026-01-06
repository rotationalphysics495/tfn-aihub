import type { Config } from 'tailwindcss'
import forms from '@tailwindcss/forms'
import animate from 'tailwindcss-animate'

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    // Override default font sizes for "glanceability" - readable from 3 feet
    fontSize: {
      'xs': ['0.875rem', { lineHeight: '1.25rem' }],     // 14px - minimum for labels
      'sm': ['1rem', { lineHeight: '1.5rem' }],          // 16px - body minimum
      'base': ['1.125rem', { lineHeight: '1.75rem' }],   // 18px - default body
      'lg': ['1.25rem', { lineHeight: '1.75rem' }],      // 20px
      'xl': ['1.5rem', { lineHeight: '2rem' }],          // 24px
      '2xl': ['1.875rem', { lineHeight: '2.25rem' }],    // 30px
      '3xl': ['2.25rem', { lineHeight: '2.5rem' }],      // 36px - section headers
      '4xl': ['3rem', { lineHeight: '1' }],              // 48px - page titles
      '5xl': ['3.75rem', { lineHeight: '1' }],           // 60px - dashboard metrics
      '6xl': ['4.5rem', { lineHeight: '1' }],            // 72px
      '7xl': ['6rem', { lineHeight: '1' }],              // 96px
    },
    extend: {
      colors: {
        // Shadcn/UI semantic colors (using CSS variables for theme switching)
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },

        // ====== INDUSTRIAL CLARITY DESIGN SYSTEM ======

        // Safety - RESERVED EXCLUSIVELY for incidents only
        // DO NOT use for error states, destructive buttons, or general warnings
        safety: {
          red: '#DC2626',           // Exclusive safety incident color
          'red-light': '#FEE2E2',   // Light background for safety alerts
          'red-dark': '#991B1B',    // Dark mode safety color
        },

        // Warning status - use for non-safety alerts
        warning: {
          amber: '#F59E0B',
          'amber-light': '#FEF3C7',
          'amber-dark': '#B45309',
        },

        // Info status
        info: {
          blue: '#3B82F6',
          'blue-light': '#DBEAFE',
          'blue-dark': '#1D4ED8',
        },

        // Success status
        success: {
          green: '#10B981',
          'green-light': '#D1FAE5',
          'green-dark': '#047857',
        },

        // Mode colors - Retrospective (cool/static analysis)
        retrospective: {
          primary: '#6B7280',     // Cool gray
          surface: '#F3F4F6',     // Light background
          border: '#D1D5DB',      // Subtle border
          'surface-dark': '#374151', // Dark mode surface
          'border-dark': '#4B5563',  // Dark mode border
        },

        // Mode colors - Live (vibrant/real-time monitoring)
        live: {
          primary: '#8B5CF6',     // Vibrant purple
          surface: '#F5F3FF',     // Light purple background
          border: '#A78BFA',      // Purple border
          pulse: '#7C3AED',       // For animations
          'surface-dark': '#4C1D95', // Dark mode surface
          'border-dark': '#6D28D9',  // Dark mode border
        },

        // Industrial neutrals - optimized for factory floor visibility
        industrial: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
          950: '#030712',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'live-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        'safety-pulse': {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 0 0 rgba(220, 38, 38, 0.4)',
          },
          '50%': {
            opacity: '0.9',
            boxShadow: '0 0 0 8px rgba(220, 38, 38, 0)',
          },
        },
      },
      animation: {
        'live-pulse': 'live-pulse 2s ease-in-out infinite',
        'safety-pulse': 'safety-pulse 1.5s ease-in-out infinite',
      },
    },
  },
  plugins: [forms, animate],
}
export default config
