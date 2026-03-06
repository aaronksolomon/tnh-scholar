import importlib.util
import sys
from argparse import Namespace
from pathlib import Path

from tnh_scholar.audio_processing.multilingual_models import TranscriptionProvider


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "transcribe_translate_srt.py"
    spec = importlib.util.spec_from_file_location("transcribe_translate_srt", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cli_build_config_sets_defaults(tmp_path: Path) -> None:
    module = _load_script_module()
    cli = module.SubtitleWorkflowCli()
    audio_file = tmp_path / "sample.mp3"
    args = Namespace(
        audio_file=audio_file,
        provider="whisper",
        source_language=None,
        target_language="en",
        transcription_model=None,
        translation_model=None,
        translation_pattern=None,
        metadata_file=None,
        chars_per_caption=42,
        use_speaker_blocks=False,
        source_srt_output=None,
        translated_srt_output=None,
        skip_translation=False,
        debug=False,
        use_repo_sample=False,
    )

    config = cli._build_config(args)

    assert config.provider is TranscriptionProvider.WHISPER
    assert config.source_srt_output == audio_file.resolve().with_suffix(".srt")
    assert config.translated_srt_output == audio_file.resolve().with_name("sample_en.srt")
    assert config.use_speaker_blocks is False


def test_cli_build_config_honors_skip_translation(tmp_path: Path) -> None:
    module = _load_script_module()
    cli = module.SubtitleWorkflowCli()
    audio_file = tmp_path / "sample.mp3"
    args = Namespace(
        audio_file=audio_file,
        provider="assemblyai",
        source_language="vi",
        target_language="en",
        transcription_model=None,
        translation_model=None,
        translation_pattern=None,
        metadata_file=None,
        chars_per_caption=42,
        use_speaker_blocks=False,
        source_srt_output=None,
        translated_srt_output=None,
        skip_translation=True,
        debug=False,
        use_repo_sample=False,
    )

    config = cli._build_config(args)

    assert config.provider is TranscriptionProvider.ASSEMBLYAI
    assert config.translated_srt_output is None


def test_cli_build_config_preserves_explicit_translated_output(tmp_path: Path) -> None:
    module = _load_script_module()
    cli = module.SubtitleWorkflowCli()
    audio_file = tmp_path / "sample.mp3"
    translated_output = tmp_path / "custom-output.srt"
    args = Namespace(
        audio_file=audio_file,
        provider="whisper",
        source_language=None,
        target_language="fr",
        transcription_model=None,
        translation_model=None,
        translation_pattern=None,
        metadata_file=None,
        chars_per_caption=42,
        use_speaker_blocks=False,
        source_srt_output=None,
        translated_srt_output=translated_output,
        skip_translation=False,
        debug=False,
        use_repo_sample=False,
    )

    config = cli._build_config(args)

    assert config.translated_srt_output == translated_output


def test_cli_build_config_resolves_metadata_file(tmp_path: Path) -> None:
    module = _load_script_module()
    cli = module.SubtitleWorkflowCli()
    audio_file = tmp_path / "sample.mp3"
    metadata_file = tmp_path / "meta.md"
    args = Namespace(
        audio_file=audio_file,
        provider="whisper",
        source_language=None,
        target_language="en",
        transcription_model=None,
        translation_model=None,
        translation_pattern=None,
        metadata_file=metadata_file,
        chars_per_caption=42,
        use_speaker_blocks=False,
        source_srt_output=None,
        translated_srt_output=None,
        skip_translation=False,
        debug=False,
        use_repo_sample=False,
    )

    config = cli._build_config(args)

    assert config.metadata_file == metadata_file.resolve()


def test_cli_build_config_uses_target_language_suffix(tmp_path: Path) -> None:
    module = _load_script_module()
    cli = module.SubtitleWorkflowCli()
    audio_file = tmp_path / "sample.mp3"
    args = Namespace(
        audio_file=audio_file,
        provider="whisper",
        source_language=None,
        target_language="fr",
        transcription_model=None,
        translation_model=None,
        translation_pattern=None,
        metadata_file=None,
        chars_per_caption=42,
        use_speaker_blocks=True,
        source_srt_output=None,
        translated_srt_output=None,
        skip_translation=False,
        debug=False,
        use_repo_sample=False,
    )

    config = cli._build_config(args)

    assert config.source_srt_output == audio_file.resolve().with_name("sample_blocks.srt")
    assert config.translated_srt_output == audio_file.resolve().with_name("sample_blocks_fr.srt")
    assert config.use_speaker_blocks is True


def test_cli_build_config_uses_repo_sample_when_requested() -> None:
    module = _load_script_module()
    cli = module.SubtitleWorkflowCli()
    args = Namespace(
        audio_file=None,
        provider="whisper",
        source_language=None,
        target_language="en",
        transcription_model=None,
        translation_model=None,
        translation_pattern=None,
        metadata_file=None,
        chars_per_caption=42,
        use_speaker_blocks=False,
        source_srt_output=None,
        translated_srt_output=None,
        skip_translation=False,
        debug=False,
        use_repo_sample=True,
    )

    config = cli._build_config(args)

    assert config.audio_file == (Path(module.__file__).resolve().parents[1] / "tmp" / "happy-farm-day-1.mp3")
