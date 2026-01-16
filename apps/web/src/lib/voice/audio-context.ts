/**
 * Audio Context Utilities (Story 8.1)
 *
 * Web Audio API helper utilities for advanced audio processing.
 * Handles browser autoplay policies and audio context management.
 *
 * AC#1: TTS Stream URL Generation - Audio context for playback
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 */

/**
 * Audio context state.
 */
export type AudioContextState = 'suspended' | 'running' | 'closed';

/**
 * Audio context wrapper for managing Web Audio API.
 */
class AudioContextManager {
  private context: AudioContext | null = null;
  private unlockPromise: Promise<void> | null = null;

  /**
   * Get or create the AudioContext.
   * Handles browser autoplay policies.
   */
  getContext(): AudioContext {
    if (!this.context) {
      // Create context with fallback for older browsers
      const AudioContextClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext })
          .webkitAudioContext;
      this.context = new AudioContextClass();
    }
    return this.context;
  }

  /**
   * Get the current state of the audio context.
   */
  getState(): AudioContextState | null {
    return this.context?.state || null;
  }

  /**
   * Check if audio context is available.
   */
  isAvailable(): boolean {
    return (
      typeof window !== 'undefined' &&
      ('AudioContext' in window ||
        'webkitAudioContext' in (window as unknown as Record<string, unknown>))
    );
  }

  /**
   * Resume the audio context (required for autoplay policy compliance).
   * Call this after a user interaction (click, tap).
   */
  async resume(): Promise<void> {
    const context = this.getContext();

    if (context.state === 'suspended') {
      await context.resume();
    }
  }

  /**
   * Unlock audio playback (call on first user interaction).
   * This is required by many browsers to allow audio playback.
   */
  async unlock(): Promise<void> {
    if (this.unlockPromise) {
      return this.unlockPromise;
    }

    this.unlockPromise = this.performUnlock();
    return this.unlockPromise;
  }

  private async performUnlock(): Promise<void> {
    const context = this.getContext();

    // Resume if suspended
    if (context.state === 'suspended') {
      await context.resume();
    }

    // Play a silent buffer to unlock audio
    const buffer = context.createBuffer(1, 1, 22050);
    const source = context.createBufferSource();
    source.buffer = buffer;
    source.connect(context.destination);
    source.start(0);

    // Wait for the silent audio to finish
    return new Promise((resolve) => {
      source.onended = () => resolve();
    });
  }

  /**
   * Close the audio context and release resources.
   */
  async close(): Promise<void> {
    if (this.context && this.context.state !== 'closed') {
      await this.context.close();
      this.context = null;
    }
  }

  /**
   * Decode audio data from an ArrayBuffer.
   */
  async decodeAudioData(arrayBuffer: ArrayBuffer): Promise<AudioBuffer> {
    const context = this.getContext();
    return context.decodeAudioData(arrayBuffer);
  }

  /**
   * Create an audio buffer source node.
   */
  createBufferSource(): AudioBufferSourceNode {
    const context = this.getContext();
    return context.createBufferSource();
  }

  /**
   * Create a gain node for volume control.
   */
  createGainNode(): GainNode {
    const context = this.getContext();
    return context.createGain();
  }

  /**
   * Get the destination node (speakers).
   */
  getDestination(): AudioDestinationNode {
    const context = this.getContext();
    return context.destination;
  }

  /**
   * Get the current time in the audio context.
   */
  getCurrentTime(): number {
    return this.context?.currentTime || 0;
  }

  /**
   * Get the sample rate of the audio context.
   */
  getSampleRate(): number {
    return this.context?.sampleRate || 44100;
  }
}

// Singleton instance
let audioContextManager: AudioContextManager | null = null;

/**
 * Get the singleton AudioContextManager instance.
 */
export function getAudioContextManager(): AudioContextManager {
  if (!audioContextManager) {
    audioContextManager = new AudioContextManager();
  }
  return audioContextManager;
}

/**
 * Create a new AudioContext.
 * Prefer using getAudioContextManager() for most use cases.
 */
export function createAudioContext(): AudioContext {
  return getAudioContextManager().getContext();
}

/**
 * Decode audio data from an ArrayBuffer.
 */
export async function decodeAudioData(
  arrayBuffer: ArrayBuffer
): Promise<AudioBuffer> {
  return getAudioContextManager().decodeAudioData(arrayBuffer);
}

/**
 * Check if Web Audio API is available.
 */
export function isAudioContextAvailable(): boolean {
  return getAudioContextManager().isAvailable();
}

/**
 * Resume the audio context after user interaction.
 */
export async function resumeAudioContext(): Promise<void> {
  return getAudioContextManager().resume();
}

/**
 * Unlock audio playback (call on first user interaction).
 */
export async function unlockAudio(): Promise<void> {
  return getAudioContextManager().unlock();
}

/**
 * Handle browser autoplay policies.
 * Call this function when mounting components that need audio.
 *
 * Returns a cleanup function to remove the event listener.
 */
export function setupAutoplayUnlock(
  onUnlocked?: () => void
): () => void {
  const handleInteraction = async () => {
    try {
      await unlockAudio();
      onUnlocked?.();
    } catch (error) {
      console.warn('Failed to unlock audio:', error);
    }
  };

  // Listen for first user interaction
  const events = ['click', 'touchstart', 'keydown'];
  const options = { once: true, passive: true };

  events.forEach((event) => {
    document.addEventListener(event, handleInteraction, options);
  });

  // Cleanup function
  return () => {
    events.forEach((event) => {
      document.removeEventListener(event, handleInteraction);
    });
  };
}

/**
 * Audio playback utilities.
 */
export const AudioUtils = {
  /**
   * Convert seconds to MM:SS format.
   */
  formatTime(seconds: number): string {
    if (!isFinite(seconds) || seconds < 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  },

  /**
   * Convert milliseconds to seconds.
   */
  msToSeconds(ms: number): number {
    return ms / 1000;
  },

  /**
   * Convert seconds to milliseconds.
   */
  secondsToMs(seconds: number): number {
    return seconds * 1000;
  },

  /**
   * Calculate progress percentage.
   */
  getProgress(currentTime: number, duration: number): number {
    if (duration === 0) return 0;
    return Math.min(100, (currentTime / duration) * 100);
  },

  /**
   * Check if browser supports audio playback.
   */
  isAudioSupported(): boolean {
    return typeof window !== 'undefined' && 'Audio' in window;
  },

  /**
   * Check if browser supports specific audio format.
   */
  canPlayType(mimeType: string): boolean {
    if (typeof window === 'undefined') return false;
    const audio = new Audio();
    return audio.canPlayType(mimeType) !== '';
  },

  /**
   * Common audio MIME types.
   */
  mimeTypes: {
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    ogg: 'audio/ogg',
    webm: 'audio/webm',
  },
};
