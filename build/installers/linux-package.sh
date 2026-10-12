#!/bin/bash
# ==============================================================================
# Linux Package Creation Script for Local AI Development Environment
# ==============================================================================
#
# This script builds an AppImage or .deb package for the Desktop GUI Application.
# It creates the necessary package structure, copies the executable and assets,
# and runs the appropriate packaging tool.
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
#   bash build/installers/linux-package.sh [appimage|deb]
#
# Output:
#   dist/LocalAIDev-x86_64.AppImage  - Universal Linux package
#   dist/local-ai-dev_1.0.0_amd64.deb  - Debian package
#
# ==============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# ==============================================================================
# Configuration
# ==============================================================================

APP_NAME="LocalAIDev"
APP_VERSION="1.0.0"
PACKAGE_TYPE="${1:-deb}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build/linux-packages"
PYINSTALLER_DIST="$DIST_DIR/$APP_NAME"

# ==============================================================================
# Colors for output
# ==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# ==============================================================================
# Validation
# ==============================================================================

log_info "Starting Linux package creation for $APP_NAME v$APP_VERSION"
log_info "Package type: $PACKAGE_TYPE"

# Check if PyInstaller output exists
if [ ! -d "$PYINSTALLER_DIST" ]; then
    log_error "PyInstaller output not found at $PYINSTALLER_DIST"
    log_info "Please run: pyinstaller build/pyinstaller/local-ai-dev.spec"
    exit 1
fi

if [ ! -f "$PYINSTALLER_DIST/$APP_NAME" ]; then
    log_error "Executable not found: $PYINSTALLER_DIST/$APP_NAME"
    exit 1
fi

mkdir -p "$BUILD_DIR"

# ==============================================================================
# Create .deb Package
# ==============================================================================

create_deb() {
    log_info "Creating .deb package..."
    
    # Check for dpkg-deb
    if ! command -v dpkg-deb &> /dev/null; then
        log_error "dpkg-deb not found. Install with: sudo apt-get install dpkg-dev"
        return 1
    fi
    
    DEB_DIR="$BUILD_DIR/deb"
    rm -rf "$DEB_DIR"
    
    # Create directory structure
    mkdir -p "$DEB_DIR/DEBIAN"
    mkdir -p "$DEB_DIR/opt/local-ai-dev"
    mkdir -p "$DEB_DIR/usr/share/applications"
    mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$DEB_DIR/usr/share/doc/local-ai-dev"
    mkdir -p "$DEB_DIR/usr/bin"
    
    log_info "Copying application files..."
    cp -r "$PYINSTALLER_DIST"/* "$DEB_DIR/opt/local-ai-dev/"
    chmod +x "$DEB_DIR/opt/local-ai-dev/$APP_NAME"
    
    # Create symlink in /usr/bin
    ln -s "/opt/local-ai-dev/$APP_NAME" "$DEB_DIR/usr/bin/local-ai-dev"
    
    # Copy desktop file
    log_info "Installing desktop entry..."
    cp "$SCRIPT_DIR/linux.desktop" "$DEB_DIR/usr/share/applications/local-ai-dev.desktop"
    sed -i "s|Exec=/opt/LocalAIDev/LocalAIDev|Exec=/opt/local-ai-dev/local-ai-dev|g" \
        "$DEB_DIR/usr/share/applications/local-ai-dev.desktop"
    
    # Copy icon
    log_info "Installing application icon..."
    ICON_SOURCE="$PROJECT_ROOT/src/web/assets/icon-256x256.png"
    if [ -f "$ICON_SOURCE" ]; then
        cp "$ICON_SOURCE" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/local-ai-dev.png"
    else
        log_warning "Icon not found at $ICON_SOURCE"
    fi
    
    # Copy control file from template
    log_info "Creating package control file..."
    cp "$SCRIPT_DIR/linux-deb/DEBIAN/control" "$DEB_DIR/DEBIAN/control"
    
    # Calculate installed size
    INSTALLED_SIZE=$(du -sk "$DEB_DIR/opt/local-ai-dev" | cut -f1)
    echo "Installed-Size: $INSTALLED_SIZE" >> "$DEB_DIR/DEBIAN/control"
    
    # Create postinst script
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

exit 0
EOF
    chmod +x "$DEB_DIR/DEBIAN/postinst"
    
    # Create postrm script
    cat > "$DEB_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications
fi

if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -q -f /usr/share/icons/hicolor
fi

exit 0
EOF
    chmod +x "$DEB_DIR/DEBIAN/postrm"
    
    # Build package
    log_info "Building .deb package with dpkg-deb..."
    DEB_FILE="$DIST_DIR/local-ai-dev_${APP_VERSION}_amd64.deb"
    [ -f "$DEB_FILE" ] && rm "$DEB_FILE"
    
    dpkg-deb --build "$DEB_DIR" "$DEB_FILE"
    
    log_success ".deb package created: $DEB_FILE"
    log_info "Package size: $(du -h "$DEB_FILE" | cut -f1)"
}

# ==============================================================================
# Create AppImage
# ==============================================================================

create_appimage() {
    log_info "Creating AppImage..."
    
    # Check for appimagetool
    if ! command -v appimagetool &> /dev/null; then
        log_warning "appimagetool not found. Creating portable directory instead."
        create_portable
        return
    fi
    
    APPDIR="$BUILD_DIR/AppDir"
    rm -rf "$APPDIR"
    
    mkdir -p "$APPDIR/usr/bin"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
    
    log_info "Copying application files..."
    cp -r "$PYINSTALLER_DIST"/* "$APPDIR/usr/bin/"
    chmod +x "$APPDIR/usr/bin/$APP_NAME"
    
    # Create desktop entry
    cat > "$APPDIR/usr/share/applications/local-ai-dev.desktop" << EOF
[Desktop Entry]
Type=Application
Version=1.5
Name=Local AI Development Environment
GenericName=AI Development Tool
Comment=AI-powered local development environment
Exec=$APP_NAME %U
Icon=local-ai-dev
Terminal=false
Categories=Development;IDE;Utility;
Keywords=ai;development;coding;llm;
StartupNotify=true
EOF
    
    # Copy icon
    ICON_SOURCE="$PROJECT_ROOT/src/web/assets/icon-256x256.png"
    if [ -f "$ICON_SOURCE" ]; then
        cp "$ICON_SOURCE" "$APPDIR/usr/share/icons/hicolor/256x256/apps/local-ai-dev.png"
        cp "$ICON_SOURCE" "$APPDIR/local-ai-dev.png"
        cp "$ICON_SOURCE" "$APPDIR/.DirIcon"
    fi
    
    # Create AppRun
    cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PATH="${HERE}/usr/bin:${PATH}"

cd "$HOME"
exec "${HERE}/usr/bin/LocalAIDev" "$@"
EOF
    chmod +x "$APPDIR/AppRun"
    
    # Copy desktop file to root
    cp "$APPDIR/usr/share/applications/local-ai-dev.desktop" "$APPDIR/local-ai-dev.desktop"
    
    # Build AppImage
    log_info "Building AppImage..."
    APPIMAGE_FILE="$DIST_DIR/${APP_NAME}-x86_64.AppImage"
    [ -f "$APPIMAGE_FILE" ] && rm "$APPIMAGE_FILE"
    
    export ARCH=x86_64
    appimagetool "$APPDIR" "$APPIMAGE_FILE"
    chmod +x "$APPIMAGE_FILE"
    
    log_success "AppImage created: $APPIMAGE_FILE"
    log_info "AppImage size: $(du -h "$APPIMAGE_FILE" | cut -f1)"
}

# ==============================================================================
# Create Portable Directory (Fallback)
# ==============================================================================

create_portable() {
    log_info "Creating portable directory package..."
    
    PORTABLE_DIR="$DIST_DIR/${APP_NAME}-portable"
    rm -rf "$PORTABLE_DIR"
    mkdir -p "$PORTABLE_DIR"
    
    cp -r "$PYINSTALLER_DIST"/* "$PORTABLE_DIR/"
    chmod +x "$PORTABLE_DIR/$APP_NAME"
    
    # Create launch script
    cat > "$PORTABLE_DIR/launch.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
./LocalAIDev "$@"
EOF
    chmod +x "$PORTABLE_DIR/launch.sh"
    
    # Create README
    cat > "$PORTABLE_DIR/README.txt" << EOF
Local AI Development Environment - Portable Edition

To run the application:
  ./launch.sh

Or directly:
  ./LocalAIDev

For installation instructions, see:
  https://github.com/yourusername/local-ai-dev
EOF
    
    log_success "Portable directory created: $PORTABLE_DIR"
}

# ==============================================================================
# Main Execution
# ==============================================================================

case "$PACKAGE_TYPE" in
    deb)
        create_deb || log_error ".deb creation failed"
        ;;
    appimage)
        create_appimage || log_error "AppImage creation failed"
        ;;
    *)
        log_error "Invalid package type: $PACKAGE_TYPE"
        log_info "Usage: $0 [appimage|deb]"
        exit 1
        ;;
esac

log_success "Package creation complete!"
echo ""
log_info "Testing:"
if [ "$PACKAGE_TYPE" = "deb" ]; then
    echo "  sudo dpkg -i $DIST_DIR/local-ai-dev_${APP_VERSION}_amd64.deb"
    echo "  Remove: sudo apt remove local-ai-dev"
elif [ "$PACKAGE_TYPE" = "appimage" ]; then
    echo "  $DIST_DIR/${APP_NAME}-x86_64.AppImage"
fi
echo ""
