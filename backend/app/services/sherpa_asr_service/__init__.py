"""Sherpa ASR (Automatic Speech Recognition) service."""
from __future__ import annotations
import os
import subprocess
import tempfile
import wave as _wave_mod

try:
    import numpy as np
except Exception:
    np = None

try:
    import sherpa_onnx
except Exception:
    sherpa_onnx = None

try:
    import httpx
except Exception:
    httpx = None


def _normalize_mode(raw):
    if raw is None:
        return "off"
    s = str(raw).strip()
    if not s:
        return "off"
    s_lower = s.lower()
    if s_lower in ("local", "remote"):
        return s_lower
    return "off"


def _get_setting(settings_obj, name, default=None):
    try:
        return getattr(settings_obj, name, default)
    except Exception:
        return default


def sherpa_is_ready(s):
    if not _get_setting(s, "sherpa_asr_enabled", False):
        return False
    mode = _normalize_mode(_get_setting(s, "sherpa_asr_mode", "off"))
    if mode == "off":
        return False
    if mode == "remote":
        url = _get_setting(s, "sherpa_asr_remote_url", "")
        return bool(url.strip())
    if mode == "local":
        if np is None or sherpa_onnx is None:
            return False
        tokens = _get_setting(s, "sherpa_onnx_tokens", "")
        wenet_model = _get_setting(s, "sherpa_onnx_wenet_ctc_model", "")
        whisper_enc = _get_setting(s, "sherpa_onnx_whisper_encoder", "")
        whisper_dec = _get_setting(s, "sherpa_onnx_whisper_decoder", "")
        has_wenet = bool(tokens) and bool(wenet_model)
        has_whisper = bool(tokens) and bool(whisper_enc) and bool(whisper_dec)
        if not has_wenet and not has_whisper:
            return False
        for p in [tokens, wenet_model, whisper_enc, whisper_dec]:
            if p and not os.path.exists(p):
                return False
        return True
    return False


def _ffmpeg_available():
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _convert_with_ffmpeg_to_wav_16k_mono(data, suffix=".wav"):
    if not _ffmpeg_available():
        raise RuntimeError("ffmpeg_not_available")
    fd_in, path_in = tempfile.mkstemp(suffix=suffix)
    os.close(fd_in)
    fd_out, path_out = tempfile.mkstemp(suffix=".wav")
    os.close(fd_out)
    try:
        with open(path_in, "wb") as f:
            f.write(data)
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", path_in, "-ar", "16000", "-ac", "1", "-f", "wav", path_out],
            capture_output=True, timeout=60,
        )
        if r.returncode != 0:
            raise RuntimeError("ffmpeg_convert_failed")
        with open(path_out, "rb") as f:
            result = f.read()
        return result
    finally:
        for p in [path_in, path_out]:
            try:
                os.remove(p)
            except OSError:
                pass


def wave_open(file_obj, mode="r"):
    return _wave_mod.open(file_obj, mode)


def _read_wav_bytes(data):
    if np is None:
        raise RuntimeError("numpy_not_installed")
    bio = __import__("io").BytesIO(data)
    wf = wave_open(bio, "r")
    try:
        sr = wf.getframerate()
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        if sw != 2:
            raise ValueError(f"unsupported_wav_sample_width:{sw}")
        raw = wf.readframes(wf.getnframes())
    finally:
        try:
            wf.close()
        except Exception:
            pass
    samples = np.frombuffer(raw, dtype=np.int16)
    if nch > 1:
        samples = samples[::nch]
    return samples.astype(np.float32) / 32768.0, sr


def _audio_to_float32_16k(data, filename=""):
    try:
        samples, sr = _read_wav_bytes(data)
    except (ValueError, RuntimeError):
        if not _ffmpeg_available():
            raise
        wav = _convert_with_ffmpeg_to_wav_16k_mono(data, suffix=filename.rsplit(".", 1)[-1] if "." in filename else ".bin")
        samples, sr = _read_wav_bytes(wav)
    if sr != 16000:
        if not _ffmpeg_available():
            raise RuntimeError("ffmpeg_not_available_for_resampling")
        wav = _convert_with_ffmpeg_to_wav_16k_mono(data, suffix=filename.rsplit(".", 1)[-1] if "." in filename else ".bin")
        samples, sr = _read_wav_bytes(wav)
    return samples, sr


class _SherpaLocalSingleton:
    _recognizer = None
    _fingerprint = None

    @classmethod
    def get_recognizer(cls, settings):
        tokens = _get_setting(settings, "sherpa_onnx_tokens", "") or ""
        wenet_model = _get_setting(settings, "sherpa_onnx_wenet_ctc_model", "") or ""
        whisper_enc = _get_setting(settings, "sherpa_onnx_whisper_encoder", "") or ""
        whisper_dec = _get_setting(settings, "sherpa_onnx_whisper_decoder", "") or ""
        if wenet_model:
            fp = ("wenet_ctc", tokens, wenet_model)
        elif whisper_enc and whisper_dec:
            fp = ("whisper", tokens, whisper_enc, whisper_dec)
        else:
            fp = ("none",)
        if cls._recognizer is not None and cls._fingerprint == fp:
            return cls._recognizer
        cls._recognizer = cls._build_recognizer(settings)
        cls._fingerprint = fp
        return cls._recognizer

    @classmethod
    def _build_recognizer(cls, s):
        if sherpa_onnx is None:
            raise RuntimeError("sherpa_onnx_not_installed")
        tokens = _get_setting(s, "sherpa_onnx_tokens", "")
        wenet_model = _get_setting(s, "sherpa_onnx_wenet_ctc_model", "")
        whisper_enc = _get_setting(s, "sherpa_onnx_whisper_encoder", "")
        whisper_dec = _get_setting(s, "sherpa_onnx_whisper_decoder", "")
        num_threads = _get_setting(s, "sherpa_onnx_num_threads", 4)
        decode_method = _get_setting(s, "sherpa_onnx_decoding_method", "greedy_search")
        sample_rate = _get_setting(s, "sherpa_onnx_sample_rate", 16000)
        feature_dim = _get_setting(s, "sherpa_onnx_feature_dim", 80)
        if wenet_model and os.path.exists(wenet_model):
            recognizer = sherpa_onnx.OfflineRecognizer.from_wenet_ctc(
                wenet=wenet_model,
                tokens=tokens,
                num_threads=num_threads,
                decoding_method=decode_method,
                sample_rate=sample_rate,
                feature_dim=feature_dim,
            )
        elif whisper_enc and whisper_dec and os.path.exists(whisper_enc) and os.path.exists(whisper_dec):
            recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=whisper_enc,
                decoder=whisper_dec,
                tokens=tokens,
                num_threads=num_threads,
                decoding_method=decode_method,
                sample_rate=sample_rate,
                language=_get_setting(s, "sherpa_onnx_whisper_language", "zh"),
                task=_get_setting(s, "sherpa_onnx_whisper_task", "transcribe"),
                tail_paddings=_get_setting(s, "sherpa_onnx_whisper_tail_paddings", 10),
            )
        else:
            raise RuntimeError("sherpa_model_not_configured")
        return recognizer


def _transcribe_local_sync(content, filename, settings):
    if np is None:
        raise RuntimeError("numpy_not_installed")
    samples, sr = _audio_to_float32_16k(content, filename)
    recognizer = _SherpaLocalSingleton.get_recognizer(settings)
    stream = recognizer.create_stream()
    stream.accept_waveform(sr, samples)
    recognizer.decode_streams([stream])
    result = stream.result
    return result.text


async def sherpa_transcribe(content=b"", filename="", settings=None, segment_index=None, is_final=False):
    if settings is None:
        from app.core.config import settings as _s
        settings = _s
    if not _get_setting(settings, "sherpa_asr_enabled", False):
        raise RuntimeError("sherpa_disabled")
    mode = _normalize_mode(_get_setting(settings, "sherpa_asr_mode", "off"))
    if mode == "off":
        raise RuntimeError("sherpa_disabled")
    if mode == "remote":
        url = _get_setting(settings, "sherpa_asr_remote_url", "")
        if not url.strip():
            raise RuntimeError("sherpa_remote_url_missing")
        if httpx is None:
            raise RuntimeError("httpx_not_installed")
        payload = {"audio": content.hex() if isinstance(content, bytes) else ""}
        if segment_index is not None:
            payload["segment_index"] = str(segment_index)
        if is_final:
            payload["is_final"] = "true"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("text", ""), "sherpa_remote", url
    text = _transcribe_local_sync(content, filename, settings)
    return text, "sherpa_local", None
