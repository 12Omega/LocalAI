# UI Icons

This directory contains SVG icons for the Desktop GUI Application interface.

## Icon Set

All icons are designed with consistent styling:
- **Size**: 24x24 pixels
- **Stroke Width**: 2px
- **Style**: Modern, minimal line icons
- **Color**: `currentColor` (inherits text color for easy theming)

### Available Icons

| Icon | Filename | Usage |
|------|----------|-------|
| ▶️ | `run.svg` | Execute/start task button |
| ⏹️ | `stop.svg` | Stop/cancel running task button |
| ⚙️ | `settings.svg` | Open settings/configuration panel |
| 🕐 | `history.svg` | View task history |
| ❌ | `clear.svg` | Clear output/remove items |
| 📋 | `copy.svg` | Copy content to clipboard |
| 📥 | `export.svg` | Export data to file |
| 🗑️ | `delete.svg` | Delete item/entry |
| 📁 | `browse.svg` | Browse/select directory |

## Usage in HTML

```html
<!-- Inline SVG -->
<img src="assets/icons/run.svg" alt="Run" width="24" height="24">

<!-- As background image in CSS -->
.run-button {
  background-image: url('assets/icons/run.svg');
  width: 24px;
  height: 24px;
}

<!-- Direct SVG include for styling control -->
<button>
  <svg><!-- paste icon SVG content --></svg>
  Run Task
</button>
```

## Theming Support

All icons use `currentColor` for the stroke, which means they automatically inherit the text color of their parent element. This allows for easy theming:

```css
/* Light theme */
.light-theme .icon {
  color: #333;
}

/* Dark theme */
.dark-theme .icon {
  color: #fff;
}

/* Accent colors */
.run-button {
  color: #4caf50; /* Green */
}

.stop-button {
  color: #f44336; /* Red */
}
```

## Design Specifications

- **Stroke Cap**: Round (`stroke-linecap="round"`)
- **Stroke Join**: Round (`stroke-linejoin="round"`)
- **Fill**: None (outline style)
- **ViewBox**: 0 0 24 24

This ensures crisp rendering at all sizes and smooth, professional appearance.
