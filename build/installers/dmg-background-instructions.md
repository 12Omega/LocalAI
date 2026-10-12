# DMG Background Image

For a professional-looking macOS disk image (.dmg), you can create a custom background image.

## Specifications

- **Size**: 600x400 pixels (matching the DMG window size in macos-installer.sh)
- **Format**: PNG with transparency support
- **File name**: `dmg-background.png`
- **Location**: Place in `build/installers/` directory

## Content Suggestions

The background image typically includes:
- Application logo or icon (centered or top)
- Visual arrow from app icon to Applications folder
- Subtle gradient or texture
- Brand colors consistent with the application

## Design Tips

1. Keep it simple - too busy backgrounds make icons hard to read
2. Use light colors or subtle patterns
3. Ensure good contrast with icon labels (black text)
4. Test with both light and dark macOS appearances

## Creating the Image

You can use any image editor:
- **macOS**: Preview, Pixelmator, Affinity Designer
- **Cross-platform**: GIMP, Photoshop, Figma, Sketch

## Example Layout

```
┌─────────────────────────────────────────────────────┐
│                                                       │
│                  [Company Logo]                       │
│                                                       │
│     [App Icon]  ────────────→  [Applications]        │
│     (150, 190)                       (450, 190)      │
│                                                       │
│         Drag the app to Applications to install      │
│                                                       │
└─────────────────────────────────────────────────────┘
```

## If No Custom Background

If you don't create `dmg-background.png`, the installer script will still work.
The create-dmg tool will use a plain white background instead.

To disable background image in the script:
1. Open `macos-installer.sh`
2. Remove the `--background` line from the `create-dmg` command
