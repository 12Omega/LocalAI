#!/bin/bash
# ==============================================================================
# macOS Installer Creation Script for Local AI Development Environment
# ==============================================================================
#
# This script creates a macOS installer (.pkg) and distributable DMG for the
# Local AI Development Environment Desktop GUI Application.
#
# Requirements implemented:
# - 8.7: Add application to Applications folder
# - 8.9: Code sign (if certificate available)
# - 7.6: Set Info.plist with version and icon
# - 15.2: Support macOS 10.14 (Mojave) and newer
#
# Prerequisites:
# - PyInstaller-built .app bundle in dist/LocalAIDev.app/
# - macOS 10.14 or later
# - Xcode Command Line Tools installed
# - pkgbuild and productbuild (included with Xcode)
# - (Optional) Apple Developer certificate for code signing
# - (Optional) create-dmg tool: brew install create-dmg
#
# Usage:
#   bash build/installers/macos-installer.sh
#
# Output:
#   dist/LocalAIDev.pkg     - Installer package
#   dist/LocalAIDev.dmg     - Distributable disk image
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
APP_BUNDLE_ID="com.localaidev.localaidev"
APP_PUBLISHER="Local AI Dev Team"
MIN_MACOS_VERSION="10.14"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build/macos-pkg"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"

# Output files
PKG_FILE="$DIST_DIR/$APP_NAME.pkg"
DMG_FILE="$DIST_DIR/$APP_NAME.dmg"

# Code signing (set to empty if not signing)
# To find your certificate: security find-identity -v -p codesigning
SIGNING_IDENTITY=""  # e.g., "Developer ID Application: Your Name (TEAM_ID)"
INSTALLER_SIGNING_IDENTITY=""  # e.g., "Developer ID Installer: Your Name (TEAM_ID)"

# Notarization (for distribution outside Mac App Store)
NOTARIZE=false
APPLE_ID=""  # Your Apple ID email
APPLE_ID_PASSWORD=""  # App-specific password
TEAM_ID=""  # Your team ID

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
        log_error "$1 is not installed or not in PATH"
        return 1
    fi
    return 0
}

# ==============================================================================
# Validation
# ==============================================================================

log_info "Starting macOS installer creation for $APP_DISPLAY_NAME v$APP_VERSION"

# Check if .app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    log_error "App bundle not found at $APP_BUNDLE"
    log_info "Please run PyInstaller first: pyinstaller build/pyinstaller/local-ai-dev.spec"
    exit 1
fi

# Check required commands
check_command pkgbuild || exit 1
check_command productbuild || exit 1

# Check optional commands
if ! check_command create-dmg; then
    log_warning "create-dmg not found. DMG creation will be skipped."
    log_info "Install with: brew install create-dmg"
fi

# ==============================================================================
# Code Signing (Optional)
# ==============================================================================

if [ -n "$SIGNING_IDENTITY" ]; then
    log_info "Code signing enabled with identity: $SIGNING_IDENTITY"
    
    # Verify certificate exists
    if ! security find-identity -v -p codesigning | grep -q "$SIGNING_IDENTITY"; then
        log_error "Code signing certificate not found: $SIGNING_IDENTITY"
        log_info "Available certificates:"
        security find-identity -v -p codesigning
        exit 1
    fi
    
    log_info "Signing app bundle..."
    codesign --deep --force --verify --verbose \
        --sign "$SIGNING_IDENTITY" \
        --options runtime \
        --timestamp \
        "$APP_BUNDLE"
    
    # Verify signature
    log_info "Verifying signature..."
    codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"
    spctl --assess --type execute --verbose=4 "$APP_BUNDLE"
    
    log_success "App bundle signed successfully"
else
    log_warning "Code signing disabled. The app will not be signed."
    log_info "To enable signing, set SIGNING_IDENTITY variable in this script"
fi

# ==============================================================================
# Create PKG Installer
# ==============================================================================

log_info "Creating PKG installer..."

# Create build directory
mkdir -p "$BUILD_DIR"

# Create component package
COMPONENT_PKG="$BUILD_DIR/$APP_NAME-component.pkg"

pkgbuild \
    --root "$DIST_DIR" \
    --install-location "/Applications" \
    --identifier "$APP_BUNDLE_ID" \
    --version "$APP_VERSION" \
    --component-plist "$SCRIPT_DIR/macos-component.plist" \
    "$COMPONENT_PKG"

log_success "Component package created"

# Create distribution XML
DISTRIBUTION_XML="$BUILD_DIR/distribution.xml"

cat > "$DISTRIBUTION_XML" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
    <title>$APP_DISPLAY_NAME</title>
    <organization>$APP_BUNDLE_ID</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false" hostArchitectures="x86_64,arm64"/>
    
    <!-- Define documents displayed at various steps -->
    <welcome file="welcome.html" mime-type="text/html"/>
    <license file="$PROJECT_ROOT/LICENSE" mime-type="text/plain"/>
    <conclusion file="conclusion.html" mime-type="text/html"/>
    
    <!-- Define the choices -->
    <choices-outline>
        <line choice="default">
            <line choice="$APP_BUNDLE_ID"/>
        </line>
    </choices-outline>
    
    <choice id="default"/>
    <choice id="$APP_BUNDLE_ID" visible="false">
        <pkg-ref id="$APP_BUNDLE_ID"/>
    </choice>
    
    <pkg-ref id="$APP_BUNDLE_ID" version="$APP_VERSION" onConclusion="none">
        $APP_NAME-component.pkg
    </pkg-ref>
    
    <!-- Minimum macOS version -->
    <installation-check script="installCheck();"/>
    
    <script>
    <![CDATA[
        function installCheck() {
            if (system.compareVersions(system.version.ProductVersion, '$MIN_MACOS_VERSION') < 0) {
                my.result.title = 'Unable to Install';
                my.result.message = 'This application requires macOS $MIN_MACOS_VERSION or later.';
                my.result.type = 'Fatal';
                return false;
            }
            return true;
        }
    ]]>
    </script>
    
</installer-gui-script>
EOF

# Create welcome page
cat > "$BUILD_DIR/welcome.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
        h1 { color: #007AFF; }
    </style>
</head>
<body>
    <h1>Welcome to $APP_DISPLAY_NAME</h1>
    <p>This installer will install $APP_DISPLAY_NAME version $APP_VERSION on your computer.</p>
    <p>$APP_DISPLAY_NAME is a modern desktop GUI application that provides a user-friendly interface for the Local AI Development Environment.</p>
    <p><strong>Minimum System Requirements:</strong></p>
    <ul>
        <li>macOS $MIN_MACOS_VERSION or later</li>
        <li>64-bit Intel or Apple Silicon processor</li>
        <li>200 MB of available disk space</li>
    </ul>
</body>
</html>
EOF

# Create conclusion page
cat > "$BUILD_DIR/conclusion.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
        h1 { color: #007AFF; }
    </style>
</head>
<body>
    <h1>Installation Complete</h1>
    <p>$APP_DISPLAY_NAME has been successfully installed.</p>
    <p>You can find the application in your Applications folder or launch it from Spotlight.</p>
    <p>Thank you for choosing $APP_DISPLAY_NAME!</p>
</body>
</html>
EOF

# Build product archive
productbuild \
    --distribution "$DISTRIBUTION_XML" \
    --package-path "$BUILD_DIR" \
    --resources "$BUILD_DIR" \
    "$PKG_FILE"

log_success "PKG installer created: $PKG_FILE"

# Sign the installer package
if [ -n "$INSTALLER_SIGNING_IDENTITY" ]; then
    log_info "Signing installer package..."
    productsign \
        --sign "$INSTALLER_SIGNING_IDENTITY" \
        "$PKG_FILE" \
        "${PKG_FILE}.signed"
    
    mv "${PKG_FILE}.signed" "$PKG_FILE"
    log_success "Installer package signed"
fi

# ==============================================================================
# Notarization (Optional)
# ==============================================================================

if [ "$NOTARIZE" = true ] && [ -n "$APPLE_ID" ] && [ -n "$APPLE_ID_PASSWORD" ]; then
    log_info "Submitting for notarization..."
    
    # Create a zip for notarization
    ditto -c -k --keepParent "$PKG_FILE" "${PKG_FILE}.zip"
    
    # Submit for notarization
    xcrun notarytool submit "${PKG_FILE}.zip" \
        --apple-id "$APPLE_ID" \
        --password "$APPLE_ID_PASSWORD" \
        --team-id "$TEAM_ID" \
        --wait
    
    # Staple the notarization ticket
    xcrun stapler staple "$PKG_FILE"
    
    # Clean up zip
    rm "${PKG_FILE}.zip"
    
    log_success "Notarization complete"
else
    log_warning "Notarization skipped. Set NOTARIZE=true and provide credentials to enable."
fi

# ==============================================================================
# Create DMG (Disk Image)
# ==============================================================================

if check_command create-dmg; then
    log_info "Creating DMG disk image..."
    
    # Remove existing DMG
    [ -f "$DMG_FILE" ] && rm "$DMG_FILE"
    
    # Create temporary directory for DMG contents
    DMG_STAGING="$BUILD_DIR/dmg-staging"
    rm -rf "$DMG_STAGING"
    mkdir -p "$DMG_STAGING"
    
    # Copy app bundle
    cp -R "$APP_BUNDLE" "$DMG_STAGING/"
    
    # Create symlink to Applications folder
    ln -s /Applications "$DMG_STAGING/Applications"
    
    # Create DMG
    create-dmg \
        --volname "$APP_DISPLAY_NAME" \
        --volicon "$APP_BUNDLE/Contents/Resources/icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 150 190 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 450 190 \
        --background "$SCRIPT_DIR/dmg-background.png" \
        --no-internet-enable \
        "$DMG_FILE" \
        "$DMG_STAGING" \
        || log_warning "DMG creation encountered issues (might still be usable)"
    
    # Clean up staging
    rm -rf "$DMG_STAGING"
    
    if [ -f "$DMG_FILE" ]; then
        log_success "DMG created: $DMG_FILE"
    fi
else
    log_warning "Skipping DMG creation (create-dmg not installed)"
fi

# ==============================================================================
# Summary
# ==============================================================================

echo ""
log_success "=== Build Complete ==="
echo ""
log_info "Output files:"
[ -f "$PKG_FILE" ] && echo "  PKG: $PKG_FILE"
[ -f "$DMG_FILE" ] && echo "  DMG: $DMG_FILE"
echo ""

log_info "Testing:"
log_info "  1. Install PKG: sudo installer -pkg $PKG_FILE -target /"
log_info "  2. Or mount DMG: open $DMG_FILE"
log_info "  3. Launch app: open /Applications/$APP_NAME.app"
echo ""

if [ -z "$SIGNING_IDENTITY" ]; then
    log_warning "Reminder: The app is not code-signed. It may show security warnings."
    log_info "To enable code signing:"
    log_info "  1. Get an Apple Developer certificate"
    log_info "  2. Set SIGNING_IDENTITY in this script"
fi

if [ "$NOTARIZE" = false ]; then
    log_warning "Reminder: The app is not notarized. Users may need to allow it in System Preferences."
    log_info "To enable notarization:"
    log_info "  1. Set NOTARIZE=true"
    log_info "  2. Provide APPLE_ID, APPLE_ID_PASSWORD, and TEAM_ID"
fi

log_success "Done!"
