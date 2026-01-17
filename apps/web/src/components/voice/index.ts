/**
 * Voice Components Index (Story 8.1, 8.2, 8.4, 8.7)
 *
 * Exports all voice-related React components.
 */

// Story 8.1 - TTS
export { BriefingPlayer, type BriefingPlayerProps, type BriefingSection } from './BriefingPlayer';

// Story 8.2 - STT
export { PushToTalkButton, type PushToTalkButtonProps } from './PushToTalkButton';
export { TranscriptPanel, type TranscriptPanelProps, type TranscriptEntry } from './TranscriptPanel';

// Story 8.7 - Area-by-Area Delivery UI
export { AreaProgress, type AreaProgressProps } from './AreaProgress';
export { VoiceControls, type VoiceControlsProps } from './VoiceControls';
export { BriefingTranscript, type BriefingTranscriptProps } from './BriefingTranscript';
export { PauseCountdown, type PauseCountdownProps } from './PauseCountdown';
