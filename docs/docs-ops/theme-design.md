---
title: "TNH Scholar Theme Design"
description: "Zen-inspired documentation theme blending mindfulness aesthetics with modern AI tooling"
owner: ""
author: ""
status: current
created: "2025-12-02"
---
# TNH Scholar Theme Design

The TNH Scholar documentation theme embodies Thich Nhat Hanh's aesthetic philosophy: minimalist zen calligraphy meets modern AI, with organic simplicity and mindful design.

## Design Philosophy

### Inspiration Sources

**Thich Nhat Hanh's Calligraphy**
- Brush strokes on rice paper
- Minimal, intentional marks
- Breathing space between elements
- Organic, flowing forms

**Plum Village Tradition**
- Earth tones and natural colors
- Peaceful, contemplative atmosphere
- Accessible clarity
- Grounded presence

**Modern AI Context**
- Technical precision with warmth
- Clear information architecture
- Professional yet approachable
- Dark mode for reduced eye strain

## Color Palette

### Primary Colors (Sumi Ink & Rice Paper - Inverted)

```css
--tnh-ink-black: #1a1a1a;      /* Deep sumi ink background */
--tnh-charcoal: #2d2d2d;       /* Brush charcoal surfaces */
--tnh-slate: #3d3d3d;          /* Stone slate elevated */
--tnh-rice-paper: #f5f1e8;     /* Warm cream text */
--tnh-soft-white: #e8e4d8;     /* Aged paper primary text */
```

### Accent Colors (Buddhist Tradition)

```css
--tnh-lotus-pink: #d4a5a5;     /* Lotus flower - wisdom */
--tnh-bamboo-green: #7a9b76;   /* Bamboo - resilience */
--tnh-zen-gold: #c9a961;       /* Temple gold - code */
--tnh-plum-purple: #9d8ba6;    /* Plum blossom - beauty */
--tnh-meditation-blue: #6b8e9e; /* Still water - links */
```

### Color Meanings

- **Bamboo Green** (`#7a9b76`): Primary accent, navigation, active states
  - Represents flexibility and resilience
  - Used for interactive elements and highlights

- **Meditation Blue** (`#6b8e9e`): Links and navigation
  - Represents calm presence and clarity
  - Gentle on the eyes for extended reading

- **Zen Gold** (`#c9a961`): Code and technical content
  - Represents illumination and understanding
  - Warm contrast against dark backgrounds

- **Lotus Pink** (`#d4a5a5`): Warnings and special notices
  - Represents wisdom emerging from complexity
  - Soft, non-alarming attention-getter

## Typography

### Font Stack

**Headings**: Source Serif 4 (200-500 weight)
- Elegant, classical serif with modern clarity
- Light weights (200-300) for main headings
- Reminiscent of brush calligraphy fluidity

**Body Text**: Inter (300-600 weight)
- Highly legible sans-serif
- Excellent screen rendering
- Professional and approachable

**Code**: JetBrains Mono
- Designed for developers
- Clear distinction of characters
- Comfortable for extended reading

### Typographic Scale

- **h1**: 2.5rem, weight 200, bottom border
- **h2**: 2rem, weight 300
- **h3**: 1.5rem, bamboo green color
- **Body**: 1rem, line-height 1.8 (spacious)

## Spacing Philosophy

### Mindful Breathing Room

```css
--tnh-space-breath: 2rem;    /* Major section breaks */
--tnh-space-pause: 1.5rem;   /* Between elements */
--tnh-space-moment: 1rem;    /* Internal padding */
```

Spacing follows the concept of "breathing room" - enough space for ideas to settle, similar to pauses in meditation.

## Design Elements

### Headings
- Lightweight, elegant serif font
- Generous spacing above and below
- H1 with subtle underline in bamboo green
- H3 colored to create visual hierarchy

### Links
- Meditation blue default color
- Subtle underline on hover (bamboo green)
- Smooth color transitions (0.3s)

### Code Blocks
- Dark background (#252525) for reduced eye strain
- Bamboo green left border for visual anchor
- Zen gold text for syntax elements
- Comfortable padding and border radius

### Blockquotes
- Lotus pink left border
- Subtle background tint (5% opacity)
- Italic text style
- Used for teachings, insights, important notes

### Tables
- Bamboo green header underline
- Subtle row hover (5% green tint)
- Clear borders in slate
- Spacious padding (0.75rem)

### Admonitions
- Color-coded by type (note, tip, warning, danger)
- Subtle background tint
- Left border for visual weight
- Breathing space around content

## Interactive Elements

### Navigation
- Active links in bamboo green
- Smooth hover transitions
- Clear visual hierarchy
- Instant page transitions

### Buttons
- Bamboo green background
- Subtle lift on hover
- Rounded corners (4px)
- Organic shadow

### Search
- Integrated into dark theme
- Suggestion support
- Highlight matching terms
- Smooth dropdown

## Material Theme Integration

The theme extends [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) with custom CSS overrides.

### Features Enabled

- `navigation.instant` - Smooth page transitions
- `navigation.tracking` - URL tracking
- `navigation.tabs` - Top-level organization
- `navigation.sections` - Hierarchical structure
- `navigation.top` - Back-to-top button
- `search.suggest` - Search suggestions
- `search.highlight` - Result highlighting
- `content.code.copy` - Copy code blocks
- `content.tabs.link` - Linked content tabs

### Custom Overrides

Location: `docs/overrides/main.html`
- Google Fonts integration (Inter, Source Serif 4, JetBrains Mono)
- Material color scheme overrides
- Custom meta tags
- Mindful interaction scripts

## Files

### Theme Components

```
docs/
├── stylesheets/
│   └── tnh-zen.css          # Main theme stylesheet
└── overrides/
    └── main.html             # Template overrides
```

### Configuration

```yaml
# mkdocs.yaml
theme:
  name: material
  palette:
    scheme: slate              # Dark mode base
    primary: custom            # Custom primary color
    accent: custom             # Custom accent color
  font:
    text: Inter
    code: JetBrains Mono
  custom_dir: docs/overrides

extra_css:
  - stylesheets/tnh-zen.css
```

## Design Principles

### Zen Aesthetics
1. **Simplicity**: Remove unnecessary elements
2. **Space**: Generous breathing room
3. **Intention**: Every element serves a purpose
4. **Organic**: Natural, flowing forms
5. **Presence**: Clear visual hierarchy

### Accessibility
1. **Contrast**: WCAG AA compliant color ratios
2. **Typography**: Highly legible fonts, generous sizing
3. **Focus**: Clear focus indicators (bamboo green)
4. **Smooth**: Gentle transitions and animations
5. **Semantic**: Proper HTML structure

### Technical Excellence
1. **Performance**: Minimal CSS, efficient selectors
2. **Responsive**: Mobile-first design
3. **Modern**: CSS custom properties
4. **Maintainable**: Well-documented, organized
5. **Extensible**: Easy to customize

## Future Enhancements

### Potential Additions

- [ ] Custom favicon with lotus or bamboo icon
- [ ] Animated brush stroke dividers
- [ ] Calligraphy-style logo
- [ ] Optional light mode with inverted palette
- [ ] Seasonal color variations (spring/summer/autumn/winter)
- [ ] Mindfulness timer integration for reading breaks
- [ ] Poetry excerpts in sidebar

### Typography Refinements

- [ ] Consider Noto Serif CJK for Vietnamese/Chinese characters
- [ ] Explore variable fonts for smoother scaling
- [ ] Test readability across different screen sizes

### Color Adjustments

- [ ] A11y audit for all color combinations
- [ ] Optional high-contrast mode
- [ ] Color-blind friendly palette verification

## Usage Guidelines

### For Documentation Authors

**Use bamboo green for**:
- Active navigation elements
- Completed tasks
- Success messages
- Primary CTAs

**Use meditation blue for**:
- Links to other pages
- Reference materials
- External resources

**Use zen gold for**:
- Code and technical terms
- Configuration values
- File paths and commands

**Use lotus pink for**:
- Important notices
- Wisdom quotes
- Special callouts

### Writing Style

Match the visual aesthetic with content:
- Clear, concise language
- Breathing space between ideas
- Intentional word choice
- Accessible technical explanations

## Inspiration & References

- [Thich Nhat Hanh Calligraphy](https://plumvillage.org/about/thich-nhat-hanh/calligraphy/)
- [Material Design Color System](https://material.io/design/color/)
- [Zen and the Art of Web Design](https://en.wikipedia.org/wiki/Wabi-sabi)
- [Japanese Aesthetics](https://en.wikipedia.org/wiki/Japanese_aesthetics)
- [Buddhist Symbolism](https://en.wikipedia.org/wiki/Buddhist_symbolism)

---

*May this theme support clarity, peace, and understanding in documentation.*
