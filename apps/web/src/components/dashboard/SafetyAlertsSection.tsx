'use client'

import { useState } from 'react'
import { SafetyAlertBanner, SafetyAlertCard, SafetyIndicator } from '@/components/safety'
import { SafetyEventModal, type SafetyEventDetail } from '@/components/downtime/SafetyEventModal'
import { useSafetyAlerts, type SafetyAlert } from '@/hooks/useSafetyAlerts'

/**
 * Safety Alerts Section
 *
 * Integrates safety alerts into the Command Center dashboard.
 * Displays the alert banner when active alerts exist.
 *
 * @see Story 2.6 - Safety Alert System
 * @see AC #4 - Safety alerts appear prominently in Live Pulse view
 * @see AC #5 - Links to specific asset
 * @see AC #6 - Alert persists until acknowledged
 */

interface SafetyAlertsSectionProps {
  className?: string
}

export function SafetyAlertsSection({ className }: SafetyAlertsSectionProps) {
  const {
    alerts,
    activeCount,
    isLoading,
    acknowledge,
    hasActiveAlerts,
  } = useSafetyAlerts({
    pollingInterval: 30000, // Poll every 30 seconds
  })

  const [selectedEvent, setSelectedEvent] = useState<SafetyEventDetail | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleAcknowledge = async (eventId: string) => {
    const success = await acknowledge(eventId)
    if (success && isModalOpen && selectedEvent?.id === eventId) {
      setIsModalOpen(false)
      setSelectedEvent(null)
    }
  }

  const handleViewDetails = (alert: SafetyAlert) => {
    // Convert SafetyAlert to SafetyEventDetail for the modal
    const eventDetail: SafetyEventDetail = {
      id: alert.id,
      asset_id: alert.asset_id,
      asset_name: alert.asset_name,
      area: alert.area,
      event_timestamp: alert.event_timestamp,
      reason_code: alert.reason_code,
      severity: alert.severity,
      description: alert.description,
      duration_minutes: alert.duration_minutes,
      financial_impact: alert.financial_impact,
      is_resolved: alert.acknowledged,
      resolved_at: alert.acknowledged_at,
    }
    setSelectedEvent(eventDetail)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedEvent(null)
  }

  if (!hasActiveAlerts && !isLoading) {
    return null
  }

  const activeAlerts = alerts.filter(a => !a.acknowledged)

  return (
    <div className={className}>
      {/* Safety Alert Banner - Prominent display */}
      {hasActiveAlerts && (
        <SafetyAlertBanner
          alerts={activeAlerts}
          onAcknowledge={handleAcknowledge}
          onViewDetails={handleViewDetails}
          className="mb-6"
        />
      )}

      {/* Safety Event Detail Modal */}
      <SafetyEventModal
        event={selectedEvent}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        isLoading={false}
      />
    </div>
  )
}

/**
 * Safety Header Indicator
 *
 * A small indicator for the header showing active alert count.
 */
interface SafetyHeaderIndicatorProps {
  onClick?: () => void
}

export function SafetyHeaderIndicator({ onClick }: SafetyHeaderIndicatorProps) {
  const { activeCount } = useSafetyAlerts({
    pollingInterval: 60000, // Poll every 60 seconds for header
  })

  return (
    <SafetyIndicator
      count={activeCount}
      onClick={onClick}
    />
  )
}
