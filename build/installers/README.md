# Desktop GUI Application Installers

This directory contains installer configuration files and scripts for creating platform-specific installers for the Local AI Development Environment Desktop GUI Application.

## Overview

The installer scripts create native installation packages for:
- **Windows**: NSIS installer (.exe)
- **macOS**: PKG installer and DMG disk image
- **Linux**: AppImage (universal) and .deb package (Debian/Ubuntu)

## Requirements Implemented

- **Requirement 8.7**: Create installer with desktop shortcut and Start menu entry
- **Requirement 7.5**: Set application icon for shortcuts
- **Requirement 7.6**: Set Info.plist with version and icon (macOS)
- **Requirement 8.9**: Code sign if certificate available (macOS)
- **Requirement 15.2**: Support macOS 10.14 (Mojave) and newer
- **Requirement 15.3**: Support Linux distributions with GTK 3.0 or newer

## Prerequisites

Before building installers, ensure:

1. **PyInstaller build is complete**:
   ```bash
   pyinstaller build/pyinstaller/local-ai-dev.spec
   ```
   This creates: `dist/LocalAIDev/` (Windows/Linux) or `dist/LocalAIDev.app` (macOS)

2. **Icon files exist**:
   - Windows: `src/web/assets/icon.ico`
   - macOS: `src/web/assets/icon.icns`
   - Linux: `src/web/assets/icon-{size}x{size}.png` (multiple sizes)

3. **Platform-specific tools** (see sections below)

## Windows Installer (NSIS)

### Requirements

- NSIS 3.0 or later: https://nsis.sourceforge.io/Download
- Windows 10 or later

### Building

```bash
# Install NSIS first, then:
makensis build/installers/windows.nsi
```

### Output

- `dist/LocalAIDev-Setup.exe` (~80-120MB compressed)

### Features

- Creates desktop shortcut (optional, user choice)
- Creates Start menu entry
- Adds to Programs & Features (uninstaller)
- Checks for existing installation
- Custom application icon
- Professional installer UI

### Testing

1. Run `dist/LocalAIDev-Setup.exe`
2. Follow installation wizard
3. Verify desktop shortcut created (if selected)
4. Verify Start menu entry: Start > Local AI Development Environment
5. Launch application
6. Test uninstaller: Settings > Apps > Local AI Development Environment > Uninstall

### Code Signing (Optional)

For production releases, sign the installer:

```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/LocalAIDev-Setup.exe
```

### Customization

Edit `windows.nsi`:
- `PRODUCT_WEB_SITE`: Your website URL
- `PRODUCT_PUBLISHER`: Your organization name
- `MUI_WELCOMEFINISHPAGE_BITMAP`: Custom installer graphics

## macOS Installer (PKG and DMG)

### Requirements

- macOS 10.14 or later
- Xcode Command Line Tools: `xcode-select --install`
- pkgbuild and productbuild (included with Xcode)
- (Optional) create-dmg: `brew install create-dmg`
- (Optional) Apple Developer certificate for code signing

### Building

```bash
bash build/installers/macos-installer.sh
```

### Output

- `dist/LocalAIDev.pkg` - Installer package
- `dist/LocalAIDev.dmg` - Distributable disk image (if create-dmg installed)

### Features

- Installs to /Applications folder
- Professional installer UI with welcome/license/conclusion pages
- Version checking (minimum macOS 10.14)
- Code signing support (if certificate configured)
- Notarization support (for distribution)

### Testing

1. **Install from PKG**:
   ```bash
   sudo installer -pkg dist/LocalAIDev.pkg -target /
   ```

2. **Or mount DMG**:
   ```bash
   open dist/LocalAIDev.dmg
   # Drag app to Applications folder
   ```

3. Verify in Applications folder
4. Launch: `open /Applications/LocalAIDev.app`
5. Check in Spotlight search

### Code Signing (Recommended)

1. Get Apple Developer certificate
2. Edit `macos-installer.sh`:
   ```bash
   SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
   INSTALLER_SIGNING_IDENTITY="Developer ID Installer: Your Name (TEAM_ID)"
   ```

3. Rebuild

Verify signature:
```bash
codesign --verify --deep --strict --verbose=2 /Applications/LocalAIDev.app
spctl --assess --type execute --verbose=4 /Applications/LocalAIDev.app
```

### Notarization (For Distribution)

1. Edit `macos-installer.sh`:
   ```bash
   NOTARIZE=true
   APPLE_ID="your@email.com"
   APPLE_ID_PASSWORD="app-specific-password"
   TEAM_ID="YOUR_TEAM_ID"
   ```

2. Rebuild - notarization happens automatically

### Customization

- Edit `macos-installer.sh` for version, URLs, etc.
- Create `dmg-background.png` (600x400) for custom DMG background
- Edit `macos-component.plist` for advanced installation options

## Linux Packages (AppImage and .deb)

### Requirements

#### For AppImage:
- appimagetool: 
  ```bash
  wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x appimagetool-x86_64.AppImage
  sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
  ```

#### For .deb:
- dpkg-dev: `sudo apt-get install dpkg-dev`
- (Optional) lintian: `sudo apt-get install lintian`

### Building

```bash
# Build both AppImage and .deb:
bash build/installers/linux-installer.sh all

# Or build individually:
bash build/installers/linux-installer.sh appimage
bash build/installers/linux-installer.sh deb
```

### Output

- `dist/LocalAIDev-x86_64.AppImage` - Universal Linux package
- `dist/localaidev_1.0.0_amd64.deb` - Debian/Ubuntu package

### Features

#### AppImage:
- Universal Linux binary - runs on most distributions
- No installation required
- Self-contained with all dependencies
- Desktop integration (registers .desktop entry)

#### .deb Package:
- Native Debian/Ubuntu integration
- Installs to /opt/LocalAIDev
- Creates symlink in /usr/bin
- Registers desktop entry
- Updates icon cache
- Proper dependency management

### Testing

#### AppImage:
```bash
# Make executable
chmod +x dist/LocalAIDev-x86_64.AppImage

# Run directly
./dist/LocalAIDev-x86_64.AppImage

# Or integrate with system (if aisap installed)
aisap register dist/LocalAIDev-x86_64.AppImage
```

#### .deb Package:
```bash
# Install
sudo dpkg -i dist/localaidev_1.0.0_amd64.deb

# Fix dependencies if needed
sudo apt-get install -f

# Launch
localaidev
# Or from application menu: Search for "Local AI Development Environment"

# Remove
sudo apt remove localaidev
```

### Customization

- Edit `linux-installer.sh` for version, descriptions, etc.
- Edit `linux.desktop` for desktop entry customization
- Add dependencies in .deb control file (in script)

### Desktop Entry

The `linux.desktop` file provides:
- Application menu entry
- Icon integration
- Keyboard shortcuts registration
- MIME type associations (if needed)
- Right-click actions

Manual installation of .desktop file:
```bash
# System-wide (requires root)
sudo cp build/installers/linux.desktop /usr/share/applications/localaidev.desktop
sudo update-desktop-database /usr/share/applications

# User-specific
mkdir -p ~/.local/share/applications
cp build/installers/linux.desktop ~/.local/share/applications/localaidev.desktop
update-desktop-database ~/.local/share/applications
```

## File Structure

```
build/installers/
├── README.md                          # This file
├── windows.nsi                        # NSIS installer script
├── macos-installer.sh                 # macOS PKG/DMG creation script
├── macos-component.plist              # macOS component configuration
├── dmg-background-instructions.md     # Guide for DMG background image
├── linux-installer.sh                 # Linux AppImage/.deb creation script
└── linux.desktop                      # Linux desktop entry file
```

## Distribution Checklist

Before distributing installers:

### All Platforms
- [ ] Test installation on clean system
- [ ] Test application launches correctly
- [ ] Verify all features work
- [ ] Test uninstallation/removal
- [ ] Check file size (target: <150MB per Requirement 8.5)

### Windows
- [ ] Installer creates desktop shortcut
- [ ] Start menu entry exists
- [ ] Application icon shows in taskbar
- [ ] Uninstaller removes all files
- [ ] (Production) Code sign the installer

### macOS
- [ ] App installs to /Applications
- [ ] App appears in Spotlight
- [ ] Icon shows in Dock
- [ ] (Production) Code sign and notarize

### Linux
- [ ] AppImage runs without installation
- [ ] .deb installs correctly
- [ ] Desktop entry appears in application menu
- [ ] Icons display correctly
- [ ] Symlink works: `localaidev` command

## Troubleshooting

### Windows

**Error: "Can't open file"**
- Ensure PyInstaller build completed: check `dist/LocalAIDev/` exists
- Verify NSIS can find the dist folder

**Installer too large**
- Check PyInstaller output size first
- Optimize PyInstaller excludes in `local-ai-dev.spec`

### macOS

**Code signing fails**
- Verify certificate: `security find-identity -v -p codesigning`
- Ensure certificate is valid and not expired
- Check certificate trust settings

**Notarization fails**
- Verify Apple ID credentials
- Check app-specific password is correct
- Ensure hardened runtime enabled

### Linux

**AppImage doesn't run**
- Make executable: `chmod +x LocalAIDev-x86_64.AppImage`
- Try with terminal to see error: `./LocalAIDev-x86_64.AppImage`
- Check FUSE is installed: `sudo apt-get install fuse`

**.deb installation fails**
- Check dependencies: `sudo apt-get install -f`
- Verify package: `dpkg-deb --info localaidev_1.0.0_amd64.deb`
- Check lintian output for issues

## Version Updates

When releasing a new version:

1. Update version in all scripts:
   - `windows.nsi`: `PRODUCT_VERSION`
   - `macos-installer.sh`: `APP_VERSION`
   - `linux-installer.sh`: `APP_VERSION`

2. Update PyInstaller spec: `build/pyinstaller/local-ai-dev.spec`

3. Rebuild PyInstaller bundle

4. Rebuild all installers

5. Test on each platform

## Support

For issues with installer creation:
- Check platform-specific documentation linked above
- Review error messages carefully
- Test PyInstaller build first (most issues are here)
- Ensure all prerequisites are installed

## License

These installer scripts are part of the Local AI Development Environment project.
See LICENSE file in project root.
