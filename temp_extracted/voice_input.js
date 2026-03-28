/**
 * static/js/voice_input.js
 * =========================
 * Complete Urdu voice input + output controller for Kisan Smart.
 *
 * Features:
 *   - Mic recording via MediaRecorder API (WebM/OGG in browser)
 *   - Live waveform visualisation using Web Audio API AnalyserNode
 *   - POST audio blob to /api/voice/transcribe
 *   - Confirmation step before submitting to ML predictor
 *   - Auto-play Urdu TTS recommendation after prediction
 *   - Graceful fallback when mic is unavailable
 *   - Accessibility: slow mode toggle, transcript display
 *
 * Usage:
 *   const voice = new KisanVoice({ jwtToken: '<jwt>' });
 *   voice.init();  // wire up all DOM elements
 */

class KisanVoice {
  /**
   * @param {object} opts
   * @param {string} opts.jwtToken      - JWT bearer token
   * @param {string} [opts.micBtnId]    - ID of the mic button element
   * @param {string} [opts.statusId]    - ID of status text element
   * @param {string} [opts.transcriptId] - ID of transcript display element
   * @param {string} [opts.canvasId]    - ID of waveform canvas element
   * @param {boolean} [opts.slowSpeech] - Use slower TTS (accessibility)
   * @param {function} [opts.onValues]  - Callback when soil values extracted
   * @param {function} [opts.onError]   - Callback on error
   */
  constructor(opts = {}) {
    this.jwtToken     = opts.jwtToken || '';
    this.micBtnId     = opts.micBtnId     || 'voice-btn';
    this.statusId     = opts.statusId     || 'voice-status';
    this.transcriptId = opts.transcriptId || 'voice-transcript';
    this.canvasId     = opts.canvasId     || 'voice-waveform';
    this.slowSpeech   = opts.slowSpeech   || false;
    this.onValues     = opts.onValues     || (() => {});
    this.onError      = opts.onError      || (() => {});

    // Internal state
    this._state         = 'idle';   // idle | recording | processing | confirming | speaking
    this._recorder      = null;
    this._chunks        = [];
    this._stream        = null;
    this._audioCtx      = null;
    this._analyser      = null;
    this._rafId         = null;
    this._lastResult    = null;
    this._mimeType      = 'audio/webm';
    this._maxDuration   = 30000;    // ms — Whisper's 30-second window
    this._autoStopTimer = null;
  }

  // ── Initialisation ────────────────────────────────────────────────────────

  init() {
    this._btn        = document.getElementById(this.micBtnId);
    this._statusEl   = document.getElementById(this.statusId);
    this._transcriptEl = document.getElementById(this.transcriptId);
    this._canvas     = document.getElementById(this.canvasId);

    if (!this._btn) {
      console.warn(`KisanVoice: button #${this.micBtnId} not found`);
      return;
    }

    // Check browser support
    if (!navigator.mediaDevices || !window.MediaRecorder) {
      this._setStatus('آپ کا براؤزر مائیک کی سہولت نہیں دیتا', 'error');
      this._btn.disabled = true;
      return;
    }

    this._btn.addEventListener('click', () => this._handleBtnClick());
    this._setStatus('مائیک کا بٹن دبائیں', 'idle');

    // Pre-load greeting audio
    this._prefetchGreeting();
  }

  // ── Main button handler ───────────────────────────────────────────────────

  _handleBtnClick() {
    switch (this._state) {
      case 'idle':        this._startRecording(); break;
      case 'recording':   this._stopRecording();  break;
      case 'confirming':  this._confirmValues();  break;
      default:
        // Ignore clicks during processing/speaking
    }
  }

  // ── Recording ─────────────────────────────────────────────────────────────

  async _startRecording() {
    try {
      this._stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount:    1,
          sampleRate:      16000,   // Whisper prefers 16kHz
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
    } catch (err) {
      this._setStatus('مائیک کی اجازت نہیں ملی', 'error');
      this.onError('mic_permission_denied');
      return;
    }

    // Determine best MIME type (browser-dependent)
    this._mimeType = this._getBestMimeType();

    this._chunks  = [];
    this._recorder = new MediaRecorder(this._stream, { mimeType: this._mimeType });
    this._recorder.ondataavailable = e => { if (e.data.size > 0) this._chunks.push(e.data); };
    this._recorder.onstop = () => this._onRecordingStop();

    this._recorder.start(100);  // collect chunks every 100ms
    this._setState('recording');
    this._setStatus('سن رہا ہوں... (روکنے کے لیے دوبارہ دبائیں)', 'recording');
    this._startWaveform();

    // Auto-stop after max duration
    this._autoStopTimer = setTimeout(() => {
      if (this._state === 'recording') this._stopRecording();
    }, this._maxDuration);
  }

  _stopRecording() {
    clearTimeout(this._autoStopTimer);
    if (this._recorder && this._recorder.state !== 'inactive') {
      this._recorder.stop();
    }
    this._stopWaveform();
    this._setState('processing');
    this._setStatus('سمجھ رہا ہوں...', 'processing');
  }

  async _onRecordingStop() {
    // Release microphone
    if (this._stream) {
      this._stream.getTracks().forEach(t => t.stop());
      this._stream = null;
    }

    const blob = new Blob(this._chunks, { type: this._mimeType });
    if (blob.size < 1000) {
      this._setStatus('آواز نہیں آئی، دوبارہ کوشش کریں', 'error');
      this._setState('idle');
      return;
    }

    await this._sendForTranscription(blob);
  }

  // ── Transcription ──────────────────────────────────────────────────────────

  async _sendForTranscription(blob) {
    try {
      const resp = await fetch('/api/voice/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type':  this._mimeType,
          'Authorization': `Bearer ${this.jwtToken}`,
        },
        body: blob,
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || `Server error ${resp.status}`);
      }

      const result = await resp.json();
      this._lastResult = result;

      // Show transcript
      if (this._transcriptEl && result.transcript) {
        this._transcriptEl.textContent = result.transcript;
        this._transcriptEl.style.direction = 'rtl';
      }

      if (result.needs_confirmation) {
        // Ask farmer to confirm parsed values
        await this._askConfirmation(result);
      } else if (result.parse_confidence >= 0.6) {
        // Good parse — auto submit
        this._submitValues(result);
      } else {
        // Poor parse — show error
        this._setStatus('قدریں سمجھ نہیں آئیں، دوبارہ بولیں', 'error');
        await this._playTemplate('error_incomplete');
        this._setState('idle');
      }

    } catch (err) {
      console.error('Transcription error:', err);
      this._setStatus(`خرابی: ${err.message}`, 'error');
      this.onError(err.message);
      this._setState('idle');
    }
  }

  // ── Confirmation ───────────────────────────────────────────────────────────

  async _askConfirmation(result) {
    this._setState('confirming');

    const cropName = result.crop || 'نامعلوم';
    const msg = [
      `فصل: ${cropName}`,
      result.nitrogen   !== null ? `N: ${result.nitrogen}`   : '',
      result.phosphorus !== null ? `P: ${result.phosphorus}` : '',
      result.potassium  !== null ? `K: ${result.potassium}`  : '',
      result.ph         !== null ? `pH: ${result.ph}`        : '',
    ].filter(Boolean).join(' | ');

    this._setStatus(`${msg} — تصدیق کے لیے دوبارہ دبائیں`, 'confirming');

    // Play audio confirmation
    await this._speakConfirmation(result);
  }

  _confirmValues() {
    if (this._lastResult) {
      this._submitValues(this._lastResult);
    }
  }

  // ── Value submission ───────────────────────────────────────────────────────

  _submitValues(result) {
    this._setState('idle');
    this._setStatus('مل گیا! سفارش تیار ہو رہی ہے...', 'success');

    // Fill the main form fields if they exist
    const fieldMap = {
      'crop':       result.crop,
      'nitrogen':   result.nitrogen,
      'phosphorus': result.phosphorus,
      'potassium':  result.potassium,
      'ph':         result.ph,
    };

    for (const [fieldId, value] of Object.entries(fieldMap)) {
      if (value === null) continue;
      const el = document.getElementById(fieldId);
      if (!el) continue;

      if (el.tagName === 'SELECT') {
        // Find matching option for crop
        const opt = Array.from(el.options).find(o =>
          o.value.toLowerCase().includes(String(value).toLowerCase())
        );
        if (opt) el.value = opt.value;
      } else {
        el.value = value;
        // Trigger input event so sliders update their fill bar
        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }

    // Fire callback
    this.onValues(result);
  }

  // ── TTS playback ───────────────────────────────────────────────────────────

  async speakRecommendation(crop, fertilizer, quantity, confidence) {
    this._setState('speaking');
    this._setStatus('سفارش سن رہے ہیں...', 'speaking');

    try {
      const resp = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Bearer ${this.jwtToken}`,
        },
        body: JSON.stringify({
          mode:       'recommendation',
          crop,
          fertilizer,
          quantity,
          confidence,
          detail:     'full',
          slow:       this.slowSpeech,
        }),
      });

      if (!resp.ok) throw new Error(`TTS error ${resp.status}`);

      const blob = await resp.blob();
      await this._playAudioBlob(blob);

    } catch (err) {
      console.warn('TTS playback failed:', err);
    } finally {
      this._setState('idle');
      this._setStatus('مائیک کا بٹن دبائیں', 'idle');
    }
  }

  async _speakConfirmation(result) {
    try {
      const resp = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Bearer ${this.jwtToken}`,
        },
        body: JSON.stringify({
          mode: 'confirm',
          crop: result.crop,
          n:    result.nitrogen,
          p:    result.phosphorus,
          k:    result.potassium,
          ph:   result.ph,
        }),
      });
      if (resp.ok) await this._playAudioBlob(await resp.blob());
    } catch (e) { /* silent fail — TTS is enhancement, not blocker */ }
  }

  async _playTemplate(key) {
    try {
      const resp = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Bearer ${this.jwtToken}`,
        },
        body: JSON.stringify({ mode: 'template', key }),
      });
      if (resp.ok) await this._playAudioBlob(await resp.blob());
    } catch (e) {}
  }

  async _prefetchGreeting() {
    // Fire-and-forget: warm up TTS cache on page load
    try {
      await fetch('/api/voice/greeting', {
        headers: { 'Authorization': `Bearer ${this.jwtToken}` }
      });
    } catch (e) {}
  }

  _playAudioBlob(blob) {
    return new Promise((resolve) => {
      const url    = URL.createObjectURL(blob);
      const audio  = new Audio(url);
      audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
      audio.onerror = () => { URL.revokeObjectURL(url); resolve(); };
      audio.play().catch(resolve);
    });
  }

  // ── Waveform visualiser ────────────────────────────────────────────────────

  _startWaveform() {
    if (!this._canvas || !this._stream) return;

    this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    this._analyser = this._audioCtx.createAnalyser();
    this._analyser.fftSize = 512;

    const src = this._audioCtx.createMediaStreamSource(this._stream);
    src.connect(this._analyser);

    const ctx    = this._canvas.getContext('2d');
    const W      = this._canvas.width;
    const H      = this._canvas.height;
    const bufLen = this._analyser.frequencyBinCount;
    const data   = new Uint8Array(bufLen);

    const draw = () => {
      this._rafId = requestAnimationFrame(draw);
      this._analyser.getByteTimeDomainData(data);

      ctx.clearRect(0, 0, W, H);
      ctx.lineWidth   = 2;
      ctx.strokeStyle = '#40916C';
      ctx.beginPath();

      const sliceW = W / bufLen;
      let x = 0;
      for (let i = 0; i < bufLen; i++) {
        const v = data[i] / 128.0;
        const y = (v * H) / 2;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        x += sliceW;
      }
      ctx.lineTo(W, H / 2);
      ctx.stroke();
    };
    draw();
  }

  _stopWaveform() {
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._audioCtx) {
      this._audioCtx.close();
      this._audioCtx = null;
    }
    if (this._canvas) {
      const ctx = this._canvas.getContext('2d');
      ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  _setState(state) {
    this._state = state;
    if (!this._btn) return;

    const icons = {
      idle:        '🎙️',
      recording:   '⏹️',
      processing:  '⏳',
      confirming:  '✅',
      speaking:    '🔊',
    };
    const labels = {
      idle:        'آواز سے داخل کریں',
      recording:   'روکیں',
      processing:  'انتظار کریں...',
      confirming:  'تصدیق کریں',
      speaking:    'سنیں...',
    };

    this._btn.dataset.state  = state;
    this._btn.disabled = (state === 'processing' || state === 'speaking');
    const iconEl  = this._btn.querySelector('.voice-icon');
    const labelEl = this._btn.querySelector('.voice-label');
    if (iconEl)  iconEl.textContent  = icons[state]  || '🎙️';
    if (labelEl) labelEl.textContent = labels[state] || '';
  }

  _setStatus(msg, type = 'idle') {
    if (!this._statusEl) return;
    this._statusEl.textContent  = msg;
    this._statusEl.dataset.type = type;
    this._statusEl.style.direction = 'rtl';
  }

  _getBestMimeType() {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/ogg',
      'audio/mp4',
    ];
    return types.find(t => MediaRecorder.isTypeSupported(t)) || 'audio/webm';
  }
}

// Auto-init if using data attributes on the button
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.querySelector('[data-kisan-voice]');
  if (btn) {
    const jwt = document.querySelector('meta[name="jwt-token"]')?.content || '';
    const voice = new KisanVoice({
      jwtToken:  jwt,
      micBtnId:  btn.id,
      slowSpeech: btn.dataset.slow === 'true',
    });
    voice.init();
    window._kisanVoice = voice; // expose for recommendation callback
  }
});
