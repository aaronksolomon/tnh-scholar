from tnh_scholar.audio_processing.transcription.assemblyai_service import AAITranscriptionService


def test_normalize_options_disables_language_detection_when_language_set() -> None:
    service = AAITranscriptionService.__new__(AAITranscriptionService)
    service._get_transcription_config_keys = lambda: {"language_code", "language_detection"}

    normalized = service._normalize_options({"language": "en", "language_detection": True})

    assert normalized["language_code"] == "en"
    assert normalized["language_detection"] is False
