# Typography and Spacing System Guide

This document provides comprehensive guidance on using the typography and spacing system for the Local AI Development Environment Desktop GUI Application.

## Overview

The typography and spacing system is implemented using CSS custom properties (variables) defined in `main.css`. This ensures consistency across all components and makes it easy to maintain and update the design system.

## Spacing System

### Base Unit

The spacing system uses a **4px base unit** for consistent spacing throughout the application.

### Spacing Scale

```css
:root {
    --spacing-xs: 0.25rem;   /* 4px  - Extra small */
    --spacing-sm: 0.5rem;    /* 8px  - Small */
    --spacing-md: 0.75rem;   /* 12px - Medium */
    --spacing-lg: 1rem;      /* 16px - Large */
    --spacing-xl: 1.5rem;    /* 24px - Extra large */
    --spacing-2xl: 2rem;     /* 32px - 2X large */
}
```

### Usage Examples

#### Padding

```css
/* Button padding */
.btn {
    padding: var(--spacing-sm) var(--spacing-lg); /* 8px 16px */
}

/* Panel padding */
.panel-content {
    padding: var(--spacing-lg); /* 16px on all sides */
}

/* Compact padding */
.compact-element {
    padding: var(--spacing-xs) var(--spacing-sm); /* 4px 8px */
}
```

#### Margin

```css
/* Standard bottom margin */
.form-group {
    margin-bottom: var(--spacing-lg); /* 16px */
}

/* Small gap between items */
.item {
    margin-bottom: var(--spacing-sm); /* 8px */
}

/* Large section spacing */
.section {
    margin-bottom: var(--spacing-2xl); /* 32px */
}
```

#### Gap (Flexbox/Grid)

```css
/* Standard gap */
.flex-container {
    display: flex;
    gap: var(--spacing-md); /* 12px */
}

/* Small gap */
.button-group {
    display: flex;
    gap: var(--spacing-sm); /* 8px */
}

/* Large gap */
.grid-layout {
    display: grid;
    gap: var(--spacing-xl); /* 24px */
}
```

### Spacing Guidelines

1. **Consistency**: Always use spacing variables instead of hard-coded values
2. **Scale Selection**:
   - `xs` (4px): Very tight spacing, icon padding, minor adjustments
   - `sm` (8px): Compact elements, small gaps, tight buttons
   - `md` (12px): Default gap between related items
   - `lg` (16px): Standard padding, default margin between groups
   - `xl` (24px): Section spacing, panel padding
   - `2xl` (32px): Large section breaks, major layout spacing

## Typography System

### Font Families

```css
:root {
    /* System UI fonts for general text */
    --font-family-base: system-ui, -apple-system, BlinkMacSystemFont, 
                        "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    
    /* Monospace fonts for code and technical content */
    --font-family-mono: "Fira Code", "Cascadia Code", "JetBrains Mono", 
                        "Source Code Pro", Consolas, "Courier New", monospace;
}
```

### Font Sizes

```css
:root {
    --font-size-xs: 0.75rem;      /* 12px - Extra small text */
    --font-size-sm: 0.8125rem;    /* 13px - Small text (code) */
    --font-size-base: 0.875rem;   /* 14px - Body text */
    --font-size-md: 1rem;         /* 16px - Medium text */
    --font-size-lg: 1.125rem;     /* 18px - Headings */
    --font-size-xl: 1.25rem;      /* 20px - Large headings */
    --font-size-2xl: 1.5rem;      /* 24px - Page titles */
}
```

### Line Heights

```css
:root {
    --line-height-tight: 1.2;     /* For titles and headings */
    --line-height-normal: 1.5;    /* For body text */
    --line-height-relaxed: 1.6;   /* For code and long-form text */
}
```

### Typography Usage Examples

#### Headings

```css
h1 {
    font-size: var(--font-size-2xl);      /* 24px - Title */
    line-height: var(--line-height-tight); /* 1.2 */
    font-weight: 600;
}

h2 {
    font-size: var(--font-size-lg);       /* 18px - Heading */
    line-height: var(--line-height-tight); /* 1.2 */
    font-weight: 600;
}

h3 {
    font-size: var(--font-size-md);       /* 16px */
    line-height: var(--line-height-tight); /* 1.2 */
    font-weight: 600;
}
```

#### Body Text

```css
body {
    font-family: var(--font-family-base);
    font-size: var(--font-size-base);      /* 14px */
    line-height: var(--line-height-normal); /* 1.5 */
}

/* Small text variant */
.text-small {
    font-size: var(--font-size-sm); /* 13px */
}

/* Extra small text */
.text-xs {
    font-size: var(--font-size-xs); /* 12px */
}
```

#### Code and Monospace

```css
code, pre {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);         /* 13px */
    line-height: var(--line-height-relaxed); /* 1.6 */
}

/* Progress output */
.progress-output {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
}
```

### Typography Guidelines

1. **Font Family Selection**:
   - Use `var(--font-family-base)` for all UI text
   - Use `var(--font-family-mono)` for code, logs, and technical output

2. **Font Size Selection**:
   - `xs` (12px): Metadata, timestamps, helper text
   - `sm` (13px): Code, small UI text
   - `base` (14px): Body text, buttons, inputs (DEFAULT)
   - `md` (16px): Section titles, emphasized text
   - `lg` (18px): Page section headings
   - `xl` (20px): Large headings
   - `2xl` (24px): Page titles, main headings

3. **Line Height Selection**:
   - `tight` (1.2): Titles and headings (reduce vertical space)
   - `normal` (1.5): Body text (comfortable reading)
   - `relaxed` (1.6): Code blocks (easier to scan)

4. **Font Weight**:
   - 400: Regular body text
   - 500: Buttons, labels, emphasized text
   - 600: Headings, titles

## Component-Specific Examples

### Buttons

```css
.btn {
    padding: var(--spacing-sm) var(--spacing-lg);  /* 8px 16px */
    font-size: var(--font-size-base);               /* 14px */
    font-family: var(--font-family-base);
    gap: var(--spacing-sm);                         /* 8px between icon and text */
}

.btn-small {
    padding: var(--spacing-xs) var(--spacing-md);   /* 4px 12px */
    font-size: var(--font-size-xs);                 /* 12px */
}

.btn-large {
    padding: var(--spacing-md) var(--spacing-xl);   /* 12px 24px */
    font-size: var(--font-size-md);                 /* 16px */
}
```

### Form Inputs

```css
.form-input {
    padding: var(--spacing-sm) var(--spacing-md);   /* 8px 12px */
    font-size: var(--font-size-base);               /* 14px */
    font-family: var(--font-family-base);
    line-height: var(--line-height-normal);         /* 1.5 */
}

.form-label {
    font-size: var(--font-size-base);               /* 14px */
    margin-bottom: var(--spacing-sm);               /* 8px */
}

.error-message {
    font-size: var(--font-size-xs);                 /* 12px */
    margin-top: var(--spacing-xs);                  /* 4px */
}
```

### Panels

```css
.panel-header {
    padding: var(--spacing-lg);                     /* 16px */
}

.panel-title {
    font-size: var(--font-size-lg);                 /* 18px */
    line-height: var(--line-height-tight);          /* 1.2 */
}

.panel-content {
    padding: var(--spacing-lg);                     /* 16px */
}

.panel-actions {
    gap: var(--spacing-sm);                         /* 8px */
}
```

### Progress Display

```css
.progress-message {
    padding: var(--spacing-sm);                     /* 8px */
    margin-bottom: var(--spacing-sm);               /* 8px */
    gap: var(--spacing-md);                         /* 12px */
}

.message-content {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);                 /* 13px */
    line-height: var(--line-height-relaxed);        /* 1.6 */
}

.message-timestamp {
    font-size: var(--font-size-xs);                 /* 12px */
}
```

## Responsive Adjustments

The typography and spacing system adapts to different screen sizes:

```css
/* Mobile devices (< 800px) */
@media (max-width: 800px) {
    /* Slightly reduce spacing for compact screens */
    .view-container {
        padding: var(--spacing-lg);  /* 16px instead of 24px */
    }
    
    /* Reduce font sizes slightly */
    .btn {
        font-size: var(--font-size-sm);  /* 13px instead of 14px */
    }
    
    /* iOS requires 16px minimum to prevent zoom */
    .form-input {
        font-size: 16px;
    }
}

/* Large screens (> 1400px) */
@media (min-width: 1400px) {
    /* Increase spacing for more breathing room */
    .view-container {
        padding: var(--spacing-2xl);  /* 32px instead of 24px */
    }
}
```

## Best Practices

### DO ✅

1. **Always use CSS variables**:
   ```css
   .element {
       padding: var(--spacing-lg);
       font-size: var(--font-size-base);
   }
   ```

2. **Use semantic spacing choices**:
   ```css
   /* Good: Semantic spacing for related items */
   .button-group {
       gap: var(--spacing-sm);
   }
   ```

3. **Maintain consistency**:
   ```css
   /* All panels use the same padding */
   .panel-content {
       padding: var(--spacing-lg);
   }
   ```

4. **Combine spacing variables logically**:
   ```css
   .element {
       padding: var(--spacing-sm) var(--spacing-lg); /* Vertical: 8px, Horizontal: 16px */
   }
   ```

### DON'T ❌

1. **Don't use hard-coded pixel values**:
   ```css
   /* Bad */
   .element {
       padding: 12px;
   }
   
   /* Good */
   .element {
       padding: var(--spacing-md);
   }
   ```

2. **Don't use arbitrary font sizes**:
   ```css
   /* Bad */
   .element {
       font-size: 15px;
   }
   
   /* Good */
   .element {
       font-size: var(--font-size-base);
   }
   ```

3. **Don't mix units unnecessarily**:
   ```css
   /* Bad */
   .element {
       padding: var(--spacing-lg) 20px;
   }
   
   /* Good */
   .element {
       padding: var(--spacing-lg) var(--spacing-xl);
   }
   ```

4. **Don't create custom spacing scales**:
   ```css
   /* Bad */
   .element {
       margin: calc(var(--spacing-sm) * 1.5);
   }
   
   /* Good - use the closest predefined size */
   .element {
       margin: var(--spacing-md);
   }
   ```

## Quick Reference

### Spacing Quick Reference

| Variable | Size | Use Case |
|----------|------|----------|
| `--spacing-xs` | 4px | Icon padding, fine adjustments |
| `--spacing-sm` | 8px | Small gaps, compact buttons |
| `--spacing-md` | 12px | Default gaps, input padding |
| `--spacing-lg` | 16px | Panel padding, section margins |
| `--spacing-xl` | 24px | Large sections, view padding |
| `--spacing-2xl` | 32px | Major layout breaks |

### Typography Quick Reference

| Variable | Size | Use Case |
|----------|------|----------|
| `--font-size-xs` | 12px | Timestamps, metadata |
| `--font-size-sm` | 13px | Code, small UI text |
| `--font-size-base` | 14px | Body text (default) |
| `--font-size-md` | 16px | Section titles |
| `--font-size-lg` | 18px | Headings |
| `--font-size-xl` | 20px | Large headings |
| `--font-size-2xl` | 24px | Page titles |

### Line Height Quick Reference

| Variable | Value | Use Case |
|----------|-------|----------|
| `--line-height-tight` | 1.2 | Titles, headings |
| `--line-height-normal` | 1.5 | Body text |
| `--line-height-relaxed` | 1.6 | Code blocks |

## Testing Your Implementation

When implementing new components, verify:

1. ✅ All spacing uses CSS variables (no hard-coded px values)
2. ✅ All font sizes use CSS variables
3. ✅ Font family matches content type (base vs mono)
4. ✅ Line heights are appropriate for content type
5. ✅ Spacing is consistent with similar components
6. ✅ Component works at different screen sizes
7. ✅ Text is readable at all sizes (14px minimum for body text)

## Accessibility Considerations

1. **Minimum font size**: Body text should not be smaller than 14px (var(--font-size-base))
2. **Line height**: Maintain at least 1.5 for body text for readability
3. **Touch targets**: Interactive elements should have at least 44x44px area (use padding)
4. **Color contrast**: Ensure text meets WCAG AA standards (handled by theme colors)
5. **Responsive text**: On mobile, inputs should be 16px to prevent iOS zoom

## Maintenance

When updating the spacing or typography system:

1. **Update main.css** first (the source of truth)
2. **Test across all components** to ensure consistency
3. **Update this guide** with any new patterns or guidelines
4. **Communicate changes** to the development team
5. **Check responsive behavior** at all breakpoints

## Related Files

- `/src/web/css/main.css` - Main stylesheet with CSS variables
- `/src/web/css/components/buttons.css` - Button components
- `/src/web/css/components/inputs.css` - Input components
- `/src/web/css/components/progress.css` - Progress display
- `/src/web/css/themes/light.css` - Light theme colors
- `/src/web/css/themes/dark.css` - Dark theme colors
