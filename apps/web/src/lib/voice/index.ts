/**
 * Voice Library Index (Story 8.1, 8.2)
 *
 * Exports all voice-related utilities and clients.
 */

// ElevenLabs Client (Story 8.1)
export {
  ElevenLabsClient,
  createElevenLabsClient,
  type AudioEventHandler,
  type AudioEventType,
  type PlaybackState,
} from './elevenlabs-client';

// Audio Context Utilities (Story 8.1)
export {
  getAudioContextManager,
  createAudioContext,
  decodeAudioData,
  isAudioContextAvailable,
  resumeAudioContext,
  unlockAudio,
  setupAutoplayUnlock,
  AudioUtils,
  type AudioContextState,
} from './audio-context';

// Push-to-Talk (Story 8.2)
export {
  PushToTalk,
  createPushToTalk,
  isPushToTalkSupported,
  type RecordingState,
  type STTResult,
  type STTError,
  type PushToTalkConfig,
} from './push-to-talk';
