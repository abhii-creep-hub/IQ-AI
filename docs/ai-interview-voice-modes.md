# AI Interview Voice Modes

## Modes

- **Written Interview** uses the existing generated questions, typed answers, evaluation, and report flow.
- **Voice Interview** records a short browser audio clip, sends it to Gemini for transcription, lets the candidate/recruiter review and correct the transcript, then saves and evaluates the confirmed text.
- **Live AI Interview** is a turn-based spoken interview. The browser reads each question with its built-in speech synthesis; the answer is recorded and transcribed; the confirmed transcript is evaluated; and a contextual follow-up can be generated and added to the saved interview. Click **Read question aloud** for each new follow-up.

The Live AI mode is not a low-latency, full-duplex call. It uses the stack already configured in IQ-AI and does not depend on a separate Gemini Live API credential.

## Setup

The backend needs the existing `GEMINI_API_KEY` in `backend/.env`. The key stays on the backend and is never sent to the browser. Configure these optional settings in the same file if needed:

```env
GEMINI_AUDIO_MODEL=gemini-2.5-flash-lite
GEMINI_REST_BASE_URL=https://generativelanguage.googleapis.com/v1beta
AI_REQUEST_TIMEOUT_SECONDS=45
AI_AUDIO_MAX_SIZE_MB=10
AI_AUDIO_MAX_SECONDS=120
```

Apply the database migration and restart the backend:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

The browser must support `getUserMedia` and `MediaRecorder` and the candidate must grant microphone permission. IQ-AI provides a typed-answer fallback when recording is unavailable or denied. Speech playback uses the browser's local `speechSynthesis`; voices and availability vary by browser and operating system.

## Audio, privacy, and costs

Recordings are limited in the UI and API to 10 MB and 120 seconds by default. The backend streams the uploaded file into memory for transcription and does not save it as a file or database blob. Only a transcript explicitly reviewed and confirmed by the user is saved as the interview answer. The recording is sent to Google's Gemini API for transcription; get the candidate's agreement before recording and follow the organization's retention and consent requirements.

Gemini transcription requires internet access and a valid Google AI Studio API key. As checked on 26 October 2026, Google's pricing page lists Gemini 2.5 Flash-Lite standard paid-tier rates of **$0.30 per 1 million audio input tokens**, **$0.10 per 1 million text input tokens**, and **$0.40 per 1 million output tokens**; standard free-tier rates are listed as $0 where the free tier is available and within quota. This is token-based billing, not a fixed per-minute fee. Prices, free-tier availability, and quotas can change, so check the [Gemini API pricing page](https://ai.google.dev/gemini-api/docs/pricing) before production use. Existing question generation, answer evaluation, and follow-up generation also use the configured Gemini text model and may consume quota or incur charges. Browser speech playback uses no additional IQ-AI API credential or external TTS request.

Audio is assessed only after transcription, using the existing answer-evaluation prompt. Accent, pitch, voice quality, and speech traits unrelated to the role are not sent as assessment criteria.
