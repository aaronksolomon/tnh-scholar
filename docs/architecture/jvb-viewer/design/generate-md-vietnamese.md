---
title: "Generate Markdown Vietnamese"
description: "Guidelines for rewriting Vietnamese journal pages into structured Markdown with one sentence per line and preserved metadata."
owner: ""
author: ""
status: current
created: "2025-11-15"
---
# Generate Markdown Vietnamese

Guidelines for rewriting Vietnamese journal pages into structured Markdown with one sentence per line and preserved metadata.

## Task

Read the provided journal page and return a Markdown version of the page.
Each sentence or fragment (such as a heading) of the Journal page must be on its own line.

## Context

This journal is from Phat Giao Viet Nam 1956, Volume 16, edited by Thich Nhat Hanh.

The page is from a section of the journal with the following metadata:

       {
            "title_vi": "LUÂN HỒI MỘT THỰC THỂ",
            "title_en": "REINCARNATION AS A REALITY",
            "author": "THẠC ĐỨC",
            "summary": "This article discusses the Buddhist concept of reincarnation, emphasizing its reality for those who have attained enlightenment. It explores the relationship between karma and rebirth, and how modern psychology and scientific discoveries are beginning to align with these ancient teachings.",
            "keywords": [
                "Reincarnation",
                "Karma",
                "Buddhism",
                "Psychology"
            ],
            "start_page": 30,
            "end_page": 34
        }

Core rules (read carefully):

 1. CRITICAL:
    - One sentence or fragment per line.
    - Do not wrap long lines.
    - Do not add trailing spaces to lines.
 2. Paragraphs are represented by a blank line (normal Markdown).
 3. Headings become Markdown headings (#, ##, ###, ####) on a single line.
 4. Bullets/lists: each bullet is on one line.
 5. Use `-` only for unordered lists.
 6. Use numbering: `1.`, `2.` for ordered lists.
 7. Nested lists are allowed. Use double (2) spaces to indicate nesting.
 8. Where appropriate, tables may also be created the `|` pipe symbol.
 9. Block quotes: prefix each quoted line with >
 10. For Poetry / verse / special layout (such as a box): use 9 spaces or more of indent:

         this is an line of verse
            this is another more indented line

11. Inline emphasis: use only `*`: *italic*, **bold**, ***bold italic***
12. Match punctuation with the source document exactly if the punctuation symbol exists in UTF, otherwise use a close approximation.
13. Include the page number on the bottom of the page if present.
14. Use --- as rule lines where present.
15. Incomplete sentences at the beginning or end of the page should be rendered exactly as is.
    - They will be fragments on their own line without ellipsis or other formatting, except what is in the original text.
16. Add no commentary.

## Granularity

- “Sentence or fragment” = a grammatically coherent unit. Headings, captions, phrases, sentences.
- For lists, the bullet item is the unit. If a list item spans multiple sentences, all those sentences should be included on the line.
- For tight paragraphs with multiple sentences: split into one sentence per line, then place a blank line to separate the paragraphs.

## Complex Layout

- For text that is laid out in a complex fashion on the page, interpret to a minimal reduction that is feasible in markdown but still communicates the logical intent: e.g. use heading levels, paragraphs, lists, tables, or other structures to demarcate information.
- Attempt to capture as much contextual/structural meaning as possible using appropriate and possibly creative Markdown styling.

## Correction Policy

- Make the best optical interpretation of the text possible, using context for difficult to scan characters.
- Use a box symbol ▢ (U+25A1) for completely illegible characters
- Do not correct grammar, spelling or other structural errors where the graphical marks are clear.

## Input

You will receive an image of a scanned page. Use all signals (layout, headings, bullets, punctuation) to build the Markdown.

## Output

Return the markdown formatted text in a markdown fence block as in:

```markdown
    <markdown formatted text>
```

to allow easier use of the markdown data.