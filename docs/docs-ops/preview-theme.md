---
title: "Preview TNH Scholar Theme"
description: "Quick guide to previewing the custom zen theme locally"
owner: ""
author: ""
status: current
created: "2025-12-02"
---
# Preview TNH Scholar Theme

Quick guide to preview the custom zen-inspired documentation theme.

## Quick Preview

Build and serve the documentation locally:

```bash
# Build the documentation
poetry run mkdocs build

# Serve locally with live reload
poetry run mkdocs serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Theme Features to Test

### Visual Elements

1. **Color Palette**
   - Dark sumi ink background (#1a1a1a)
   - Warm rice paper text (#e8e4d8)
   - Bamboo green accents (#7a9b76)
   - Check contrast and readability

2. **Typography**
   - Source Serif 4 headings (elegant, lightweight)
   - Inter body text (clean, professional)
   - JetBrains Mono code (developer-friendly)

3. **Spacing**
   - Generous breathing room between sections
   - Comfortable reading width (48rem max)
   - Organic padding and margins

### Interactive Elements

1. **Navigation**
   - Hover effects on links (bamboo green underline)
   - Active page highlighting
   - Smooth page transitions

2. **Code Blocks**
   - Copy button functionality
   - Syntax highlighting with zen gold
   - Left border in bamboo green

3. **Search**
   - Dark theme integration
   - Suggestion popups
   - Result highlighting

### Content Types

Test the theme with different content:

1. **Headers** (h1-h6)
2. **Lists** (bulleted, numbered, task lists)
3. **Tables** (check hover effects)
4. **Blockquotes** (lotus pink border)
5. **Admonitions** (note, tip, warning, danger)
6. **Code** (inline and blocks)
7. **Links** (internal and external)

## Sample Content

Visit these pages to see theme in action:

- [Index](/index.md) - Hero content and overview
- [Architecture Overview](/architecture/overview.md) - Technical content with code
- [Quick Start Guide](/getting-started/quick-start-guide.md) - User-facing docs
- [Theme Design](theme-design.md) - Color palette showcase
- [ADR Template](adr-template.md) - Structured document format

## Customization

### Adjust Colors

Edit `docs/stylesheets/tnh-zen.css`:

```css
:root {
  /* Change any color variable */
  --tnh-bamboo-green: #7a9b76;  /* Primary accent */
  --tnh-meditation-blue: #6b8e9e; /* Links */
  --tnh-zen-gold: #c9a961;      /* Code */
}
```

### Modify Spacing

```css
:root {
  --tnh-space-breath: 2rem;   /* Section spacing */
  --tnh-space-pause: 1.5rem;  /* Element spacing */
  --tnh-space-moment: 1rem;   /* Internal padding */
}
```

### Change Fonts

Edit `mkdocs.yaml`:

```yaml
theme:
  font:
    text: Inter              # Body font
    code: JetBrains Mono     # Code font
```

For headings, edit `docs/overrides/main.html` Google Fonts import.

## Browser Testing

Test across browsers for consistency:

- Chrome/Edge (Chromium)
- Firefox
- Safari
- Mobile browsers (responsive design)

## Dark Mode

The theme is designed for dark mode by default. To add light mode support, you would need to create alternate color schemes in `mkdocs.yaml`:

```yaml
theme:
  palette:
    # Dark mode (default)
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
    # Light mode (inverted palette)
    - scheme: default
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
```

## Performance

Check the theme performs well:

1. **Page Load**: Should be fast with minimal CSS
2. **Smooth Scrolling**: Anchor links scroll smoothly
3. **Transitions**: Hover effects are smooth (0.3s)
4. **Font Loading**: Web fonts load progressively

## Accessibility

Verify accessibility features:

1. **Contrast Ratios**: All text meets WCAG AA standards
2. **Focus Indicators**: Bamboo green outline on focus
3. **Keyboard Navigation**: Tab through all interactive elements
4. **Screen Readers**: Semantic HTML structure

## Troubleshooting

### CSS Not Loading

```bash
# Clear the site directory and rebuild
rm -rf site/
poetry run mkdocs build
```

### Fonts Not Showing

Check Google Fonts loaded in browser DevTools:
1. Open Network tab
2. Filter by "fonts.googleapis.com"
3. Verify Inter, Source Serif 4, and JetBrains Mono loaded

### Colors Look Wrong

Verify Material theme version:
```bash
poetry show mkdocs-material
```

Should be compatible with Material 9.x+

## Production Deployment

Before deploying:

1. **Build with strict mode**: `poetry run mkdocs build --strict`
2. **Test all links**: Run lychee link checker
3. **Verify responsive**: Test mobile layouts
4. **Check performance**: Use Lighthouse audit

## Feedback

The theme is designed to be minimal, peaceful, and functional. Adjust as needed while maintaining:

- Dark backgrounds for reduced eye strain
- Warm, organic color palette
- Generous spacing for breathing room
- Clear visual hierarchy
- Professional yet approachable aesthetic

---

*Walk mindfully through the documentation.*
