
# Generate Markdown Translation JSON Pairs

## Task

Read the provided journal page and return a JSON array named "lines".
Each element is a pair of Markdown lines: the original Vietnamese ("vi") and the English translation ("en").

Core rules (read carefully):

 1. One sentence or fragment per line. Do not wrap long lines.
 2. Paragraphs are represented by a blank pair between groups:
 {"vi": "", "en": ""}
 3. Headings become Markdown headings (#, ##, ###, ####) on a single line.
 4. Bullets/lists: each bullet is one line.
 5. Use `-` only for unordered lists.
 6. Use numbering such as `1.`, `2.` for ordered lists.
 7. Nested lists are allowed. Use tabs to indicate nesting.
 8. Where appropriate and clear, tables may also be created using the `|` pipe symbol.
 9. Block quotes: prefix each quoted line with >  in both languages (one fragment per line).
 10. Poetry / verse / special layout: use a fenced block:
    - Open with: plaintext (on its own line, as a pair)
    - Put one verse line per JSON pair (no extra blank lines inside)
    - Close with: plaintext
11. Inline emphasis: keep Markdown clear and minimal, using only `*`
    - *italic*, **bold**, ***bold italic***
12. Match punctuation to the source document for Vietnamese, and natural for English
13. No extra commentary in the JSON. Do not add keys other than "vi" and "en", and the required outer "lines" array.


## Output format (strict)

```plaintext
{
  "lines": [
    {"vi": "<markdown line 1>", "en": "<markdown line 1 translated>"},
    {"vi": "<markdown line 2>", "en": "<markdown line 2 translated>"},
    {"vi": "", "en": ""},                       // paragraph break
    // …
  ]
}
```

## Granularity guidance

- “Sentence or fragment” = a grammatically coherent unit. Headings and captions are fragments.
- For lists, the bullet item is the unit. If it spans multiple sentences, all those sentences should be included on the line.
- For tight paragraphs with multiple sentences: split into one JSON pair per sentence, then place a blank pair to end the paragraph.

## Complex layout guidance

- For text that is laid out in a complex fashion on the page, interpret to a minimal reduction that is feasible in markdown but still communicates some of the logical intent: e.g. use paragraphs, lists or other structures to demarcate information.

## Language policy

- vi = Vietnamese as faithfully read from the page.
- en = idiomatic, accurate English translation in the style of Thich Nhat Hanh on the same line.
- Preserve names, dates, and terms; translate only where appropriate (e.g., don’t localize proper nouns).

## Input

You will receive an image of a scanned page. Use all signals (layout, headings, bullets, punctuation) to infer Markdown.

## Output

Return only the JSON object.

⸻

Example of Expected JSON:

```plaintext
{
  "lines": [
    {"vi": "# Câu chuyện thống nhất", "en": "# The Story of Unification"},
    {"vi": "## Lời mở đầu", "en": "## Foreword"},

    {"vi": "", "en": ""},

    {"vi": "Thực vậy, vấn đề thống nhất đã làm chúng ta trăn trở nhiều năm.", "en": "Indeed, the issue of unification has troubled us for many years."},
    {"vi": "Nhưng với tinh thần hòa hợp, chúng ta có thể bước đi cùng nhau.", "en": "Yet, with a spirit of harmony, we can walk together."},

    {"vi": "", "en": ""},

    {"vi": "- Phát huy lòng từ bi trong mọi hành xử.", "en": "- Cultivate compassion in every action."},

    {"vi": "", "en": ""},

    {"vi": "```plaintext", "en": "```plaintext"},
    {"vi": "Sáng mai sương mỏng phủ hiên chùa", "en": "Tomorrow’s dawn, a thin mist veils the temple eaves"},
    {"vi": "Tiếng chuông nhẹ khẽ gọi tên người", "en": "A gentle bell softly calls our names"},
    {"vi": "```", "en": "```"}
    {"vi": "| Tiếng chuông |", "en": "| Bell |" }
  ]
}
```
