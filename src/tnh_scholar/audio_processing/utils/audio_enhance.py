"""
Module review and recommendations:

Big Picture Approach:

Modular, Configurable, and Extensible: Your use of Pydantic models for settings and configs is excellent. 
It makes the pipeline flexible and easy to tune for different ASR or enhancement needs.
Tooling: Leveraging SoX and FFmpeg is a pragmatic choice for robust, high-quality audio processing.
Pipeline Structure: The AudioEnhancer class is well-structured, 
with clear separation of concerns for each processing step (remix, rate, gain, EQ, compand, etc.).
Notebook Integration: The play_audio method and use of IPython display is great for interactive, 
iterative work.

Details & Points You Might Be Missing:

Error Handling & Logging:

You print errors but could benefit from more structured logging (e.g., using Python’s logging module).
Consider more granular exception handling, especially for subprocess calls.
Testing & Validation:

No unit tests or validation of output audio quality/format are present. Consider adding automated tests 
(even if just for file existence, format, and basic properties).
You could add a method to compare pre/post enhancement SNR, loudness, or other metrics.
Documentation & Examples:

While docstrings are good, a usage example (in code or markdown) would help new users.
Consider a README or notebook cell that demonstrates a full workflow.
Performance:

For large-scale or batch processing, consider parallelization or async processing.
Temporary files (e.g., intermediate FLACs) could be managed/cleaned up more robustly.
Extensibility:

The pipeline is modular, but adding a “custom steps” hook (e.g., user-defined SoX/FFmpeg args) 
would make it even more flexible.
You might want to support other codecs or output formats for downstream ASR models.
Feature Gaps:

The extract_sample method is a TODO. Implementing this would be useful for quick QA or dataset creation.
Consider adding Voice Activity Detection (VAD) or silence trimming as optional steps.
You could add a “dry run” mode to print the SoX/FFmpeg commands without executing, for debugging.
ASR-Specific Enhancements:

You might want to add preset configs for different ASR models (e.g., Whisper, Wav2Vec2, etc.), 
as they may have different optimal preprocessing.
Consider integrating with open-source ASR evaluation tools to close the loop on enhancement effectiveness.
General Strategic Recommendations:

Automate QA: Add methods to check output audio quality, duration, and format, and optionally compare to input.
Batch Processing: Add a method to process a directory or list of files.
Config Export/Import: Allow saving/loading configs as JSON/YAML for reproducibility.
CLI/Script Interface: Consider a command-line interface for use outside notebooks.
Unit Tests: Add basic tests for each method, especially for error cases.
Summary Table:

 | Modularity | Good | Add custom step hooks | 
 | Configurability | Excellent | Presets for more ASR models | 
 | Error Handling | Basic | Use logging, more granular exceptions | 
 | Testing | Missing | Add unit tests, output validation | 
 | Documentation | Good | Add usage examples, README | 
 | Extensibility | Good | Support more codecs, batch processing | 
 | ASR Optimization | Good start | Add VAD, silence trim, model-specific configs |
 
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from IPython.display import Audio, display
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)

class CompressionSettings(BaseSettings):
    """Compression settings for audio enhancement routines.
    
    Attributes:
        minimal: List of compand arguments for minimal compression.
        light: List of compand arguments for light compression.
        moderate: List of compand arguments for moderate compression.
        aggressive: List of compand arguments for aggressive compression.
        whisper_optimized: List of compand arguments for Whisper-optimized compression.
        whisper_aggressive: List of compand arguments for aggressive Whisper compression.
        primary_speech_only: List of compand arguments for primary speech only.
    """
    minimal: list[str] = ["0.1,0.3", "3:-50,-40,-30,-20", "-3", "-80", "0.2"]
    light: list[str] = ["0.05,0.2", "6:-60,-50,-40,-30,-20,-10", "-3", "-85", "0.1"]
    moderate: list[str] = ["0.03,0.15", "6:-65,-50,-40,-30,-20,-10", "-4", "-85", "0.1"]
    aggressive: list[str] = ["0.02,0.1", "8:-70,-55,-45,-35,-25,-15", "-5", "-90", "0.05"]
    whisper_optimized: list[str] = ["0.005,0.06", "12:-75,-65,-55,-45,-35,-25,-15,-8", "-8", "-95", "0.03"]
    whisper_aggressive: list[str] = ["0.005,0.06", "12:-75,-45,-55,-30,-35,-18,-15,-8", "-8", "-95", "0.03"]
    primary_speech_only: list[str] = ["0.005,0.06", "12:-60,-45,-55,-30,-35,-18,-15,-8", "-8", "-60", "0.03"]


class EQSettings(BaseSettings):
    highpass_freq: int = 175
    lowpass_freq: int = 15000
    eq_bands: list[tuple[int, float, int]] = [
        (100, 0.9, -20),
        (1500, 1, 4),
        (4000, 0.6, 15),
        (10000, 1, -10)
    ]
    contrast: int = 75
    bass: tuple[int, int] = (-5, 200)
    treble: tuple[int, int] = (3, 3000)

class GateSettings(BaseSettings):
    gate_params: list[str] = ["0.1", "0.05", "-inf", "0.1", "-90", "0.1"]

class NormalizationSettings(BaseSettings):
    norm_level: int = -1

class RemixSettings(BaseSettings):
    remix_channels: str = "1,2"

class RateSettings(BaseSettings):
    rate_args: list[str] = ["-v"]

class EnhancementConfig(BaseModel):
    codec: str = 'flac'
    sample_rate: int = 48000
    channels: int = 2
    compression_level: str = 'aggressive'
    force_mono: bool = False
    target_rate: Optional[int] = None
    eq: EQSettings = EQSettings()
    gate: GateSettings = GateSettings()
    norm: NormalizationSettings = NormalizationSettings()
    remix: RemixSettings = RemixSettings()
    rate: RateSettings = RateSettings()
    include_gate: bool = True
    include_eq: bool = True

class AudioEnhancer:
    def __init__(
        self, 
        config: EnhancementConfig = EnhancementConfig(), 
        compression_settings: CompressionSettings = CompressionSettings()
        ):
        """Initialize with enhancement configuration and compression settings."""
        
        # Check required tools
        for tool in ["sox", "ffmpeg"]:
            try:
                subprocess.run(["which", tool], capture_output=True, text=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                raise RuntimeError(f"{tool} is not installed. Please install it first.") from e
            
        self.config = config
        self.compression_settings = compression_settings

    def enhance(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Apply enhancement routines (compression, EQ, gating, etc.) in a modular fashion.
        Converts input to FLAC working format for Whisper compatibility.
        """
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_enhanced.flac"

        # Step 1: Convert to FLAC if needed
        working_flac = input_path.with_suffix(".flac")
        if not working_flac.exists():
            self._convert_to_flac(input_path, working_flac)

        # Step 2: Build SoX command modularly using helper methods
        sox_cmd = ["sox", str(working_flac), str(output_path)]
        sox_cmd.extend(self._set_remix())
        sox_cmd.extend(self._set_rate())
        sox_cmd.extend(self._set_gain())
        sox_cmd.extend(self._set_freq())
        sox_cmd.extend(self._set_eq())
        sox_cmd.extend(self._set_compand())
        sox_cmd.extend(self._set_gate())
        sox_cmd.extend(self._set_contrast_bass_treble())
        sox_cmd.extend(self._set_norm())

        result = subprocess.run(sox_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.info(f"SoX Error: {result.stderr}")
            raise RuntimeError(f"SoX processing failed: {result.stderr}")
        return output_path

    def _set_remix(self) -> list[str]:
        """Set remix channels if force_mono is enabled."""
        if self.config.force_mono:
            return ["remix", self.config.remix.remix_channels]
        return []

    def _set_rate(self) -> list[str]:
        """Set sample rate if target_rate is specified."""
        if self.config.target_rate:
            return ["rate", *self.config.rate.rate_args, str(self.config.target_rate)]
        return []

    def _set_gain(self) -> list[str]:
        """Set gain normalization."""
        return ["gain", "-n", str(self.config.norm.norm_level)]

    def _set_freq(self) -> list[str]:
        """Set highpass and lowpass frequencies."""
        return [
            "highpass", "-1", str(self.config.eq.highpass_freq),
            "lowpass", "-1", str(self.config.eq.lowpass_freq)
        ]

    def _set_eq(self) -> list[str]:
        """Set equalizer bands."""
        eq_cmd = []
        for freq, width, gain in self.config.eq.eq_bands:
            eq_cmd.extend(["equalizer", str(freq), str(width), str(gain)])
        return eq_cmd

    def _set_compand(self) -> list[str]:
        """Set compression arguments."""
        comp_args: list[str] = getattr(
            self.compression_settings,
            self.config.compression_level,
            self.compression_settings.whisper_optimized
        )
        return ["compand", *comp_args, ":"]

    def _set_gate(self) -> list[str]:
        """Set gate if enabled."""
        if self.config.include_gate:
            return ["gate", *self.config.gate.gate_params]
        return []

    def _set_contrast_bass_treble(self) -> list[str]:
        """Set contrast, bass, and treble if EQ is enabled."""
        if self.config.include_eq:
            return [
                "contrast", str(self.config.eq.contrast),
                "bass", str(self.config.eq.bass[0]), str(self.config.eq.bass[1]),
                "treble", f"+{self.config.eq.treble[0]}", str(self.config.eq.treble[1])
            ]
        return []

    def _set_norm(self) -> list[str]:
        """Set normalization."""
        return ["norm", str(self.config.norm.norm_level)]

    def _convert_to_flac(self, input_path: Path, output_path: Path) -> None:
        """
        Convert input audio to FLAC format using ffmpeg, preserving maximal fidelity.
        """
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-map", "0:a:0",
            "-c:a", "flac",
            "-compression_level", "8",
            str(output_path),
            "-y"
        ]
        result = subprocess.run(cmd, check=True, capture_output=True)
        if result.returncode != 0:
            print(f"FFmpeg Error: {result.stderr.decode()}")
            raise RuntimeError(f"FFmpeg conversion failed: {result.stderr.decode()}")

    def extract_sample(
        self,
        input_path: Path,
        start: float,
        duration: float,
        output_path: Optional[Path] = None,
        output_format: str = "flac",
        codec: Optional[str] = None,
        compression_level: int = 8,
    ) -> Path:
        """
        Extract a sample segment from the audio file.

        Parameters
        ----------
        input_path : Path
            Path to the input audio file.
        start : float
            Start time in seconds.
        duration : float
            Duration in seconds.
        output_path : Path, optional
            Output file path. If None, auto-generated from input.
        output_format : str, default="flac"
            Output audio format/extension.
        codec : str, optional
            Audio codec to use (default: "flac" if output_format is "flac", else None).
        compression_level : int, default=8
            Compression level for supported codecs.

        Returns
        -------
        Path
            Path to the extracted audio sample.
        """
        input_path = Path(input_path)
        output_path = self._sample_output_path(input_path, output_path, start, duration, output_format)
        
        if codec is None:
            codec = "flac" if output_format == "flac" else None

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-t", str(duration),
            "-i", str(input_path),
        ]
        if codec:
            cmd += ["-c:a", codec]
        if codec == "flac":
            cmd += ["-compression_level", str(compression_level)]
        cmd.append(str(output_path))

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg sample extraction failed: {result.stderr}")
            raise RuntimeError(f"Sample extraction failed: {result.stderr}")
        return output_path

    def _sample_output_path(self, input_path, output_path, start, duration, output_format) -> Path:
        if output_path is None:
            return ( 
                    input_path.parent / 
                    f"{input_path.stem}_sample_{int(start)}s_{int(duration)}s.{output_format}"
            )
        return Path(output_path)
            
    def play_audio(self, file_path: Path):
        """Play audio in notebook for quality assessment."""
        display(Audio(str(file_path)))

    def get_audio_info(self, file_path: Path):
        """Get detailed audio information using ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-select_streams", "a:0", str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return self._display_stream_info(result, file_path)
        logger.error(f"FFprobe error: {result.stderr}")
        raise RuntimeError("Failed to retrieve audio info.")

    def _display_stream_info(self, result: subprocess.CompletedProcess, file_path: Path) -> dict:
        data = json.loads(result.stdout)
        stream = data["streams"][0]

        logger.info(f"File: {file_path}")
        logger.info(f"Codec: {stream.get('codec_name', 'Unknown')}")
        logger.info(f"Sample Rate: {stream.get('sample_rate', 'Unknown')} Hz")
        logger.info(f"Channels: {stream.get('channels', 'Unknown')}")
        logger.info(f"Bit Rate: {stream.get('bit_rate', 'Unknown')} bps")
        logger.info(f"Duration: {stream.get('duration', 'Unknown')} seconds")
        logger.info(f"Sample Format: {stream.get('sample_fmt', 'Unknown')}")

        return stream
            
            
            
def compress_wav_to_mp4_vbr(
    input_wav: str | Path, output_path: Optional[str | Path] = None, quality: int = 8
    ) -> Path:
    """
    Compress WAV to M4A (AAC VBR) using ffmpeg.
    
    Parameters:
    -----------
    input_wav : str or Path
        Path to the input .wav file
    output_path : str or Path, optional
        Output .mp4 file path. If None, auto-generated from input
    quality : int, default=8
        VBR quality level: 1 = good (~96kbps), 2 = very good (~128kbps), 3+ = higher bitrate
    
    Returns:
    --------
    Path
        Path to the compressed .m4a file
    """
    input_wav = Path(input_wav)
    if output_path is None:
        output_path = input_wav.with_suffix(".mp4")
    else:
        output_path = Path(output_path)

    cmd = [
        "ffmpeg", "-y", "-i", str(input_wav),
        "-c:a", "aac",
        "-q:a", str(quality),
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error("Error compressing audio:")
        logger.error(result.stderr)
        raise RuntimeError("FFmpeg compression failed.")
    
    print(f"Compressed audio saved to: {output_path}")
    return output_path



def get_sox_info(file_path):
    """Get audio info using SoX"""
    result = subprocess.run(["sox", "--info", str(file_path)], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        logger.error(result.stdout)
    else:
        logger.error(f"Error: {result.stderr}")
