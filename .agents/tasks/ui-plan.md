# Implementation Plan: VS Code UI Redesign

## Overview
This plan transforms the Local AI Dev GUI to exactly match VS Code's modern, professional aesthetic. The current UI has a traditional header-navigation-content layout with rounded corners and a gradient-based color scheme. The VS Code design uses a distinctive left activity bar, sharp edges, flat colors, and the Dark+ theme palette.

## Project Context
- **Current Structure**: Eel-based desktop app with Python backend (src/gui/gui_app.py) and web frontend (src/web/)
- **Entry Point**: `eel.start('index.html', size=(1200, 800), port=8080, mode='chrome')`
- **Key Files**: index.html (structure), css/main.css (base layout), css/themes/dark.css (colors), js/main.js (routing/state)
- **Eel Functions**: Must preserve all `eel.` calls in JS components (run_task, stop_task, get_history, save_config, etc.)
- **Accessibility**: Must preserve sr-only elements, ARIA attributes, focus indicators, and keyboard shortcuts

## VS Code Color Scheme (Dark+)
```css
--background: #1e1e1e       /* Main editor background */
--sidebar-bg: #252526       /* Sidebar background */
--activitybar-bg: #333333   /* Activity bar (left edge) */
--titlebar-bg: #323233      /* Title bar */
--statusbar-bg: #007ACC     /* Status bar (blue) */
--input-bg: #3c3c3c         /* Input fields */
--border: #454545           /* Borders */
--text: #cccccc             /* Main text */
--text-muted: #858585       /* Secondary text */
--accent: #007ACC           /* Focus/active (blue) */
--success: #89d185          /* Success (green) */
--error: #f48771            /* Error (red) */
--warning: #cca700          /* Warning (yellow) */
```

## Implementation Plan

### Phase 1: Layout & Structure (Foundation)

- [x] 1. **Rewrite HTML structure with VS Code layout**
      Create the three-column layout: activity bar (48px fixed left), sidebar (300px resizable), main area (flex-1).
      Replace current header-navigation-content grid with: `<div class="vscode-layout">` containing `<aside class="activity-bar">`, `<aside class="sidebar">`, `<main class="editor-area">`, and `<footer class="status-bar">`.
      Move tab navigation from header into editor-area as editor tabs.
      Add activity bar with three icons: Task (play), History (clock), Settings (gear) - each is a button that controls sidebar content.
      Files: src/web/index.html
      Verify: Open index.html in browser - should see left activity bar, collapsible sidebar, main area, status bar at bottom

- [x] 2. **Create VS Code base CSS variables and layout grid**
      Replace existing CSS variables in :root with VS Code Dark+ colors (exact hex values above).
      Define `.vscode-layout` as CSS grid: `grid-template-columns: 48px 300px 1fr; grid-template-rows: 1fr 22px;`.
      Remove all border-radius (sharp corners), box-shadow (flat design), and gradient backgrounds.
      Update font stack: UI uses 'Segoe UI', system-ui; code uses 'Consolas', 'Monaco', monospace.
      Files: src/web/css/main.css, src/web/css/themes/dark.css
      Verify: Run `python src/gui/gui_app.py` - window opens, layout matches VS Code structure (no rounded corners/shadows)

- [x] 3. **Implement resizable sidebar splitter**
      Add draggable vertical splitter (1px border, #454545 color) between sidebar and editor-area.
      Use JS to handle mousedown on splitter, track mousemove, update sidebar width (min 200px, max 500px).
      Add CSS `.resizing` class that sets `cursor: col-resize` on body and `user-select: none`.
      Persist sidebar width to localStorage as 'vscode-sidebar-width'.
      Files: src/web/css/main.css, src/web/js/main.js
      Verify: Drag the splitter between sidebar and main area - sidebar resizes smoothly; refresh page - width is restored

### Phase 2: Component Styling (Match VS Code Exactly)

- [x] 4. **Restyle activity bar with icon-only buttons**
      Style `.activity-bar` with background #333333, 48px width, flex column layout.
      Each `.activity-item` button is 48px height, centered icon (24px SVG or Unicode), transparent background.
      Hover: lighten background by 10% (#3d3d3d). Active: 2px left border in #007ACC (accent blue).
      Replace emoji icons in HTML with proper SVG icons or Unicode symbols (▶ for task, 🕐 for history, ⚙ for settings).
      Files: src/web/index.html, src/web/css/main.css
      Verify: Hover activity bar icons - background lightens; click icon - 2px blue left border appears; matches VS Code exactly

- [x] 5. **Restyle sidebar with clean list view**
      Style `.sidebar` with background #252526, border-right 1px #454545.
      Add `.sidebar-header` (padding 16px 20px, border-bottom 1px #454545, text 13px bold #cccccc).
      Style list items (`.sidebar-item`) with padding 8px 20px, hover background #2a2a2b, active background #37373d + left border 2px #007ACC.
      Remove all rounded corners, shadows, and colored backgrounds from list items.
      Files: src/web/css/main.css
      Verify: Sidebar items have flat design, subtle hover, sharp left accent when selected - matches VS Code sidebar

- [x] 6. **Restyle editor tabs (top of main area)**
      Move tabs from header into `.editor-area` top. Style `.editor-tabs` as flex row, background #1e1e1e, border-bottom 1px #454545.
      Each `.editor-tab` is height 35px, padding 0 12px, text 13px #858585, transparent background.
      Hover: text changes to #cccccc. Active: text #ffffff, bottom border 2px #007ACC.
      Add close button (x) on each tab, right-aligned, 16px, visible on hover or when tab is active.
      Files: src/web/index.html, src/web/css/main.css
      Verify: Tabs look exactly like VS Code editor tabs - flat, bottom accent border, subtle hover, close button appears

- [x] 7. **Restyle all input fields and textareas**
      Update input, textarea, select with background #3c3c3c, border 1px #454545, color #cccccc, padding 6px 8px.
      Remove border-radius (or set to max 2px). Focus: border changes to #007ACC (accent), no box-shadow.
      Placeholder text color #858585.
      Apply to .task-textarea, all .form-input, .form-select, .search-input, .filter-select.
      Files: src/web/css/components/inputs.css
      Verify: Click into any input/textarea - border turns blue with no shadow; matches VS Code input styling

- [x] 8. **Restyle all buttons to match VS Code**
      Primary buttons (Run Task): background #007ACC, color #ffffff, border none, border-radius 2px, height 28px, padding 4px 14px.
      Hover: background #005a9e (slightly darker). No shadows or gradients.
      Secondary buttons: transparent background, border 1px #454545, color #cccccc. Hover: border #007ACC.
      Icon buttons: transparent, 28px square, color #858585. Hover: background #2a2a2b, color #cccccc.
      Remove all box-shadow, reduce border-radius to 2px max.
      Files: src/web/css/components/buttons.css
      Verify: All buttons match VS Code style - flat colors, sharp edges, subtle hover, no shadows

- [x] 9. **Create status bar with connection indicators**
      Style `.status-bar` with background #007ACC (blue), color #ffffff, height 22px, padding 0 12px, font-size 12px.
      Add flex row layout with items separated by | dividers (color rgba(255,255,255,0.5)).
      Display: LLM connection status (left), task status (center), version/info (right).
      Make text unselectable (user-select: none).
      Files: src/web/index.html, src/web/css/main.css
      Verify: Status bar at bottom is blue (#007ACC), white text, 22px height - matches VS Code exactly

### Phase 3: Views (Redesign Each View)

- [x] 10. **Redesign Task view with editor-style layout**
       Split Task view into top input area (40% height) and bottom output panel (60% height) with horizontal splitter.
       Style `.task-input-area` like VS Code editor: background #1e1e1e, padding 16px, monospace font.
       Style `.task-textarea` to fill area, background transparent, border none, color #cccccc, font 'Consolas' 14px, line-height 1.6.
       Add toolbar below textarea: Run/Stop buttons (left), character count (right), height 40px, background #252526, border-top 1px #454545.
       Style `.output-panel` with header "Output" and terminal-like output area (background #1e1e1e, monospace 13px).
       Files: src/web/index.html, src/web/css/main.css, src/web/js/components/task_input.js
       Verify: Task view looks like VS Code editor with integrated terminal - splitter is draggable, textarea is clean, output looks like terminal

- [x] 11. **Redesign History view with list + details panel**
       Split History view into left list (40% width) and right details panel (60% width) with vertical splitter.
       Style `.history-list` with alternating row backgrounds (#1e1e1e, #252526), no borders on items, padding 8px 16px.
       Each `.history-item` shows: timestamp (12px #858585) | description (13px #cccccc) | status badge (compact, flat colors).
       Selected item: background #37373d, left border 2px #007ACC.
       Style `.history-details` with sections: Task Description, Output (code block), Actions (buttons at bottom).
       Files: src/web/index.html, src/web/css/components/history.css, src/web/js/components/history.js
       Verify: History list looks like VS Code file explorer with alternating rows; details panel matches VS Code info panel

- [x] 12. **Redesign Settings view like VS Code settings**
       Style Settings as single-column form with section headers (20px top margin, 16px bold #cccccc, 1px border-bottom #454545).
       Each setting row: label above input (11px uppercase #858585, 4px bottom margin), input below (full width).
       Group settings into sections: LLM Settings, Project Settings, Feature Flags, GUI Settings.
       Style validation messages inline below inputs (12px #f48771 for errors, #89d185 for success).
       Add "Test Connection" button next to endpoint field with loading spinner on click.
       Save/Reset buttons: fixed to bottom-right corner of view, float above content.
       Files: src/web/index.html, src/web/css/main.css, src/web/js/components/settings.js
       Verify: Settings view matches VS Code settings - clean sections, labels above inputs, inline validation, floating action buttons

### Phase 4: Polish & Integration

- [x] 13. **Fine-tune all spacing and typography**
       Review all views against VS Code and adjust spacing: activity bar items (48px), tab height (35px), status bar (22px), sidebar padding (16px 20px).
       Ensure all text uses correct font sizes: UI labels 13px, code/output 13px-14px, status bar 12px, section headers 16px.
       Update line-height: UI text 1.5, code 1.6, compact areas 1.4.
       Adjust all padding/margin to match VS Code's tight but readable spacing.
       Files: src/web/css/main.css, all component CSS files
       Verify: Open each view and compare spacing/typography to VS Code screenshot - should be nearly identical

- [x] 14. **Implement smooth transitions matching VS Code**
       Set all transition durations: hover states 100ms, view changes 150ms, background changes 200ms.
       Remove any ease-in-out, use linear or ease for subtle transitions.
       Activity bar, sidebar, tabs: transition background-color 100ms ease.
       View transitions: crossfade with opacity 150ms linear.
       Keep GPU-accelerated properties (opacity, transform) for performance.
       Files: src/web/css/main.css, all component CSS files
       Verify: Hover any interactive element - transition is smooth and fast like VS Code; switch views - quick crossfade

- [x] 15. **Ensure all colors match VS Code Dark+ exactly**
       Audit every CSS file and replace any color not in the VS Code palette.
       Double-check: backgrounds (#1e1e1e, #252526, #333333), borders (#454545), text (#cccccc, #858585), accent (#007ACC).
       Update status badge colors: success #89d185, error #f48771, warning #cca700, info #007ACC.
       Remove any blue gradients, replace with flat #007ACC.
       Files: src/web/css/main.css, src/web/css/themes/dark.css, all component CSS files
       Verify: Use browser DevTools color picker on various elements - all colors match VS Code hex values exactly

- [x] 16. **Preserve all accessibility features**
       Verify all sr-only elements still present (skip links, announcements).
       Ensure ARIA attributes remain on all interactive elements (role, aria-selected, aria-controls, aria-label).
       Test focus indicators: all buttons, inputs, tabs should show 2px #007ACC outline on focus.
       Verify keyboard shortcuts still work: Ctrl+Enter to run, Ctrl+1/2/3 for views, Esc to close dialogs.
       Test with keyboard-only navigation: Tab through all controls, Enter to activate, arrow keys in lists.
       Files: src/web/css/accessibility.css, src/web/js/accessibility.js, verify in all HTML
       Verify: Tab through entire app without mouse - all interactive elements are focusable with visible indicator; screen reader announces view changes

- [x] 17. **Test all Eel integration points**
       Verify all eel.* calls still work: run_task(), stop_task(), get_history(), save_config(), get_config(), etc.
       Test Python backend communication: run a task and watch progress updates, load history entries, save settings.
       Check error handling: disconnect backend mid-operation, verify graceful fallback messages.
       Ensure exposed functions work: eel.expose(update_progress), task_completed callbacks.
       Files: src/web/js/components/*.js (task_input.js, progress_display.js, history.js, settings.js)
       Verify: Run `python src/gui/gui_app.py`, open app, execute a sample task - task runs and output appears; open Settings, change values, save - config persists; open History - entries load

- [x] 18. **Final integration test**
       Run the full application: `python src/gui/gui_app.py`
       Test complete workflow: enter task → run → watch output → check history → modify settings → save
       Verify responsive behavior: resize window, drag sidebar/panel splitters, toggle sidebar visibility
       Check dark theme consistency: all views should use Dark+ colors, no light theme artifacts
       Compare final result to VS Code side-by-side: layout, colors, spacing, interactions should be nearly indistinguishable
       Files: all files modified in previous steps
       Verify: Application launches, all features work, UI matches VS Code in every view - ready for user review

## Key Constraints

1. **DO NOT modify Python backend files** (src/gui/gui_app.py, src/**/*.py except web/*)
2. **Preserve all Eel function calls** - every `eel.run_task()`, `eel.get_config()`, etc. must remain functional
3. **Maintain accessibility** - all sr-only content, ARIA attributes, focus indicators, keyboard shortcuts must work
4. **Test command**: `python src/gui/gui_app.py` (launches Eel app on port 8080, opens in Chrome app mode)

## Files Modified

### HTML Structure
- src/web/index.html (complete restructure for VS Code layout)

### CSS - Core
- src/web/css/main.css (base layout, grid, spacing, typography)
- src/web/css/themes/dark.css (VS Code Dark+ color variables)

### CSS - Components  
- src/web/css/components/buttons.css (flat buttons, no shadows)
- src/web/css/components/inputs.css (VS Code input styling)
- src/web/css/components/panels.css (editor panels, sidebar)
- src/web/css/accessibility.css (preserve focus styles, update colors)

### JavaScript
- src/web/js/main.js (add splitter logic, activity bar switching, preserve all Eel calls)
- src/web/js/components/task_input.js (update for new layout, preserve Eel calls)
- src/web/js/components/history.js (update for two-panel layout, preserve Eel calls)
- src/web/js/components/settings.js (update for VS Code settings style, preserve Eel calls)

### Assets (if needed)
- src/web/assets/icons/ (may need SVG icons for activity bar)

## Success Criteria

1. Application launches with `python src/gui/gui_app.py`
2. Layout matches VS Code: 48px activity bar left, resizable sidebar, editor tabs top, 22px status bar bottom
3. All colors exactly match VS Code Dark+ (no rounded corners, no shadows, no gradients)
4. All functionality works: run tasks, view history, modify settings
5. All Eel backend communication works (tasks execute, history loads, settings save)
6. Accessibility features intact (keyboard navigation, screen reader support, focus indicators)
7. Side-by-side comparison with VS Code shows nearly identical appearance

## Notes

- This is a pure UI redesign - all Python backend code remains unchanged
- Focus is on visual fidelity to VS Code Dark+ theme
- The goal is to make the app indistinguishable from VS Code at first glance
- Component functionality (task execution, history, settings) must continue working exactly as before
