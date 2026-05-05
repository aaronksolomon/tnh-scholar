---
title: "Pipeline Case Study: Phat Giao Viet Nam OCR Journal Text"
description: "A worked case study — section, clean, and translate a scanned Vietnamese Buddhist journal article using tnh-gen."
owner: ""
author: ""
status: draft
created: "2026-05-04"
---

# Pipeline Case Study: Phat Giao Viet Nam OCR Journal Text

This case study follows TNH-scholar work on a real document, a PDF scanned article from Thich Nhat Hanh's edited 1950's journal, Phat Giao Viet Nam (Journal of Vietnamese Buddhism). This goes through a complete processing pipeline, transforming a scanned raw article from the journal, [*Vũ-trụ-quan Phật học*](assets/journal-pipeline/pgvn-17-18-vu-tru-quan-phat-hoc.pdf), to a full readable English translation: [*A Buddhist Cosmological View*](/user-guide/vu-tru-quan-phat-hoc-en.md).

[*Phật Giáo Việt Nam*](https://thuvienhoasen.org/a26248/tap-chi-phat-giao-viet-nam) is an important source for
studying Thich Nhat Hanh's early teachings, editorial work, and original thinking: he served as
editor-in-chief, authored many pieces under pen names, and helped shape a modern Buddhist
conversation in Vietnam before his later work became widely known internationally.

Much of this material has not been officially translated into English. `tnh-scholar`
is meant to work in exactly this kind of setting: not to create authoritative
translations, but to give translators and researchers a metadata-aware,
provenance-tracked generation stream that can serve as a baseline for real scholarly
translation work. The example here is a four-page OCR text with the kinds of damage
that make scanned journal materials hard to read, search, translate, and cite.

The case study shows what `tnh-gen` does at each stage, what the results look like,
and roughly how the commands fit together. Six commands cover the full pipeline.

---

## The Article

The text is *Vũ-trụ-quan Phật học* — *A Buddhist Cosmological View* — signed
Thạc-Đức and published in *Phật Giáo Việt Nam*, issue 17–18, December 1957.
`Thạc-Đức` is likely connected to `Trần Thạc Đức`, a pen name associated with
Thích Nhất Hạnh, but this case study treats the attribution cautiously: it records
the byline as it appears in the source and does not require the pipeline to resolve
the authorship question.

The article takes up a question that was important in the Buddha's time and
remained central for modern Buddhist reformers: what principle underlies the world
of experience, action, suffering, and liberation? The author (possibly Thich Nhat Hanh under a pen name) surveys three competing
answers that were current in ancient India — fatalism, divine-will theory, and pure
accidentalism — and works through why the Buddha's doctrine of dependent origination
(*duyên khởi*, *paticca-samuppāda*) offers something none of them can: a foundation
for moral responsibility and genuine human agency.

That makes the article useful on several levels at once. It is a Buddhist study of
causality reaching back to the early discourses; it is a Vietnamese Buddhist journal
article written in the reform atmosphere of the 1950s; and it sits near the beginning
of the historical arc through which Thich Nhat Hanh's thought developed from
Vietnamese Buddhist renewal into socially engaged Buddhism, peace work, and the
forms of Buddhist teaching that later took root in the United States and Europe.
For `tnh-scholar`, that combination matters: the pipeline must preserve philological
detail, historical context, uncertain attribution, and translator-facing provenance
rather than flattening the text into a generic English summary.

### The scanned pages

The processed text comes from four scanned journal pages. The two below bookend
the article and give a sense of the source material.

![Opening page of Vũ-trụ-quan Phật học — Phật Giáo Việt Nam issue 17–18, p. 7](assets/journal-pipeline/pgvn-17-18-page7-clean.jpg)

*Page 7 of the scan: article title, byline, and the opening argument.
The running footer `PHẬT-GIÁO VIỆT-NAM` is visible at the bottom — one of the
artifacts the clean stage must remove. ([View with OCR region annotations](assets/journal-pipeline/pgvn-17-18-page7.jpg))*

![Final page of the article — Phật Giáo Việt Nam issue 17–18, p. 10](assets/journal-pipeline/pgvn-17-18-page10-clean.jpg)

*Page 10: the article's closing argument on temporal causality, continuity of
existence, and liberation. The footer `PHẬT GIÁO VIỆT NAM` and a page-number
artifact appear near the bottom. ([View with OCR region annotations](assets/journal-pipeline/pgvn-17-18-page10.jpg))*

### Source and attribution note

The public source used for this walkthrough is the scanned PDF of *Phật Giáo Việt Nam*,
issue 17–18. The scan is hosted by Thư Viện Hoa Sen, and the collection page notes
that the journal was digitized by Thư Viện Huệ Quang in 2013:

- Collection page: <https://thuvienhoasen.org/a26248/tap-chi-phat-giao-viet-nam>
- Direct PDF: <https://thuvienhoasen.org/images/file/4Vp0iwbv0wgQAJAY/phat-giao-viet-nam-1956-17-18.pdf>
- Hoa Vô Ưu mirror/reference page: <https://hoavouu.com/a24580/nguyet-san-phat-giao-viet-nam-1956>

A second catalog record at Tài Liệu Phật Học lists the same periodical collection and
identifies item 33 as *Nguyệt san Phật Giáo Việt Nam Số 17-18 -1957*:

- Catalog record: <https://tailieuphathoc.com/tai-lieu/nguyet-san-phat-giao-viet-nam-do-tong-hoi-phat-giao-viet-nam-xuat-ban-dat-tai-chua-an-quang-tu-nam-1956-1959-1892?viewpdf=2325>

The dating is worth preserving as source metadata rather than normalizing too early:
some library URLs and labels use `1956`, while catalog entries for the same issue list
`1957`. The article itself belongs to the 1950s *Phật Giáo Việt Nam* corpus, and the
local file metadata here stays aligned with the scanned source being used.

For research context, recent scholarship describes Thích Nhất Hạnh as editor-in-chief
of *Phật Giáo Việt Nam* from 1956 to 1959 and treats `Thạc Đức` as one of the bylines
associated with him while also noting that Nhất Hạnh himself did not confirm every
such attribution. That makes this a good example for the system: the pipeline can
preserve uncertain historical metadata without forcing it into a false certainty.

The source files live at `tests/golden/journal-pipeline/` in this repository.

### What the raw OCR looks like

When the scan comes out of the OCR process, it looks like this:

```
VŨ-TRỤ-QUAN
PHAT-HOC                     ← title diacritics dropped
THẠC - ĐỨC
...
1.―
1-                           ← duplicate section marker
Khuynh hướng Túc mệnh-luận (Pubba kata hetu)
...
họa phúc đều
PHẬT GIÁO VIỆT NAM           ← running journal footer landed mid-paragraph
...
thấu suốt quá khứ vị lai hiện-
THẢI CHO MỌT NẤU             ← page footer artifact (page 10)
```

The text is mostly intact — sentences, structure, vocabulary — but there are broken
lines, dropped diacritics, and stray running-header lines scattered through the
paragraphs. This is what `tnh-gen` is built to handle.

---

## What's needed

Two CLI tools from the repo:

- **`tnh-lines`** — adds or removes line numbers from a text file
- **`tnh-gen`** — runs a prompt against a file and writes the result

All commands run from the repo root. Prompts come from the local prompt workspace:

```bash
--prompt-dir ./tnh-prompts
```

A few shell variables simplify the commands throughout:

```bash
SOURCE_FILE=tests/golden/journal-pipeline/source.txt
WORK_DIR=tests/golden/journal-pipeline/walkthrough/clean_translate
METADATA='title: Vũ-trụ-quan Phật học
author: Thạc-Đức
possible_author: Trần Thạc Đức / Thích Nhất Hạnh attribution uncertain
journal: Phật Giáo Việt Nam
issue: 17-18
year: 1957
digitized_by: Thư Viện Huệ Quang, 2013
source_page: https://thuvienhoasen.org/a26248/tap-chi-phat-giao-viet-nam
source_pdf: https://thuvienhoasen.org/images/file/4Vp0iwbv0wgQAJAY/phat-giao-viet-nam-1956-17-18.pdf
source_mirror: https://hoavouu.com/a24580/nguyet-san-phat-giao-viet-nam-1956'
```

---

## Pipeline overview

```
PDF scan
  ↓ OCR
raw OCR text
  ↓ tnh-lines number
numbered source
  ↓ tnh-gen default_section
sections.json
  ↓ extract section
section raw text
  ↓ tnh-gen default_clean
cleaned Vietnamese
  ↓ tnh-gen translate_journal_section_en
English draft translation + provenance
```

The walkthrough below follows this sequence step by step. The extract step is a
plain `sed` range — there is no dedicated command yet; that is one of the friction
points noted in the [UX directions note](/architecture/tnh-gen/notes/tnh-gen-ux-directions-2026-05.md).

---

## Stage 1: Number the lines

The sectioning prompt needs numbered input to anchor its section boundaries.
We add line numbers to the source first:

```bash
tnh-lines number \
  $SOURCE_FILE \
  $WORK_DIR/source_numbered.txt
```

The output is plain text with `N:LINE` formatting — every line prefixed with its
position. The OCR text is unchanged; this just gives the model something to anchor
its section boundaries to.

```
1:VŨ-TRỤ-QUAN
2:PHAT-HOC
3:THẠC - ĐỨC
4:Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn-
5:đề rất được chú trọng trong tư tưởng-giới Ấn Độ. Kinh Phạm-Động có
```

---

## Stage 2: Section the article

`default_section` reads the numbered source and divides it into logical sections.
It also generates document-level metadata — a summary, key concepts, and section
titles in both Vietnamese and English — that will travel with the text through later
stages.

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt default_section \
  --input-file $WORK_DIR/source_numbered.txt \
  --var source_language=Vietnamese \
  --var target_section_count=4 \
  --var target_lines_per_section=36 \
  --var document_metadata="$METADATA" \
  --output-file $WORK_DIR/sections.json
```

The output is a JSON file. Here is what it finds in this article:

| Section | Lines | Title |
|---------|-------|-------|
| 1 | 1–48 | Indian Intellectual Context and Buddhism's Critical Stance |
| 2 | 49–93 | The Conditioned World and the Principle of Dependent Origination |
| 3 | 94–124 | Simultaneous Causality and the Constitution of the World of Cognition |
| 4 | 125–146 | Successive-Time Causality, Continuity of Life, and Ethical-Liberative Meaning |

Beyond the section map, the JSON includes a document summary, key concepts
(`nhân duyên`, `duyên khởi`, `vô thường`, `luân hồi`, and more), Dublin Core
metadata, and a narrative context note explaining the structure of the argument.
This context gets passed into the translation stage.

The section map is worth reviewing before proceeding. If a boundary looks off —
a section breaks mid-argument, or two short sections should be merged — the JSON
can be edited directly at this point.

---

## Stage 3: Extract a section

We work through section 1 first. Taking `start_line` and `end_line` from the JSON,
we extract that range from the numbered source (lines 1–48):

```bash
sed -n '1,48p' \
  $WORK_DIR/source_numbered.txt \
  > $WORK_DIR/section_01_numbered.txt
```

Next, we strip the line numbers — cleaning and translation work on plain text:

```bash
tnh-lines unnumber \
  $WORK_DIR/section_01_numbered.txt \
  $WORK_DIR/section_01_raw.txt
```

This gives us the raw OCR text for section 1, ready to clean.

---

## Stage 4: Clean the OCR text

`default_clean` corrects OCR damage while staying close to the original. It removes
stray footer lines, restores dropped diacritics, and rejoins lines that were split
across page boundaries — without rewriting the text or changing its register.

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt default_clean \
  --input-file $WORK_DIR/section_01_raw.txt \
  --vars $WORK_DIR/clean_vars.json \
  --output-file $WORK_DIR/section_01_cleaned.txt
```

Before cleaning, section 1 opens like this:

```
VŨ-TRỤ-QUAN
PHAT-HOC
THẠC - ĐỨC
...
1.―
1-
Khuynh hướng Túc mệnh-luận (Pubba kata hetu)
```

After cleaning:

```
VŨ-TRỤ-QUAN
PHẬT-HỌC
THẠC-ĐỨC

Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn đề rất
được chú trọng trong tư tưởng giới Ấn Độ. Kinh Phạm-Động có chép lại đến
sáu mươi hai lối giải thích khác nhau của các triết-phái Ấn-Độ thời ấy.
Tựu trung, ta thấy có ba khuynh hướng sau đây:

1. — Khuynh hướng Túc mệnh-luận (Pubba kata hetu)
```

Title diacritics restored. Duplicate section marker collapsed to one. Lines rejoined
into continuous prose. The footer intrusion that appeared mid-paragraph on page 7
(`PHẬT GIÁO VIỆT NAM`) is gone.

---

## Stage 5: Translate the section

`translate_journal_section_en` translates a cleaned section into English, using the
document context from the sectioning JSON — the summary, key concepts, and section
structure — to make consistent terminology choices across sections.

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt translate_journal_section_en \
  --input-file $WORK_DIR/section_01_cleaned.txt \
  --vars $WORK_DIR/section_01_journal_translate_vars.json \
  --output-file $WORK_DIR/section_01_translated.txt
```

The vars file carries the section context from `sections.json` forward into this
call. See [Using a vars file](#using-a-vars-file) below.

Here is the opening of the translation:

---

*The Indian Intellectual Context and Buddhism's Critical Stance*

In the time of the Buddha, the question of the principle underlying all things was
one to which the Indian intellectual world gave great attention. The Brahmajāla Sutta
records as many as sixty-two different explanations advanced by the Indian
philosophical schools of that age. In sum, we may discern the following three
tendencies:

1.— The tendency of fatalism (*pubba-kata-hetu*)

The philosophical schools belonging to this tendency held that both the natural world
and the human world are arranged by predestination. Everything operates according to
pre-existing natural laws. The value of human effort and material agency is not
acknowledged here.

---

And here is the closing of the fourth and final section:

---

In sum, the Buddhist conception of causality, in its narrow sense, is simply the law
of causality; but in its broader sense, it is not confined to causal relations of a
purely theoretical kind. The Buddhist conception of causality also encompasses ethical
and soteriological relations; in breadth it extends throughout the ten directions,
and in length it penetrates past, future, and present.

---

The complete four-section translation — assembled from the pipeline artifacts and
formatted as a readable document — is at
[*Vũ-trụ-quan Phật học*: A Buddhist Cosmological View](/user-guide/vu-tru-quan-phat-hoc-en.md).

---

## Stage 6: Repeat for remaining sections

The same clean → translate pattern applies to sections 2, 3, and 4. Each section
gets its own cleaned file and its own translated file. The section-level vars files
carry the right context for each one.

When all four sections are done:

```bash
cat $WORK_DIR/section_0{1,2,3,4}_translated.txt > $WORK_DIR/final_translated.txt
```

---

## What the terminal shows

While a model call is running, the terminal is quiet. On success:

- the result prints to `stdout`
- if `--output-file` was used, a confirmation appears on `stderr`:
  `Wrote output to <path>`

On failure, an error message and a trace ID appear. The trace ID is useful for
reporting problems.

Each output file also gets a provenance header — model name, prompt version,
timestamp, fingerprint — written as YAML front matter at the top of the file. This
makes the artifacts self-documenting and allows later comparison runs to detect
regressions.

---

## Using a vars file

The `--vars` flag loads a JSON file as a batch of variables. For translation, the
section-specific vars file carries the document context forward:

```json
{
  "source_language": "Vietnamese",
  "target_language": "English",
  "style": "scholarly",
  "document_summary": "...",
  "section_title": "Indian Intellectual Context...",
  "key_concepts": ["nhân duyên", "duyên khởi", ...]
}
```

This is built from `sections.json` by pulling out the relevant section entry
along with the document-level fields. Individual `--var key=value` flags can
supplement or override.

---

## Artifact layout

After running the full pipeline, the working directory looks like this:

```
tests/golden/journal-pipeline/walkthrough/clean_translate/
├── source_numbered.txt
├── sections.json
├── sections.json.provenance.yaml
├── section_01_numbered.txt
├── section_01_raw.txt
├── section_01_cleaned.txt
├── section_01_journal_translate_vars.json
├── section_01_translated.txt
├── section_02_raw.txt      ← (and numbered, cleaned, vars, translated)
├── section_03_raw.txt
├── section_04_raw.txt
├── section_04_cleaned.txt
├── section_04_translated.txt
└── final_translated.txt
```

These files are local-only and not tracked in git. They are useful for review,
comparison runs, and prompt refinement.

---

## Where this is going

`tnh-gen` is designed as a backend engine. The command-line workflow shown here is
the current working surface — explicit, inspectable, and well-suited for operator-driven
runs where each stage deserves review. But the same prompt execution, provenance
tracking, and structured output are intended to power richer interfaces as the project
develops.

The planned trajectory:

- **VS Code extension** — the nearest-term direction. A panel that lets a user open
  a source file, run sectioning, review and adjust the section map, then step through
  clean and translate without leaving the editor. The artifact chain stays the same;
  the command surface becomes a UI.

- **TUI (terminal user interface)** — for users who prefer staying in the terminal but
  want a navigable, interactive view of the pipeline state: live artifact previews,
  section selection, and prompt output rendered in place rather than written to files
  first.

- **Web interface** — a longer-term direction for collaborative or institutionally-hosted
  use, where translators, editors, and researchers can work together on a shared
  document queue with version tracking and annotation.

In all cases, `tnh-gen` stays as the execution layer. The prompts, the vars contract,
the provenance sidecars, and the structured JSON output from the sectioner are the
stable foundation that the interfaces will build on top of.

---

## See also

- [tnh-gen CLI Reference](/cli-reference/tnh-gen.md)
- [Prompt System](/user-guide/prompt-system.md)
- [Best Practices](/user-guide/best-practices.md)
