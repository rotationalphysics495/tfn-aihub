/**
 * AreaProgress Component Tests (Story 8.7 Task 2.6)
 *
 * Tests for the AreaProgress stepper component including:
 * - Vertical stepper rendering with area names
 * - Current section highlighting
 * - Completed sections with checkmarks
 * - Upcoming sections dimmed
 * - Responsive design
 *
 * AC#1: Clear visual interface showing briefing progress
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AreaProgress, AreaProgressProps } from '../AreaProgress';
import { BriefingSection } from '@/lib/hooks/useBriefing';

// Mock sections for testing
const mockSections: BriefingSection[] = [
  {
    section_type: 'safety',
    title: 'Safety Update',
    content: 'No safety incidents reported.',
    area_id: 'grinding',
    status: 'completed',
    pause_point: true,
  },
  {
    section_type: 'production',
    title: 'Production Overview',
    content: 'Production is at 95% of target.',
    area_id: 'assembly',
    status: 'active',
    pause_point: true,
  },
  {
    section_type: 'quality',
    title: 'Quality Metrics',
    content: 'Quality rate is at 99.2%.',
    area_id: 'packaging',
    status: 'pending',
    pause_point: true,
  },
  {
    section_type: 'maintenance',
    title: 'Maintenance Update',
    content: 'Scheduled maintenance complete.',
    status: 'pending',
    pause_point: false,
  },
];

describe('AreaProgress', () => {
  const defaultProps: AreaProgressProps = {
    sections: mockSections,
    currentIndex: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all section titles', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByText('Safety Update')).toBeInTheDocument();
      expect(screen.getByText('Production Overview')).toBeInTheDocument();
      expect(screen.getByText('Quality Metrics')).toBeInTheDocument();
      expect(screen.getByText('Maintenance Update')).toBeInTheDocument();
    });

    it('renders progress header with count', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByText('Briefing Progress')).toBeInTheDocument();
      expect(screen.getByText('2 of 4')).toBeInTheDocument();
    });

    it('renders navigation role', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByRole('navigation')).toHaveAttribute(
        'aria-label',
        'Briefing progress'
      );
    });

    it('renders section list', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByRole('list')).toHaveAttribute(
        'aria-label',
        'Section list'
      );
    });
  });

  describe('Current section highlighting (AC#1)', () => {
    it('highlights current section with correct styling', () => {
      render(<AreaProgress {...defaultProps} />);

      // Current section (index 1) should have bold text
      const currentTitle = screen.getByText('Production Overview');
      expect(currentTitle).toHaveClass('text-blue-700');
      expect(currentTitle).toHaveClass('font-semibold');
    });

    it('applies aria-current to current step indicator', () => {
      render(<AreaProgress {...defaultProps} />);

      const stepIndicators = screen.getAllByText((content, element) => {
        return element?.tagName === 'SPAN' && /^[1-4]$/.test(content);
      });

      // Find the step indicator with aria-current
      const currentIndicator = document.querySelector('[aria-current="step"]');
      expect(currentIndicator).toBeInTheDocument();
    });

    it('shows section type badge for current section', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByText('production')).toBeInTheDocument();
    });
  });

  describe('Completed sections (AC#1)', () => {
    it('shows checkmark icon for completed sections', () => {
      render(<AreaProgress {...defaultProps} />);

      // First section is completed (index 0, currentIndex is 1)
      const listItems = screen.getAllByRole('listitem');
      const completedItem = listItems[0];

      // Check for checkmark SVG
      const checkmark = completedItem.querySelector('svg');
      expect(checkmark).toBeInTheDocument();
    });

    it('shows "Completed" status text for completed sections', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByText('Completed')).toBeInTheDocument();
    });

    it('applies muted styling to completed sections', () => {
      render(<AreaProgress {...defaultProps} />);

      const completedTitle = screen.getByText('Safety Update');
      expect(completedTitle).toHaveClass('text-gray-500');
    });
  });

  describe('Upcoming sections (AC#1)', () => {
    it('applies dimmed styling to upcoming sections', () => {
      render(<AreaProgress {...defaultProps} />);

      const upcomingTitle = screen.getByText('Quality Metrics');
      expect(upcomingTitle).toHaveClass('text-gray-400');
    });

    it('shows number indicator for upcoming sections', () => {
      render(<AreaProgress {...defaultProps} />);

      // Section 3 and 4 should show numbers
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });
  });

  describe('Area ID display', () => {
    it('shows area ID when provided and not in compact mode', () => {
      render(<AreaProgress {...defaultProps} compact={false} />);

      expect(screen.getByText('grinding')).toBeInTheDocument();
      expect(screen.getByText('assembly')).toBeInTheDocument();
      expect(screen.getByText('packaging')).toBeInTheDocument();
    });

    it('hides area ID in compact mode', () => {
      render(<AreaProgress {...defaultProps} compact={true} />);

      // Area IDs should not be visible in compact mode
      // They are rendered but with conditional display
      const areaIds = screen.queryAllByText(/grinding|assembly|packaging/);
      // In compact mode, area_id divs are not rendered
      expect(areaIds.length).toBe(0);
    });
  });

  describe('Progress bar', () => {
    it('renders progress bar', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByText('Start')).toBeInTheDocument();
      expect(screen.getByText('50% complete')).toBeInTheDocument();
    });

    it('calculates correct progress percentage', () => {
      render(<AreaProgress sections={mockSections} currentIndex={2} />);

      expect(screen.getByText('75% complete')).toBeInTheDocument();
    });

    it('shows 25% for first section', () => {
      render(<AreaProgress sections={mockSections} currentIndex={0} />);

      expect(screen.getByText('25% complete')).toBeInTheDocument();
    });

    it('shows 100% when on last section', () => {
      render(<AreaProgress sections={mockSections} currentIndex={3} />);

      expect(screen.getByText('100% complete')).toBeInTheDocument();
    });
  });

  describe('Section click handling', () => {
    it('calls onSectionClick when section is clicked', () => {
      const onSectionClick = vi.fn();
      render(<AreaProgress {...defaultProps} onSectionClick={onSectionClick} />);

      const upcomingButton = screen.getByText('Quality Metrics').closest('button');
      if (upcomingButton) {
        fireEvent.click(upcomingButton);
      }

      expect(onSectionClick).toHaveBeenCalledWith(2);
    });

    it('does not render as clickable when no handler provided', () => {
      render(<AreaProgress {...defaultProps} />);

      const sectionButton = screen.getByText('Quality Metrics').closest('button');
      expect(sectionButton).toHaveAttribute('disabled');
    });

    it('applies hover styles when clickable', () => {
      const onSectionClick = vi.fn();
      render(<AreaProgress {...defaultProps} onSectionClick={onSectionClick} />);

      const sectionButton = screen.getByText('Quality Metrics').closest('button');
      expect(sectionButton).toHaveClass('cursor-pointer');
    });
  });

  describe('Compact mode', () => {
    it('applies compact spacing in compact mode', () => {
      const { container } = render(<AreaProgress {...defaultProps} compact={true} />);

      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass('space-y-1');
    });

    it('applies normal spacing in non-compact mode', () => {
      const { container } = render(<AreaProgress {...defaultProps} compact={false} />);

      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass('space-y-2');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <AreaProgress {...defaultProps} className="custom-progress-class" />
      );

      expect(container.firstChild).toHaveClass('custom-progress-class');
    });
  });

  describe('Edge cases', () => {
    it('handles empty sections array', () => {
      render(<AreaProgress sections={[]} currentIndex={0} />);

      // Component renders without crashing and shows the Briefing Progress header
      expect(screen.getByText('Briefing Progress')).toBeInTheDocument();
      // Empty list is rendered but component handles gracefully
      expect(screen.getByRole('list')).toBeInTheDocument();
    });

    it('handles single section', () => {
      const singleSection = [mockSections[0]];
      render(<AreaProgress sections={singleSection} currentIndex={0} />);

      expect(screen.getByText('1 of 1')).toBeInTheDocument();
      expect(screen.getByText('100% complete')).toBeInTheDocument();
    });

    it('handles current index at start', () => {
      render(<AreaProgress sections={mockSections} currentIndex={0} />);

      const firstTitle = screen.getByText('Safety Update');
      expect(firstTitle).toHaveClass('text-blue-700');
    });

    it('handles current index at end', () => {
      render(<AreaProgress sections={mockSections} currentIndex={3} />);

      const lastTitle = screen.getByText('Maintenance Update');
      expect(lastTitle).toHaveClass('text-blue-700');
    });
  });

  describe('Accessibility', () => {
    it('has proper navigation landmarks', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('has accessible list structure', () => {
      render(<AreaProgress {...defaultProps} />);

      expect(screen.getByRole('list')).toBeInTheDocument();
      expect(screen.getAllByRole('listitem')).toHaveLength(4);
    });

    it('marks current step with aria-current', () => {
      render(<AreaProgress {...defaultProps} />);

      const currentStep = document.querySelector('[aria-current="step"]');
      expect(currentStep).toBeInTheDocument();
    });
  });
});
