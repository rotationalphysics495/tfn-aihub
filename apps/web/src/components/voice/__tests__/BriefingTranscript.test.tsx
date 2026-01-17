/**
 * BriefingTranscript Component Tests (Story 8.7 Task 3.3)
 *
 * Tests for the BriefingTranscript component including:
 * - Text transcript display
 * - Auto-scroll to current section
 * - Section highlighting (current, completed, upcoming)
 * - Single vs all sections view
 *
 * AC#1: Text transcript of current section with auto-scroll
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BriefingTranscript, BriefingTranscriptProps } from '../BriefingTranscript';
import { BriefingSection } from '@/lib/hooks/useBriefing';

// Mock scrollIntoView since jsdom doesn't support it
const mockScrollIntoView = vi.fn();
window.HTMLElement.prototype.scrollIntoView = mockScrollIntoView;

// Mock sections for testing
const mockSections: BriefingSection[] = [
  {
    section_type: 'safety',
    title: 'Safety Update',
    content: 'No safety incidents reported in the last 24 hours. All safety protocols are being followed.',
    area_id: 'grinding',
    status: 'completed',
    pause_point: true,
  },
  {
    section_type: 'production',
    title: 'Production Overview',
    content: 'Production is currently at 95% of target. Machine efficiency is optimal.',
    area_id: 'assembly',
    status: 'active',
    pause_point: true,
  },
  {
    section_type: 'quality',
    title: 'Quality Metrics',
    content: 'Quality rate is at 99.2%, above our 98% target.',
    area_id: 'packaging',
    status: 'pending',
    pause_point: true,
  },
  {
    section_type: 'maintenance',
    title: 'Maintenance Update',
    content: 'Scheduled maintenance complete. All equipment operating normally.',
    status: 'pending',
    pause_point: false,
    error_message: 'Data temporarily unavailable for this area.',
  },
];

describe('BriefingTranscript', () => {
  const defaultProps: BriefingTranscriptProps = {
    sections: mockSections,
    currentIndex: 1,
    showAllSections: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Full transcript view (showAllSections=true)', () => {
    it('renders all section titles', () => {
      render(<BriefingTranscript {...defaultProps} />);

      expect(screen.getByText('Safety Update')).toBeInTheDocument();
      expect(screen.getByText('Production Overview')).toBeInTheDocument();
      expect(screen.getByText('Quality Metrics')).toBeInTheDocument();
      expect(screen.getByText('Maintenance Update')).toBeInTheDocument();
    });

    it('renders all section content', () => {
      render(<BriefingTranscript {...defaultProps} />);

      expect(screen.getByText(/No safety incidents reported/)).toBeInTheDocument();
      expect(screen.getByText(/Production is currently at 95%/)).toBeInTheDocument();
      expect(screen.getByText(/Quality rate is at 99.2%/)).toBeInTheDocument();
      expect(screen.getByText(/Scheduled maintenance complete/)).toBeInTheDocument();
    });

    it('shows section numbers for each section', () => {
      render(<BriefingTranscript {...defaultProps} />);

      // Should show numbers 1-4 or checkmarks
      expect(screen.getByText('2')).toBeInTheDocument(); // Current section
      expect(screen.getByText('3')).toBeInTheDocument(); // Upcoming
      expect(screen.getByText('4')).toBeInTheDocument(); // Upcoming
    });

    it('shows area ID for sections that have it', () => {
      render(<BriefingTranscript {...defaultProps} />);

      expect(screen.getByText('grinding')).toBeInTheDocument();
      expect(screen.getByText('assembly')).toBeInTheDocument();
      expect(screen.getByText('packaging')).toBeInTheDocument();
    });
  });

  describe('Current section highlighting (AC#1)', () => {
    it('highlights current section with blue styling', () => {
      render(<BriefingTranscript {...defaultProps} />);

      const currentTitle = screen.getByText('Production Overview');
      expect(currentTitle).toHaveClass('text-blue-800');
    });

    it('shows "Now Playing" badge for current section', () => {
      render(<BriefingTranscript {...defaultProps} />);

      expect(screen.getByText('Now Playing')).toBeInTheDocument();
    });

    it('applies ring styling to current section container', () => {
      const { container } = render(<BriefingTranscript {...defaultProps} />);

      const currentSection = container.querySelector('.ring-2');
      expect(currentSection).toBeInTheDocument();
    });
  });

  describe('Completed sections styling', () => {
    it('shows checkmark for completed sections', () => {
      const { container } = render(<BriefingTranscript {...defaultProps} />);

      // Completed section should have an SVG checkmark
      const transcriptSections = container.querySelectorAll('.transcript-section');
      const completedSection = transcriptSections[0];
      const checkmark = completedSection.querySelector('svg');
      expect(checkmark).toBeInTheDocument();
    });

    it('shows "Done" badge for completed sections', () => {
      render(<BriefingTranscript {...defaultProps} />);

      expect(screen.getByText('Done')).toBeInTheDocument();
    });

    it('applies muted styling to completed sections', () => {
      render(<BriefingTranscript {...defaultProps} />);

      const completedTitle = screen.getByText('Safety Update');
      expect(completedTitle).toHaveClass('text-gray-500');
    });

    it('applies opacity to completed section container', () => {
      const { container } = render(<BriefingTranscript {...defaultProps} />);

      const transcriptSections = container.querySelectorAll('.transcript-section');
      const completedSection = transcriptSections[0];
      expect(completedSection).toHaveClass('opacity-60');
    });
  });

  describe('Upcoming sections styling', () => {
    it('applies dimmed styling to upcoming sections', () => {
      render(<BriefingTranscript {...defaultProps} />);

      const upcomingTitle = screen.getByText('Quality Metrics');
      expect(upcomingTitle).toHaveClass('text-gray-400');
    });

    it('applies reduced opacity to upcoming section container', () => {
      const { container } = render(<BriefingTranscript {...defaultProps} />);

      const transcriptSections = container.querySelectorAll('.transcript-section');
      const upcomingSection = transcriptSections[2];
      expect(upcomingSection).toHaveClass('opacity-50');
    });

    it('shows number indicator for upcoming sections', () => {
      render(<BriefingTranscript {...defaultProps} />);

      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });
  });

  describe('Auto-scroll behavior (AC#1)', () => {
    it('calls scrollIntoView on current section', () => {
      render(<BriefingTranscript {...defaultProps} />);

      expect(mockScrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'start',
      });
    });

    it('calls scrollIntoView when currentIndex changes', () => {
      const { rerender } = render(<BriefingTranscript {...defaultProps} />);

      mockScrollIntoView.mockClear();

      rerender(<BriefingTranscript {...defaultProps} currentIndex={2} />);

      expect(mockScrollIntoView).toHaveBeenCalled();
    });
  });

  describe('Single section view (showAllSections=false)', () => {
    it('shows only current section title', () => {
      render(
        <BriefingTranscript {...defaultProps} showAllSections={false} />
      );

      expect(screen.getByText('Production Overview')).toBeInTheDocument();
      expect(screen.queryByText('Safety Update')).not.toBeInTheDocument();
      expect(screen.queryByText('Quality Metrics')).not.toBeInTheDocument();
    });

    it('shows only current section content', () => {
      render(
        <BriefingTranscript {...defaultProps} showAllSections={false} />
      );

      expect(screen.getByText(/Production is currently at 95%/)).toBeInTheDocument();
      expect(screen.queryByText(/No safety incidents/)).not.toBeInTheDocument();
    });

    it('shows section number for current section', () => {
      render(
        <BriefingTranscript {...defaultProps} showAllSections={false} />
      );

      expect(screen.getByText('2')).toBeInTheDocument(); // Current section is index 1
    });

    it('shows area ID in single section view', () => {
      render(
        <BriefingTranscript {...defaultProps} showAllSections={false} />
      );

      expect(screen.getByText('assembly')).toBeInTheDocument();
    });
  });

  describe('Error message display', () => {
    it('shows error message for current section with error', () => {
      render(
        <BriefingTranscript {...defaultProps} currentIndex={3} />
      );

      expect(screen.getByText(/Data temporarily unavailable/)).toBeInTheDocument();
    });

    it('shows error message in single section view', () => {
      render(
        <BriefingTranscript
          {...defaultProps}
          currentIndex={3}
          showAllSections={false}
        />
      );

      expect(screen.getByText(/Data temporarily unavailable/)).toBeInTheDocument();
    });

    it('does not show error for non-current sections in full view', () => {
      render(<BriefingTranscript {...defaultProps} currentIndex={1} />);

      // Error is on section 4 (index 3), current is section 2 (index 1)
      // In full view, error should only show for current section
      expect(screen.queryByText(/Data temporarily unavailable/)).not.toBeInTheDocument();
    });
  });

  describe('ScrollArea and maxHeight', () => {
    it('applies maxHeight to ScrollArea', () => {
      const { container } = render(
        <BriefingTranscript {...defaultProps} maxHeight="500px" />
      );

      const scrollArea = container.querySelector('[style*="max-height"]');
      expect(scrollArea).toHaveStyle({ maxHeight: '500px' });
    });

    it('uses default maxHeight of 400px', () => {
      const { container } = render(<BriefingTranscript {...defaultProps} />);

      const scrollArea = container.querySelector('[style*="max-height"]');
      expect(scrollArea).toHaveStyle({ maxHeight: '400px' });
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <BriefingTranscript {...defaultProps} className="custom-transcript-class" />
      );

      expect(container.firstChild).toHaveClass('custom-transcript-class');
    });
  });

  describe('Edge cases', () => {
    it('handles empty sections array', () => {
      render(<BriefingTranscript sections={[]} currentIndex={0} />);

      // Should render without errors
      const container = document.querySelector('.briefing-transcript');
      expect(container).toBeInTheDocument();
    });

    it('handles currentIndex at start', () => {
      render(<BriefingTranscript {...defaultProps} currentIndex={0} />);

      const firstTitle = screen.getByText('Safety Update');
      expect(firstTitle).toHaveClass('text-blue-800');
    });

    it('handles currentIndex at end', () => {
      render(<BriefingTranscript {...defaultProps} currentIndex={3} />);

      const lastTitle = screen.getByText('Maintenance Update');
      expect(lastTitle).toHaveClass('text-blue-800');
    });

    it('handles single section', () => {
      const singleSection = [mockSections[0]];
      render(<BriefingTranscript sections={singleSection} currentIndex={0} />);

      expect(screen.getByText('Safety Update')).toBeInTheDocument();
      expect(screen.getByText('Now Playing')).toBeInTheDocument();
    });
  });

  describe('Content formatting', () => {
    it('preserves whitespace in content', () => {
      render(<BriefingTranscript {...defaultProps} />);

      const content = screen.getByText(/Production is currently at 95%/);
      expect(content).toHaveClass('whitespace-pre-wrap');
    });

    it('applies relaxed line height for readability', () => {
      render(<BriefingTranscript {...defaultProps} />);

      const content = screen.getByText(/Production is currently at 95%/);
      expect(content).toHaveClass('leading-relaxed');
    });
  });

  describe('Accessibility', () => {
    it('uses semantic HTML structure', () => {
      render(<BriefingTranscript {...defaultProps} />);

      // Should have heading elements for section titles
      const headings = screen.getAllByRole('heading', { level: 3 });
      expect(headings.length).toBeGreaterThan(0);
    });

    it('single section view uses h2 for title', () => {
      render(
        <BriefingTranscript {...defaultProps} showAllSections={false} />
      );

      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Production Overview');
    });
  });
});
