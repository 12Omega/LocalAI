# CSS Styling System

## Overview

The Local AI Development Environment desktop GUI uses a modern, maintainable CSS architecture with a theme system supporting both light and dark modes.

## File Structure

```
css/
├── main.css                 # Base styles, layout, and components
├── themes/
│   ├── light.css           # Light theme color variables
│   └── dark.css            # Dark theme color variables
└── components/             # Component-specific styles
    ├── buttons.css         # Button styles
    ├── inputs.css          # Input field styles
    └── progress.css        # Progress message styles
```

## Architecture

### Main Stylesheet (`main.css`)

The main stylesheet contains:

- **CSS Reset**: Normalized browser defaults
- **Typography**: Font families, sizes, line heights
- **Layout**: CSS Grid-based application layout
- **Components**: Base styles for all UI components
- **Responsive Design**: Breakpoints at 800px, 1000px, 1400px
- **Animations**: Smooth transitions and animations
- **Accessibility**: Focus states and screen reader support

#### Layout Structure

The application uses CSS Grid for the main layout:

```
┌─────────────────────────────────┐
│         Header (fixed)          │
├─────────────────────────────────┤
│      Navigation (fixed)         │
├─────────────────────────────────┤
│                                 │
│      Content (scrollable)       │
│                                 │
├─────────────────────────────────┤
│         Footer (fixed)          │
└─────────────────────────────────┘
```

Grid template areas:
- `header`: Application branding and theme toggle
- `navigation`: Tab-based navigation
- `content`: View-specific content (Task, History, Settings)
- `footer`: Status bar

### Theme System

The theme system uses CSS custom properties (variables) for easy customization and runtime switching.

#### Light Theme (`themes/light.css`)

Default color scheme with high contrast for readability:
- Background: White (#ffffff)
- Surface: Light gray (#f9fafb)
- Primary: Blue (#2563eb)
- Success: Green (#10b981)
- Error: Red (#ef4444)

#### Dark Theme (`themes/dark.css`)

Dark color scheme for reduced eye strain:
- Background: Dark gray (#111827)
- Surface: Medium gray (#1f2937)
- Primary: Light blue (#3b82f6)
- Success: Green (#10b981)
- Error: Red (#ef4444)

### Color Variables

Both themes define the following CSS custom properties:

**Primary Colors:**
- `--primary`: Main action color
- `--primary-hover`: Hover state
- `--primary-alpha`: Transparent variant
- `--success`: Success states
- `--warning`: Warning states
- `--error`: Error states
- `--info`: Informational states

**Neutral Colors:**
- `--background`: Main background
- `--surface`: Card/panel backgrounds
- `--border`: Border colors
- `--text-primary`: Main text color
- `--text-secondary`: Secondary text
- `--text-disabled`: Disabled text

**Component Colors:**
- `--input-bg`: Input backgrounds
- `--input-border`: Input borders
- `--code-bg`: Code block backgrounds
- `--hover-bg`: Hover backgrounds
- `--shadow`: Box shadows

## Theme Switching

Theme switching is handled by `js/theme.js`:

### JavaScript API

```javascript
// Get current theme
const theme = themeManager.getTheme(); // 'light' or 'dark'

// Set specific theme
themeManager.setTheme('dark');

// Toggle between themes
themeManager.toggleTheme();

// Reset to system preference
themeManager.resetToSystemTheme();
```

### Implementation Details

1. Theme preference is stored in `localStorage` under key `app-theme`
2. On load, the theme is applied immediately to prevent flash
3. System theme preference is detected via `prefers-color-scheme` media query
4. Theme changes are animated with a smooth transition
5. A custom `themechange` event is dispatched for components to react

### Keyboard Shortcut

- **Alt + T**: Toggle between light and dark themes

## Responsive Breakpoints

The layout adapts to different screen sizes:

### Small Screens (≤800px)
- Navigation tabs show only icons (text hidden)
- Single column layouts
- Reduced padding
- Stacked form layouts

### Medium Screens (800px - 1000px)
- Standard two-column layouts where appropriate
- Normal padding

### Large Screens (≥1400px)
- Maximum content width applied
- Increased spacing
- Optimal reading width maintained

## Component Styling

### Buttons

**Classes:**
- `.btn`: Base button style
- `.btn-primary`: Primary action (blue)
- `.btn-secondary`: Secondary action (gray)
- `.btn-success`: Success action (green)
- `.btn-danger`: Danger action (red)
- `.btn-large`: Larger button size
- `.icon-button`: Icon-only button (36x36px)

**Usage:**
```html
<button class="btn btn-primary">
    <svg class="btn-icon">...</svg>
    <span>Click Me</span>
</button>
```

### Forms

**Classes:**
- `.form-input`: Text inputs
- `.form-select`: Select dropdowns
- `.form-range`: Range sliders
- `.form-checkbox`: Checkboxes
- `.form-label`: Form labels
- `.error-message`: Validation errors

**Features:**
- Focus states with primary color outline
- Error states with red border
- Help icons with hover tooltips
- Validation error messages below fields

### Panels

**Classes:**
- `.panel`: Container for content sections
- `.panel-header`: Panel title and actions
- `.panel-content`: Scrollable content area
- `.panel-title`: Panel heading text
- `.panel-actions`: Action buttons in header

**Structure:**
```html
<div class="panel">
    <div class="panel-header">
        <h2 class="panel-title">Title</h2>
        <div class="panel-actions">
            <button>Action</button>
        </div>
    </div>
    <div class="panel-content">
        Content...
    </div>
</div>
```

### Progress Messages

**Classes:**
- `.progress-message`: Message container
- `.progress-message.info`: Informational message (blue)
- `.progress-message.success`: Success message (green)
- `.progress-message.warning`: Warning message (amber)
- `.progress-message.error`: Error message (red)

**Features:**
- Left border indicating message type
- Colored background with transparency
- Timestamp display
- Monospace font for code/log output

## Typography

### Font Families

**UI Text:**
```css
font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

**Code/Monospace:**
```css
font-family: "Fira Code", "Cascadia Code", "JetBrains Mono", "Source Code Pro", Consolas, monospace;
```

### Font Sizes

- Title: 1.5rem (24px)
- Heading: 1.125rem (18px)
- Body: 0.875rem (14px)
- Small: 0.75rem (12px)
- Code: 0.8125rem (13px)

### Line Heights

- Title: 1.2
- Heading: 1.3
- Body: 1.5
- Code: 1.6

## Spacing System

Based on a 4px unit:

- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px
- `2xl`: 48px

Applied consistently to:
- Padding
- Margins
- Gap (flexbox/grid)
- Border radius (6px = 1.5 units)

## Accessibility

### Focus Indicators

All interactive elements have visible focus indicators:
- 2px solid outline in primary color
- 2px offset from element
- Applied via `:focus-visible` for keyboard navigation only

### Color Contrast

All text meets WCAG AA standards:
- Light theme: Dark text on light backgrounds
- Dark theme: Light text on dark backgrounds
- Minimum contrast ratio of 4.5:1

### Screen Readers

- ARIA labels on all buttons and inputs
- Live regions for dynamic content updates
- Semantic HTML structure
- Proper heading hierarchy

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

CSS features used:
- CSS Grid
- CSS Custom Properties (variables)
- Flexbox
- Modern selectors (`:focus-visible`)

## Customization

To customize colors, edit the theme files:

1. Open `themes/light.css` or `themes/dark.css`
2. Modify CSS custom properties in the `:root` selector
3. Changes apply immediately when theme is active

Example:
```css
:root {
    --primary: #your-color-here;
    --primary-hover: #hover-color-here;
}
```

## Performance

### Optimizations

- GPU-accelerated animations (transform, opacity)
- Will-change hints on animated elements
- Efficient selectors (avoid deep nesting)
- Minimal repaints and reflows

### File Size

- main.css: ~18KB uncompressed
- light.css: ~4KB uncompressed
- dark.css: ~5KB uncompressed
- Total: ~27KB (compresses well with gzip)

## Testing

To test the styles:

1. Open the application
2. Toggle between light and dark themes
3. Resize window to test responsive breakpoints
4. Tab through interface to verify focus states
5. Test with screen reader for accessibility

## Future Enhancements

Potential improvements:

- Additional theme options (high contrast, colorblind-friendly)
- Custom theme builder UI
- CSS-in-JS for dynamic theming
- Animation preferences (respect `prefers-reduced-motion`)
- Print stylesheet optimization
