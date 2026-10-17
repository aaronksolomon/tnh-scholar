---
title: "Sr. Dang Nghiem Transcription Workflow"
description: "Local operating recipe for recurring English YouTube talk transcription with AssemblyAI."
owner: ""
author: "Codex"
status: current
created: "2026-10-11"
updated: "2026-10-13"
---
# Sr. Dang Nghiem Transcription Workflow

Use this recipe whenever the user supplies YouTube talks by Sr. Dang Nghiem
and asks for transcription. Run from the TNH Scholar repository root.
This file is an operating recipe, not a scheduled task or conductor workflow.

## Fixed defaults

- Tool: `poetry run audio-transcribe` (uses the current repository code).
- Provider: `--service assemblyai`.
- Language: `--language en` for every talk.
- Deliverable: UTF-8 plain-text `.txt`, containing the transcript without an
  added summary or translation.
- Output folder: `~/Desktop/Sr Dang Nghiem`.
- Top-level deliverables: `title_MM_DD_YYYY_raw.txt` for whitespace-only
  paragraph blocks and `title_MM_DD_YYYY_corrected.txt` for reviewed Sol output.
- Keep the same title/date basename for both outputs. Role suffixes do not
  count toward the 20-character title limit. Older transcripts go in `archive/`.
- Keep the inventory in `processing-records/transcription-inventory.txt`.
- Process each URL separately and sequentially.
- Deduplicate supplied URLs by YouTube video ID before starting; short and
  full URLs for the same video count as one talk.
- Keep every intermediate in retained run subfolders, including downloaded
  audio. Use `--keep_artifacts` with a staged output under `transcription-runs/`.

## Preparation

1. Confirm `poetry run audio-transcribe --help` and `ffmpeg -version` work.
2. Ensure `ASSEMBLYAI_API_KEY` is available through the environment or the
   repository's ignored `.env`. Never print or copy the key into this file.
   This pipeline uses AssemblyAI's cloud API and skips separate Pyannote
   processing; OpenAI and Pyannote credentials are unnecessary.
3. Create the output folder if missing. When executing through an agent,
   request filesystem access only if the runtime requires it for Desktop
   writes. Do not substitute a different final destination silently.

## Filename policy

Read the actual YouTube title and description before naming the transcript.
Fetch video ID, title, upload date, and description without downloading audio:

```bash
poetry run yt-dlp --no-playlist --skip-download \
  --print '%(id)s' --print '%(title)s' \
  --print '%(upload_date)s' --print '%(description)s' "YOUTUBE_URL"
```

Derive a filename stem from the title:

1. Remove trailing speaker, venue, and date labels when clearly separated
   from the talk title (for example, `Title | Sister Dang Nghiem | Date`).
2. Convert to lowercase ASCII; replace punctuation and whitespace with `_`,
   collapse repeated underscores, and strip leading/trailing underscores.
3. Keep stems of 20 characters or fewer. For longer stems, shorten to a
   meaningful title prefix of at most 20 characters, preferably at a word
   boundary. Only the title stem counts toward this limit.
4. Append the chosen date as `_MM_DD_YYYY`, then `.txt`. If the title stem
   is empty, use `talk`. See the date policy below.
5. If the dated destination already exists, do not overwrite it: insert
   `_VIDEO_ID` before the date tag. The video ID, date, and extension are
   exempt from the 20-character title limit.
6. If the suffixed destination also exists, report the existing file and
   skip that talk unless the user explicitly requests retranscription.

Examples: `Flowers in the Dark`, March 22, 2024 →
`flowers_in_the_dark_03_22_2024.txt`; `Beginning Anew with Children & Teens`,
June 23, 2023 → `beginning_anew_with_06_23_2023.txt`.

## Date policy

Use the date the talk was given, with this evidence order:

1. A talk date explicitly supplied by the user.
2. A recording/talk date explicitly stated in the YouTube title or
   description, transcript introduction, or matching official event page.
3. YouTube `upload_date` when no talk date is available. Parse its
   `YYYYMMDD` value and format it as `MM_DD_YYYY`.

Validate the date as a real calendar date. A retreat date range, mention of
an unrelated event, file creation/modification timestamp, or transcription
run date is not a talk date. Do not infer a specific day from those values.
If reliable sources conflict, resolve the conflict before naming the file.
If both talk and upload dates are unavailable, leave the existing file
unchanged and report that its date is unresolved; never invent a date tag.
In the completion report, identify whether each date came from talk evidence
or the upload-date fallback, and give the source. Keep that information in a
local inventory when consolidating older transcripts.

## Transcribe each talk

Choose the filename using the policy above, then run the following recipe
with the supplied URL and selected filename. Quote paths and URLs, including
those containing spaces or `&`.

```bash
talk_url="YOUTUBE_URL"
talk_filename="flowers_in_the_dark_03_22_2024.txt"
talk_output_dir="$HOME/Desktop/Sr Dang Nghiem"
mkdir -p "$talk_output_dir"
mkdir -p "$talk_output_dir/transcription-runs"
talk_stage_dir=$(mktemp -d "$talk_output_dir/transcription-runs/run-XXXXXX")

if poetry run audio-transcribe \
  --yt_url "$talk_url" \
  --service assemblyai \
  --language en --keep_artifacts \
  --output "$talk_stage_dir/transcript.txt"; then
  if test -s "$talk_stage_dir/transcript.txt"; then
    cp -n "$talk_stage_dir/transcript.txt" "$talk_stage_dir/$talk_filename"
  else
    echo "No transcript text was produced; inspect the CLI output."
  fi
fi
```

Keep the unformatted transcript in the processing run folder, named with its
title/date basename. It is an intermediate, not a top-level deliverable.
`cp -n` protects existing destinations and keeps the intermediate transcript.
Verify the named intermediate is byte-identical to the staged transcript;
report a collision if it differs. Keep the run directory, downloaded audio,
and transcripts after success or failure. Do not remove intermediates.

Do not use `--yt_url_csv`: the current CLI selects only the first URL.
Do not pass Whisper-specific model or prompt options. If YouTube downloading
fails, report the diagnostic and resolve the download problem before retrying
transcription. Do not switch providers automatically.

## YouTube download fallback

The direct `--yt_url` route requires the latest yt-dlp and can fail with
HTTP 403 even when metadata retrieval succeeds. In the October 11, 2026
live test, a separate download with explicit JavaScript support succeeded.
Use this two-step fallback before retrying transcription; keep AssemblyAI
and English as the transcription settings.

Use a working Node runtime and yt-dlp's `ejs:github` remote component support.
The following installs current yt-dlp into a temporary directory, preserving
the repository environment and dependency lock:

```bash
talk_ytdlp_runtime=$(mktemp -d)
poetry run python -m pip install --target "$talk_ytdlp_runtime" yt-dlp
PYTHONPATH="$talk_ytdlp_runtime" poetry run python -m yt_dlp --no-playlist \
  --js-runtimes node --remote-components ejs:github \
  -f bestaudio -x --audio-format mp3 \
  -o "$talk_stage_dir/audio.%(ext)s" "$talk_url"

poetry run audio-transcribe \
  --file "$talk_stage_dir/audio.mp3" \
  --service assemblyai --language en --keep_artifacts \
  --output "$talk_stage_dir/transcript.txt"
```

Wait for download and conversion to finish before transcribing. Validate and
publish the staged transcript using the same filename/date policy and
overwrite protection. Do not submit again if an AssemblyAI job is already
running. If the repo's pinned yt-dlp is outdated, a temporary installation
outside the repo can supply the downloader via `PYTHONPATH`; document that
runtime choice and do not silently modify dependency files.

## Completion

Check the beginning and end of each transcript for obvious truncation or
provider error messages. Report the source title, final `.txt` path, and any
failed or skipped talks. Preserve the original wording; proofreading is a
separate task. Never commit transcripts, downloaded media, or credentials.

## Format paragraph blocks with tnh-gen

Use two stages in order: (1) whitespace-only paragraph formatting, then
(2) grammar correction of each paragraph independently. Keep every intermediate.
Stage 2 takes the saved Stage 1 output, never the unformatted raw transcript.

The current `tnh-gen run` CLI has no paragraph/chunk-splitting flag. The legacy
`SectionProcessor.process_paragraphs` processes individual nonempty lines
(`src/tnh_scholar/ai_text_processing/ai_text_processing.py:378`), so it is not
used here. The workflow runner splits on blank lines, preserves wrapped lines
inside paragraphs, and executes one `tnh-gen` call per paragraph.

### Stage 1: verbatim paragraph breaks

After transcription, create a top-level `title_MM_DD_YYYY_raw.txt` containing
verbatim paragraph blocks. Preserve the unformatted transcript in its
processing folder. This stage uses OpenAI through
tnh-gen and requires `OPENAI_API_KEY`, in addition to the AssemblyAI key used
by the transcription stage.

Existing prompts `default_punctuate` and `punctuate_dharma_talk` add paragraph
breaks and edit punctuation/typographic errors. The older `omega_paragraphs.txt`
records a `default_punctuate` pass through the legacy `SectionProcessor`, not
a historical tnh-gen CLI invocation. The user guide documents the modern
equivalent: `tnh-gen run --prompt default_punctuate --input-file ...
--var source_language=English --output-file ...`.

For strictly verbatim formatting, use the dedicated `sr-d-paragraph-blocks` prompt from
`workflows/prompts/`. It permits whitespace changes only: original words,
punctuation, repetitions, and ordering must remain intact. Use its default
model `gpt-5-mini`, minimal reasoning, and a 16,000-token output allowance for
the tested talks. Longer talks may need separate contiguous sections;
never publish a truncated or altered result.

Run from the repository root, with a raw transcript selected explicitly:

```bash
talk_input="$HOME/Desktop/Sr Dang Nghiem/transcription-runs/imported-originals/love_in_training_09_10_2026.txt"
talk_paragraph_dir="$HOME/Desktop/Sr Dang Nghiem"
talk_basename=$(basename "$talk_input" .txt)
talk_paragraph_filename="${talk_basename}_raw.txt"
mkdir -p "$HOME/Desktop/Sr Dang Nghiem/paragraph-runs"
talk_paragraph_stage=$(mktemp -d "$HOME/Desktop/Sr Dang Nghiem/paragraph-runs/run-XXXXXX")
cp "$talk_input" "$talk_paragraph_stage/source.txt"
cp workflows/prompts/sr-d-paragraph-blocks.md "$talk_paragraph_stage/prompt.md"

poetry run tnh-gen --api --prompt-dir ./workflows/prompts run \
  --prompt sr-d-paragraph-blocks \
  --input-file "$talk_input" \
  --reasoning minimal --max-tokens 16000 \
  --no-provenance \
  --output-file "$talk_paragraph_stage/paragraphs.txt" \
  > "$talk_paragraph_stage/response.json" 2> "$talk_paragraph_stage/stderr.log"
```

Only after the CLI succeeds, check content preservation and paragraph breaks:

```bash
if poetry run python - "$talk_input" "$talk_paragraph_stage/paragraphs.txt" <<'PY'
from pathlib import Path
import re
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
result = Path(sys.argv[2]).read_text(encoding="utf-8")
if not result.strip():
    raise SystemExit("Empty formatted transcript; publication stopped.")
if source.split() != result.split():
    raise SystemExit("Transcript wording or punctuation changed; publication stopped.")
if len(re.split(r"\n\s*\n", result.strip())) < 2:
    raise SystemExit("No paragraph blocks produced; publication stopped.")
print("Verified: only whitespace changed, with paragraph blocks added.")
PY
then
  mkdir -p "$talk_paragraph_dir"
  cp -n "$talk_paragraph_stage/paragraphs.txt" \
    "$talk_paragraph_dir/$talk_paragraph_filename"
fi
```

Check that the destination matches the staged output. Preserve the entire
run folder, including successful intermediates, API response, and prompt snapshot.
Report failures or differing existing output as a collision. Use `--no-provenance` to keep these
deliverables plain text; record prompt key, model, source path, and validation
result in `processing-records/transcription-inventory.txt`. Process unformatted files only, not previous
paragraph outputs. There is no punctuation-cleanup or summarization step here.

Validated October 12, 2026: `love_in_training_09_10_2026.txt` produced 49
paragraph blocks, and `authentic_insight_on_10_04_2026.txt` produced 26. Both
passed exact token equality checks against their raw transcripts, including
punctuation, and were initially published in the `paragraphs/` subfolder.
They now reside at the top level with `_raw` suffixes.

### Stage 2: paragraph-by-paragraph grammar correction

Use `sr-d-paragraph-grammar` from `workflows/prompts/`. It corrects grammar and
punctuation with minimal edits while preserving meaning, details, quotations,
and repetitions. It returns one paragraph for each input paragraph. Exact word
identity is required only in Stage 1; Stage 2 edits must be compared and reviewed.

Run from the repository root, choosing a new retained run directory each time:

```bash
poetry run python workflows/run_paragraph_grammar.py \
  "$HOME/Desktop/Sr Dang Nghiem/love_in_training_09_10_2026_raw.txt" \
  "$HOME/Desktop/Sr Dang Nghiem/grammar-runs/love_in_training_09_10_2026-sol-2026-10-13" \
  --workers 3 --requests-per-minute 12 --tokens-per-minute 60000
```

The runner uses `gpt-5.6-sol`, low reasoning, and an 8,192-token allowance
per paragraph. Stage 1 remains on the tested `gpt-5-mini` model. The model and
reasoning can be overridden using `--model` and `--reasoning`. Up to three independent calls run concurrently; combined output
always follows source paragraph order. Worker threads share paced request
starts (`--requests-per-minute`, default 12) and a rolling token reservation
budget (`--tokens-per-minute`, default 60000). Reservations include the encoded
input/prompt plus the entire output allowance, so they are conservative.
These are provisional local caps, not discovered account limits. Set them
below the project's actual model limits with headroom for other traffic.

`tnh-gen` currently retries 429/server failures, but its shared rate-limiter
module is a placeholder. This workflow limiter governs initial CLI submissions
within one runner process; provider/SDK retries and other runner processes
are outside its accounting. If rate limits persist, lower these caps. Failed
paragraph artifacts remain available; the runner does not add another retry
loop on top of provider retries or publish incomplete combined output.

The run directory must not already
exist, so previous runs cannot be overwritten. No combined output is produced
if any paragraph fails or returns an empty/multiple-paragraph result.

Each run retains:

- `stage-1.txt`: exact snapshot of the paragraph-formatted input.
- `prompt.md`: snapshot of the grammar prompt used for this run.
- `paragraph-NNN/source.txt`: the input to that individual call.
- `paragraph-NNN/generated.txt` and `corrected.txt`: generated and validated output.
- `paragraph-NNN/command.json`, `response.json`, and `stderr.log`: invocation,
  API response with generation metadata, and diagnostics.
- `paragraph-NNN/changes.diff`: word-level comparison.
- `grammar.txt`: combined grammar-corrected candidate with the original paragraph count.
- `comparison.html`: side-by-side Stage 1 / Stage 2 comparison.
- `review.txt`: per-paragraph word counts and edit sizes, for reviewing larger changes.
- `failures.txt` if a run fails; successful individual paragraphs remain available.

Check the comparison for omissions or meaning changes, especially paragraphs
with large reductions. Word-count changes alone do not prove content loss.
Keep candidates and review artifacts even when a run is rejected. Never delete
intermediates automatically or overwrite raw/Stage 1 transcripts. The retained
`grammar.txt` is the retained candidate. After review, publish a copy at the
top level with the same title/date basename and `_corrected.txt` suffix:

```bash
talk_grammar_run="$HOME/Desktop/Sr Dang Nghiem/grammar-runs/love_in_training_09_10_2026-sol-2026-10-13"
cp -n "$talk_grammar_run/grammar.txt" \
  "$HOME/Desktop/Sr Dang Nghiem/love_in_training_09_10_2026_corrected.txt"
```

Verify the published copy matches the retained candidate; never overwrite a
different existing output. Record the run path and review outcome in
`processing-records/transcription-inventory.txt`.

The earlier single-pass `punctuate_dharma_talk` outputs are historical comparison
artifacts, not the default grammar stage. That prompt also restructures the
whole document and can delete wording. The older `omega_paragraphs.txt` records
a `default_punctuate` pass through legacy `SectionProcessor`; it does not record
a historical tnh-gen CLI command.

Validated October 13, 2026 on the existing Stage 1 files: all 50 Love in
Training paragraphs and all 26 Authentic Insight paragraphs completed. Both
runs retain one corrected block per source block and all comparison artifacts.
These full-document tests used the original `gpt-5-mini` grammar configuration.
The Love candidate reduced total words from 8,856 to 8,776; Insight from 9,849
to 9,816. These are candidates for editorial review, not semantic guarantees.
Review notes identify the Love paragraph 39 named-training punctuation and
paragraph 46 repetition/qualifier cleanup for attention. Earlier single-pass
outputs and logs are retained under `formatting-history/2026-10-12/` on Desktop.

Model selection: Sol is a stronger professional-work model than Mini; low
reasoning is the starting setting for this bounded editing task, rather than
assuming high reasoning improves grammar fidelity. See the
[official Sol model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [OpenAI rate-limit guidance](https://developers.openai.com/api/docs/guides/rate-limits).
Actual model quality is assessed through retained paragraph comparisons.

The Sol/low configuration with grammar prompt v1.1 was tested on October 13
using Love in Training paragraphs 39, 46, and 48. All three calls completed
under the shared local submission limits. The sample correctly punctuated
the named Fifth Mindfulness Training and retained the repeated training text
and lay Buddhist qualifier. The trust/distrust false start still needs review.
Artifacts and the source-paragraph mapping are retained under
`grammar-runs/love-sol-review-2026-10-13/`. The initial document runs used
Mini; this sample changes both model and prompt and is not a controlled
comparison of model quality alone.

Full Sol/low runs completed October 13, 2026 for both saved Stage 1 texts:
`grammar-runs/love_in_training_09_10_2026-sol-full-2026-10-13/` (50 paragraphs,
8,856 → 8,819 words) and
`grammar-runs/authentic_insight_on_10_04_2026-sol-full-2026-10-13/` (26 paragraphs,
9,849 → 9,805 words). All 76 paragraph calls succeeded, paragraph ordering/counts
were verified, and both Stage 1 sources remained byte-identical to their run
snapshots. Retained `grammar.txt`, `comparison.html`, and `review-notes.txt`
are available in each folder; prior Mini and Sol sample runs remain intact.

## Repository references

- [Audio-transcribe CLI reference](/docs/cli-reference/audio-transcribe.md)
- [tnh-gen CLI reference](/docs/cli-reference/tnh-gen.md)
- [Prompt system user guide](/docs/user-guide/prompt-system.md)
- CSV selection: `src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe.py:211`
- AssemblyAI pipeline: `src/tnh_scholar/cli_tools/audio_transcribe/transcription_pipeline.py:148`
- Provider option mapping: `src/tnh_scholar/audio_processing/transcription/assemblyai_service.py:232`
