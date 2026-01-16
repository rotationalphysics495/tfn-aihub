/**
 * Push-to-Talk Utilities (Story 8.2)
 *
 * Recording utilities for voice input using MediaRecorder and WebSocket.
 * Handles audio capture, streaming, and STT communication.
 *
 * AC#1: Push-to-Talk Recording Initiation
 * AC#2: WebSocket STT Streaming
 *
 * References:
 * - [Source: architecture/voice-briefing.md#Voice Integration Architecture]
 * - [Source: prd/prd-non-functional-requirements.md#NFR10]
 */

export type RecordingState =
  | 'idle'
  | 'requesting_permission'
  | 'ready'
  | 'recording'
  | 'processing'
  | 'error';

export interface STTResult {
  text: string;
  confidence: number;
  durationMs: number;
}

export interface STTError {
  code: string;
  message: string;
}

export interface PushToTalkConfig {
  /** WebSocket URL for STT */
  websocketUrl: string;
  /** Session ID */
  sessionId?: string;
  /** Audio sample rate */
  sampleRate?: number;
  /** MIME type for recording */
  mimeType?: string;
  /** Callback when transcription is received */
  onTranscription?: (result: STTResult) => void;
  /** Callback on error */
  onError?: (error: STTError) => void;
  /** Callback when recording state changes */
  onStateChange?: (state: RecordingState) => void;
  /** Callback for audio level updates during recording */
  onAudioLevel?: (level: number) => void;
}

/**
 * Push-to-Talk manager class.
 *
 * Story 8.2 Implementation:
 * - AC#1: Manages MediaRecorder for audio capture
 * - AC#2: Streams audio to WebSocket for STT
 *
 * Usage:
 * ```typescript
 * const ptt = new PushToTalk({
 *   websocketUrl: '/api/v1/voice/stt',
 *   onTranscription: (result) => console.log(result.text),
 * });
 *
 * await ptt.initialize();
 * ptt.startRecording();
 * // ... user speaks
 * ptt.stopRecording();
 * ```
 */
export class PushToTalk {
  private config: PushToTalkConfig;
  private _state: RecordingState = 'idle';
  private mediaRecorder: MediaRecorder | null = null;
  private mediaStream: MediaStream | null = null;
  private websocket: WebSocket | null = null;
  private audioChunks: Blob[] = [];
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private animationFrameId: number | null = null;

  constructor(config: PushToTalkConfig) {
    this.config = {
      sampleRate: 16000,
      mimeType: 'audio/webm;codecs=opus',
      ...config,
    };
  }

  /**
   * Get current recording state.
   */
  get state(): RecordingState {
    return this._state;
  }

  /**
   * Check if MediaRecorder is supported.
   */
  static isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      'MediaRecorder' in window &&
      'getUserMedia' in navigator.mediaDevices
    );
  }

  /**
   * Get supported MIME types for recording.
   */
  static getSupportedMimeTypes(): string[] {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
    ];

    return types.filter((type) => MediaRecorder.isTypeSupported(type));
  }

  /**
   * Initialize the push-to-talk system.
   * Requests microphone permission and sets up recording.
   */
  async initialize(): Promise<boolean> {
    if (!PushToTalk.isSupported()) {
      this.setState('error');
      this.config.onError?.({
        code: 'not_supported',
        message: 'MediaRecorder is not supported in this browser',
      });
      return false;
    }

    this.setState('requesting_permission');

    try {
      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: this.config.sampleRate,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Find supported MIME type
      const supportedTypes = PushToTalk.getSupportedMimeTypes();
      const mimeType = supportedTypes.includes(this.config.mimeType!)
        ? this.config.mimeType!
        : supportedTypes[0];

      if (!mimeType) {
        throw new Error('No supported audio MIME types found');
      }

      // Create MediaRecorder
      this.mediaRecorder = new MediaRecorder(this.mediaStream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      // Set up audio level detection
      this.setupAudioAnalyser();

      // Set up MediaRecorder event handlers
      this.setupMediaRecorderEvents();

      this.setState('ready');
      return true;
    } catch (error) {
      this.setState('error');
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to access microphone';

      if (error instanceof DOMException && error.name === 'NotAllowedError') {
        this.config.onError?.({
          code: 'permission_denied',
          message: 'Microphone access was denied',
        });
      } else {
        this.config.onError?.({
          code: 'initialization_failed',
          message: errorMessage,
        });
      }
      return false;
    }
  }

  /**
   * Set up audio analyser for level detection.
   */
  private setupAudioAnalyser(): void {
    if (!this.mediaStream) return;

    try {
      this.audioContext = new AudioContext();
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);
    } catch (error) {
      console.warn('Failed to set up audio analyser:', error);
    }
  }

  /**
   * Set up MediaRecorder event handlers.
   */
  private setupMediaRecorderEvents(): void {
    if (!this.mediaRecorder) return;

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.audioChunks.push(event.data);
        this.sendAudioChunk(event.data);
      }
    };

    this.mediaRecorder.onstop = async () => {
      // Signal end of recording to server
      this.sendMessage({ type: 'end_recording' });
    };

    this.mediaRecorder.onerror = (event) => {
      this.setState('error');
      this.config.onError?.({
        code: 'recording_error',
        message: 'Recording failed',
      });
    };
  }

  /**
   * Connect to WebSocket for STT.
   */
  async connect(): Promise<boolean> {
    return new Promise((resolve) => {
      const sessionId = this.config.sessionId || crypto.randomUUID();
      const url = `${this.config.websocketUrl}?session_id=${sessionId}`;

      // Handle both ws:// and http:// URLs
      const wsUrl = url.startsWith('http')
        ? url.replace(/^http/, 'ws')
        : url;

      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log('STT WebSocket connected');
        resolve(true);
      };

      this.websocket.onmessage = (event) => {
        this.handleWebSocketMessage(event);
      };

      this.websocket.onerror = (error) => {
        console.error('STT WebSocket error:', error);
        this.config.onError?.({
          code: 'websocket_error',
          message: 'WebSocket connection failed',
        });
        resolve(false);
      };

      this.websocket.onclose = () => {
        console.log('STT WebSocket closed');
        this.websocket = null;
      };
    });
  }

  /**
   * Handle incoming WebSocket messages.
   */
  private handleWebSocketMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'transcription':
          this.setState('ready');
          this.config.onTranscription?.({
            text: data.text,
            confidence: data.confidence,
            durationMs: data.duration_ms,
          });
          break;

        case 'no_speech':
          this.setState('ready');
          this.config.onError?.({
            code: 'no_speech',
            message: data.message || 'No speech detected',
          });
          break;

        case 'recording_too_short':
          this.setState('ready');
          // Silent filter - no error shown
          break;

        case 'error':
          this.setState('ready');
          this.config.onError?.({
            code: data.error_code || 'stt_error',
            message: data.message || 'Transcription failed',
          });
          break;

        case 'recording_started':
          this.setState('recording');
          break;

        case 'recording_cancelled':
          this.setState('ready');
          break;

        case 'pong':
          // Heartbeat response
          break;

        default:
          console.log('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Send message to WebSocket.
   */
  private sendMessage(message: Record<string, unknown>): void {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
    }
  }

  /**
   * Send audio chunk to WebSocket.
   */
  private async sendAudioChunk(blob: Blob): Promise<void> {
    const arrayBuffer = await blob.arrayBuffer();
    const base64 = btoa(
      new Uint8Array(arrayBuffer).reduce(
        (data, byte) => data + String.fromCharCode(byte),
        ''
      )
    );

    this.sendMessage({
      type: 'audio_chunk',
      data: base64,
    });
  }

  /**
   * Start recording.
   *
   * AC#1: Push-to-Talk Recording Initiation
   */
  startRecording(): void {
    if (this._state !== 'ready') {
      console.warn('Cannot start recording in state:', this._state);
      return;
    }

    if (!this.mediaRecorder) {
      this.config.onError?.({
        code: 'not_initialized',
        message: 'Push-to-talk not initialized',
      });
      return;
    }

    // Clear previous chunks
    this.audioChunks = [];

    // Signal start to server
    this.sendMessage({ type: 'start_recording' });

    // Start recording with short timeslice for streaming
    this.mediaRecorder.start(100); // 100ms chunks

    // Start audio level monitoring
    this.startAudioLevelMonitoring();

    this.setState('recording');
  }

  /**
   * Stop recording.
   *
   * AC#2: Triggers transcription when recording stops
   */
  stopRecording(): void {
    if (this._state !== 'recording') {
      return;
    }

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }

    // Stop audio level monitoring
    this.stopAudioLevelMonitoring();

    this.setState('processing');
  }

  /**
   * Cancel recording without transcription.
   */
  cancelRecording(): void {
    if (this._state !== 'recording') {
      return;
    }

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }

    this.sendMessage({ type: 'cancel_recording' });
    this.stopAudioLevelMonitoring();
    this.setState('ready');
  }

  /**
   * Start monitoring audio levels.
   */
  private startAudioLevelMonitoring(): void {
    if (!this.analyser || !this.config.onAudioLevel) return;

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

    const updateLevel = () => {
      if (this._state !== 'recording') return;

      this.analyser!.getByteFrequencyData(dataArray);

      // Calculate average level
      const sum = dataArray.reduce((a, b) => a + b, 0);
      const average = sum / dataArray.length;
      const normalizedLevel = average / 255;

      this.config.onAudioLevel!(normalizedLevel);

      this.animationFrameId = requestAnimationFrame(updateLevel);
    };

    updateLevel();
  }

  /**
   * Stop monitoring audio levels.
   */
  private stopAudioLevelMonitoring(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Set state and notify callback.
   */
  private setState(state: RecordingState): void {
    this._state = state;
    this.config.onStateChange?.(state);
  }

  /**
   * Disconnect and cleanup.
   */
  disconnect(): void {
    this.stopAudioLevelMonitoring();

    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.mediaRecorder = null;

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.analyser = null;
    this.audioChunks = [];
    this.setState('idle');
  }
}

/**
 * Create a new PushToTalk instance.
 */
export function createPushToTalk(config: PushToTalkConfig): PushToTalk {
  return new PushToTalk(config);
}

/**
 * Check if push-to-talk is supported in this browser.
 */
export function isPushToTalkSupported(): boolean {
  return PushToTalk.isSupported();
}
