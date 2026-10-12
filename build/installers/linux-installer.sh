#!/bin/bash
# ==============================================================================
# Linux Installer Creation Script for Local AI Development Environment
# ==============================================================================
#
# This script creates Linux distribution packages (AppImage and .deb) for the
# Local AI Development Environment Desktop GUI Application.
#
# Requirements implemented:
# - 8.7: Create AppImage or .deb package configuration
# - 7.5: Add application icon to standard locations
# - 15.3: Support Linux distributions with GTK 3.0 or newer
#
# Prerequisites:
# - PyInstaller-built executable in dist/LocalAIDev/
# - appimagetool (for AppImage): https://github.com/AppImage/AppImageKit
# - dpkg-deb (for .deb, usually pre-installed on Debian-based systems)
#
# Usage:
#   bash build/installers/linux-installer.sh [appimage|deb|all]
#
# Output:
#   dist/LocalAIDev-x86_64.AppImage  - Universal Linux package
#   dist/localaidev_1.0.0_amd64.deb  - Debian package
#
# ==============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# ==============================================================================
# Configuration
# ==============================================================================

# Application information
APP_NAME="LocalAIDev"
APP_DISPLAY_NAME="Local AI Development Environment"
APP_VERSION="1.0.0"
APP_DESCRIPTION="Modern desktop GUI for AI-powered development environment"
APP_AUTHOR="Local AI Dev Team"
APP_MAINTAINER="Local AI Dev Team <dev@localaidev.com>"
APP_WEBSITE="https://github.com/yourusername/local-ai-dev"
APP_LICENSE="MIT"
DESKTOP_CATEGORIES="Development;IDE;Utility;"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build/linux-packages"
PYINSTALLER_DIST="$DIST_DIR/$APP_NAME"

# Output files
APPIMAGE_FILE="$DIST_DIR/${APP_NAME}-x86_64.AppImage"
DEB_FILE="$DIST_DIR/localaidev_${APP_VERSION}_amd64.deb"

# Build mode (default: all)
BUILD_MODE="${1:-all}"

# ==============================================================================
# Colors for output
# ==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_warning "$1 is not installed or not in PATH"
        return 1
    fi
    return 0
}

# ==============================================================================
# Validation
# ==============================================================================

log_info "Starting Linux package creation for $APP_DISPLAY_NAME v$APP_VERSION"
log_info "Build mode: $BUILD_MODE"

# Check if PyInstaller output exists
if [ ! -d "$PYINSTALLER_DIST" ]; then
    log_error "PyInstaller output not found at $PYINSTALLER_DIST"
    log_info "Please run PyInstaller first: pyinstaller build/pyinstaller/local-ai-dev.spec"
    exit 1
fi

# Check if executable exists
if [ ! -f "$PYINSTALLER_DIST/$APP_NAME" ]; then
    log_error "Executable not found: $PYINSTALLER_DIST/$APP_NAME"
    exit 1
fi

# Create build directory
mkdir -p "$BUILD_DIR"

# ==============================================================================
# Prepare Icon Files
# ==============================================================================

prepare_icons() {
    log_info "Preparing icon files..."
    
    ICON_SOURCE="$PROJECT_ROOT/src/web/assets"
    ICON_BUILD="$BUILD_DIR/icons"
    mkdir -p "$ICON_BUILD"
    
    # Icon sizes for Linux (freedesktop.org specification)
    ICON_SIZES="16 22 24 32 48 64 128 256 512"
    
    for size in $ICON_SIZES; do
        local icon_file="$ICON_SOURCE/icon-${size}x${size}.png"
        if [ -f "$icon_file" ]; then
            mkdir -p "$ICON_BUILD/${size}x${size}/apps"
            cp "$icon_file" "$ICON_BUILD/${size}x${size}/apps/localaidev.png"
        else
            log_warning "Icon not found: $icon_file"
        fi
    done
    
    # Use 256x256 as the main icon if available
    if [ -f "$ICON_SOURCE/icon-256x256.png" ]; then
        cp "$ICON_SOURCE/icon-256x256.png" "$ICON_BUILD/localaidev.png"
    elif [ -f "$ICON_SOURCE/icon.png" ]; then
        cp "$ICON_SOURCE/icon.png" "$ICON_BUILD/localaidev.png"
    else
        log_warning "No main icon found"
    fi
    
    log_success "Icons prepared"
}

# ==============================================================================
# Create AppImage
# ==============================================================================

create_appimage() {
    log_info "Creating AppImage..."
    
    # Check for appimagetool
    if ! check_command appimagetool; then
        log_error "appimagetool not found. Please install it:"
        log_info "  wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        log_info "  chmod +x appimagetool-x86_64.AppImage"
        log_info "  sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool"
        return 1
    fi
    
    # Create AppDir structure
    APPDIR="$BUILD_DIR/AppDir"
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr/bin"
    mkdir -p "$APPDIR/usr/lib"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor"
    mkdir -p "$APPDIR/usr/share/metainfo"
    
    # Copy application files
    log_info "Copying application files to AppDir..."
    cp -r "$PYINSTALLER_DIST"/* "$APPDIR/usr/bin/"
    
    # Make executable
    chmod +x "$APPDIR/usr/bin/$APP_NAME"
    
    # Copy desktop entry
    cat > "$APPDIR/usr/share/applications/localaidev.desktop" << EOF
[Desktop Entry]
Type=Application
Version=1.5
Name=$APP_DISPLAY_NAME
GenericName=AI Development Tool
Comment=$APP_DESCRIPTION
Exec=$APP_NAME %U
Icon=localaidev
Terminal=false
Categories=$DESKTOP_CATEGORIES
Keywords=ai;development;coding;llm;
StartupNotify=true
EOF
    
    # Create AppRun script
    cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
# AppRun script for AppImage

SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Export library paths
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PATH="${HERE}/usr/bin:${PATH}"

# Change to user's home directory to avoid permission issues
cd "$HOME"

# Execute the application
exec "${HERE}/usr/bin/LocalAIDev" "$@"
EOF
    
    chmod +x "$APPDIR/AppRun"
    
    # Copy icons
    log_info "Copying icons..."
    if [ -d "$ICON_BUILD" ]; then
        for size_dir in "$ICON_BUILD"/*/; do
            if [ -d "$size_dir" ]; then
                size=$(basename "$size_dir")
                mkdir -p "$APPDIR/usr/share/icons/hicolor/$size"
                cp -r "$size_dir"/* "$APPDIR/usr/share/icons/hicolor/$size/"
            fi
        done
        
        # Copy main icon
        if [ -f "$ICON_BUILD/localaidev.png" ]; then
            cp "$ICON_BUILD/localaidev.png" "$APPDIR/localaidev.png"
            cp "$ICON_BUILD/localaidev.png" "$APPDIR/.DirIcon"
        fi
    fi
    
    # Create .desktop file in root (required for AppImage)
    cp "$APPDIR/usr/share/applications/localaidev.desktop" "$APPDIR/localaidev.desktop"
    
    # Create AppStream metadata
    cat > "$APPDIR/usr/share/metainfo/localaidev.appdata.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.localaidev.LocalAIDev</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>$APP_LICENSE</project_license>
  <name>$APP_DISPLAY_NAME</name>
  <summary>$APP_DESCRIPTION</summary>
  <description>
    <p>
      Local AI Development Environment provides a modern desktop GUI that wraps
      AI-powered development tools. It allows users to interact with local LLMs
      for code generation, refactoring, and development tasks.
    </p>
    <p>Features:</p>
    <ul>
      <li>Task-based interface for AI development requests</li>
      <li>Real-time progress monitoring</li>
      <li>Configuration management</li>
      <li>Task history tracking</li>
      <li>Cross-platform support</li>
    </ul>
  </description>
  <url type="homepage">$APP_WEBSITE</url>
  <launchable type="desktop-id">localaidev.desktop</launchable>
  <provides>
    <binary>LocalAIDev</binary>
  </provides>
  <releases>
    <release version="$APP_VERSION" date="$(date +%Y-%m-%d)"/>
  </releases>
</component>
EOF
    
    # Build AppImage
    log_info "Building AppImage with appimagetool..."
    
    # Remove old AppImage
    [ -f "$APPIMAGE_FILE" ] && rm "$APPIMAGE_FILE"
    
    # Set architecture
    export ARCH=x86_64
    
    # Build
    appimagetool "$APPDIR" "$APPIMAGE_FILE"
    
    # Make executable
    chmod +x "$APPIMAGE_FILE"
    
    log_success "AppImage created: $APPIMAGE_FILE"
    
    # Get size
    SIZE=$(du -h "$APPIMAGE_FILE" | cut -f1)
    log_info "AppImage size: $SIZE"
}

# ==============================================================================
# Create .deb Package
# ==============================================================================

create_deb() {
    log_info "Creating .deb package..."
    
    # Check for dpkg-deb
    if ! check_command dpkg-deb; then
        log_error "dpkg-deb not found. Install with: sudo apt-get install dpkg-dev"
        return 1
    fi
    
    # Create debian package structure
    DEB_DIR="$BUILD_DIR/deb"
    rm -rf "$DEB_DIR"
    
    # Create directory structure
    mkdir -p "$DEB_DIR/DEBIAN"
    mkdir -p "$DEB_DIR/opt/$APP_NAME"
    mkdir -p "$DEB_DIR/usr/share/applications"
    mkdir -p "$DEB_DIR/usr/share/icons/hicolor"
    mkdir -p "$DEB_DIR/usr/share/doc/localaidev"
    mkdir -p "$DEB_DIR/usr/bin"
    
    # Copy application files
    log_info "Copying application files..."
    cp -r "$PYINSTALLER_DIST"/* "$DEB_DIR/opt/$APP_NAME/"
    
    # Make executable
    chmod +x "$DEB_DIR/opt/$APP_NAME/$APP_NAME"
    
    # Create symlink in /usr/bin
    ln -s "/opt/$APP_NAME/$APP_NAME" "$DEB_DIR/usr/bin/localaidev"
    
    # Copy desktop entry
    cp "$SCRIPT_DIR/linux.desktop" "$DEB_DIR/usr/share/applications/localaidev.desktop"
    
    # Update Exec path in desktop file
    sed -i "s|Exec=/opt/LocalAIDev/LocalAIDev|Exec=/opt/$APP_NAME/$APP_NAME|g" \
        "$DEB_DIR/usr/share/applications/localaidev.desktop"
    
    # Copy icons
    log_info "Copying icons..."
    if [ -d "$ICON_BUILD" ]; then
        for size_dir in "$ICON_BUILD"/*/; do
            if [ -d "$size_dir" ]; then
                size=$(basename "$size_dir")
                mkdir -p "$DEB_DIR/usr/share/icons/hicolor/$size"
                cp -r "$size_dir"/* "$DEB_DIR/usr/share/icons/hicolor/$size/"
            fi
        done
    fi
    
    # Create copyright file
    cat > "$DEB_DIR/usr/share/doc/localaidev/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: $APP_NAME
Upstream-Contact: $APP_MAINTAINER
Source: $APP_WEBSITE

Files: *
Copyright: 2024 $APP_AUTHOR
License: $APP_LICENSE
EOF
    
    # Create changelog
    cat > "$DEB_DIR/usr/share/doc/localaidev/changelog.Debian.gz" << EOF
localaidev ($APP_VERSION) unstable; urgency=medium

  * Initial release
  * Desktop GUI for Local AI Development Environment
  * Task execution with real-time progress
  * Configuration management
  * Task history tracking

 -- $APP_MAINTAINER  $(date -R)
EOF
    gzip -9 "$DEB_DIR/usr/share/doc/localaidev/changelog.Debian.gz"
    
    # Calculate installed size (in KB)
    INSTALLED_SIZE=$(du -sk "$DEB_DIR/opt/$APP_NAME" | cut -f1)
    
    # Create control file
    cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: localaidev
Version: $APP_VERSION
Section: devel
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.27), libgtk-3-0 (>= 3.22), libx11-6
Maintainer: $APP_MAINTAINER
Installed-Size: $INSTALLED_SIZE
Homepage: $APP_WEBSITE
Description: $APP_DESCRIPTION
 Local AI Development Environment provides a modern desktop GUI
 that wraps AI-powered development tools. It allows users to
 interact with local LLMs for code generation, refactoring,
 and other development tasks.
 .
 Features:
  * Task-based interface for AI development requests
  * Real-time progress monitoring
  * Configuration management
  * Task history tracking and export
  * Cross-platform support
  * Light and dark themes
EOF
    
    # Create postinst script (post-installation)
    cat > "$DEB_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -q -f /usr/share/icons/hicolor
fi

# Update MIME database
if command -v update-mime-database > /dev/null 2>&1; then
    update-mime-database /usr/share/mime
fi

exit 0
EOF
    
    chmod +x "$DEB_DIR/DEBIAN/postinst"
    
    # Create postrm script (post-removal)
    cat > "$DEB_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -q -f /usr/share/icons/hicolor
fi

exit 0
EOF
    
    chmod +x "$DEB_DIR/DEBIAN/postrm"
    
    # Build the .deb package
    log_info "Building .deb package..."
    
    # Remove old .deb
    [ -f "$DEB_FILE" ] && rm "$DEB_FILE"
    
    # Build
    dpkg-deb --build "$DEB_DIR" "$DEB_FILE"
    
    log_success ".deb package created: $DEB_FILE"
    
    # Get size
    SIZE=$(du -h "$DEB_FILE" | cut -f1)
    log_info "Package size: $SIZE"
    
    # Lint the package
    if check_command lintian; then
        log_info "Running lintian checks..."
        lintian "$DEB_FILE" || log_warning "Lintian found some issues (see above)"
    fi
}

# ==============================================================================
# Main Execution
# ==============================================================================

# Prepare icons first
prepare_icons

# Build based on mode
case "$BUILD_MODE" in
    appimage)
        create_appimage
        ;;
    deb)
        create_deb
        ;;
    all)
        create_appimage || log_warning "AppImage creation failed"
        create_deb || log_warning ".deb creation failed"
        ;;
    *)
        log_error "Invalid build mode: $BUILD_MODE"
        log_info "Usage: $0 [appimage|deb|all]"
        exit 1
        ;;
esac

# ==============================================================================
# Summary
# ==============================================================================

echo ""
log_success "=== Build Complete ==="
echo ""
log_info "Output files:"
[ -f "$APPIMAGE_FILE" ] && echo "  AppImage: $APPIMAGE_FILE"
[ -f "$DEB_FILE" ] && echo "  .deb:     $DEB_FILE"
echo ""

log_info "Testing:"
if [ -f "$APPIMAGE_FILE" ]; then
    log_info "  AppImage: $APPIMAGE_FILE"
    log_info "  Or integrate with system: aisap register $APPIMAGE_FILE"
fi
if [ -f "$DEB_FILE" ]; then
    log_info "  .deb:     sudo dpkg -i $DEB_FILE"
    log_info "  Remove:   sudo apt remove localaidev"
fi
echo ""

log_info "Distribution:"
log_info "  AppImage can be distributed as a single file - runs on most Linux distros"
log_info "  .deb package can be installed on Debian/Ubuntu-based systems"
echo ""

log_success "Done!"
