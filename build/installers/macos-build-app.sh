#!/bin/bash
# ==============================================================================
# macOS .app Bundle Builder for Local AI Development Environment
# ==============================================================================
#
# This script builds the macOS .app bundle with proper structure and Info.plist.
# It should be run AFTER PyInstaller creates the initial app bundle.
#
# Requirements implemented:
# - 7.6: Set Info.plist with version and icon
# - 8.9: Code sign (if certificate available)
# - 15.2: Support macOS 10.14 (Mojave) and newer
#
# Prerequisites:
# - PyInstaller installed: pip install pyinstaller
# - Icon file: src/web/assets/icon.icns
# - macOS 10.14 or later
# - (Optional) Apple Developer certificate for code signing
#
# Usage:
#   bash build/installers/macos-build-app.sh [--sign]
#
# Options:
#   --sign    Enable code signing (requires certificate configuration)
#
# Output:
#   dist/LocalAIDev.app - Complete .app bundle ready for distribution
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
APP_CATEGORY="public.app-category.developer-tools"
MIN_MACOS_VERSION="10.14"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
RESOURCES_DIR="$APP_BUNDLE/Contents/Resources"
MACOS_DIR="$APP_BUNDLE/Contents/MacOS"
INFO_PLIST="$APP_BUNDLE/Contents/Info.plist"

# Icon file
ICON_SOURCE="$PROJECT_ROOT/src/web/assets/icon.icns"
ICON_DEST="$RESOURCES_DIR/icon.icns"

# PyInstaller spec
PYINSTALLER_SPEC="$BUILD_DIR/pyinstaller/local-ai-dev.spec"

# Code signing
DO_SIGN=false
SIGNING_IDENTITY=""  # e.g., "Developer ID Application: Your Name (TEAM_ID)"
ENTITLEMENTS="$SCRIPT_DIR/macos-entitlements.plist"

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

# ==============================================================================
# Parse Arguments
# ==============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --sign)
            DO_SIGN=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Usage: $0 [--sign]"
            exit 1
            ;;
    esac
done

# ==============================================================================
# Step 1: Build with PyInstaller
# ==============================================================================

log_info "Building application with PyInstaller..."

if [ ! -f "$PYINSTALLER_SPEC" ]; then
    log_error "PyInstaller spec not found: $PYINSTALLER_SPEC"
    exit 1
fi

cd "$PROJECT_ROOT"
pyinstaller "$PYINSTALLER_SPEC" --clean --noconfirm

if [ ! -d "$APP_BUNDLE" ]; then
    log_error "PyInstaller failed to create app bundle: $APP_BUNDLE"
    exit 1
fi

log_success "PyInstaller build complete"

# ==============================================================================
# Step 2: Create proper .app bundle structure
# ==============================================================================

log_info "Configuring .app bundle structure..."

# Ensure required directories exist
mkdir -p "$RESOURCES_DIR"
mkdir -p "$MACOS_DIR"

# Copy icon file
if [ -f "$ICON_SOURCE" ]; then
    log_info "Copying icon file..."
    cp "$ICON_SOURCE" "$ICON_DEST"
    log_success "Icon copied to bundle"
else
    log_warning "Icon file not found: $ICON_SOURCE"
    log_info "App will use default icon"
fi

# ==============================================================================
# Step 3: Create/Update Info.plist
# ==============================================================================

log_info "Creating Info.plist..."

cat > "$INFO_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleName</key>
	<string>$APP_NAME</string>
	<key>CFBundleDisplayName</key>
	<string>$APP_DISPLAY_NAME</string>
	<key>CFBundleIdentifier</key>
	<string>$APP_BUNDLE_ID</string>
	<key>CFBundleVersion</key>
	<string>$APP_VERSION</string>
	<key>CFBundleShortVersionString</key>
	<string>$APP_VERSION</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleSignature</key>
	<string>????</string>
	<key>CFBundleExecutable</key>
	<string>$APP_NAME</string>
	<key>CFBundleIconFile</key>
	<string>icon.icns</string>
	<key>LSApplicationCategoryType</key>
	<string>$APP_CATEGORY</string>
	<key>LSMinimumSystemVersion</key>
	<string>$MIN_MACOS_VERSION</string>
	<key>NSHumanReadableCopyright</key>
	<string>Copyright © $(date +%Y) Local AI Dev Team. All rights reserved.</string>
	<key>NSHighResolutionCapable</key>
	<true/>
	<key>NSRequiresAquaSystemAppearance</key>
	<false/>
	<key>LSBackgroundOnly</key>
	<false/>
	<key>LSUIElement</key>
	<false/>
	<key>NSAppTransportSecurity</key>
	<dict>
		<key>NSAllowsArbitraryLoads</key>
		<false/>
		<key>NSAllowsLocalNetworking</key>
		<true/>
		<key>NSExceptionDomains</key>
		<dict>
			<key>localhost</key>
			<dict>
				<key>NSExceptionAllowsInsecureHTTPLoads</key>
				<true/>
				<key>NSIncludesSubdomains</key>
				<true/>
			</dict>
			<key>127.0.0.1</key>
			<dict>
				<key>NSExceptionAllowsInsecureHTTPLoads</key>
				<true/>
			</dict>
		</dict>
	</dict>
	<key>CFBundleDocumentTypes</key>
	<array>
		<dict>
			<key>CFBundleTypeExtensions</key>
			<array>
				<string>yaml</string>
				<string>yml</string>
			</array>
			<key>CFBundleTypeName</key>
			<string>YAML Configuration File</string>
			<key>CFBundleTypeRole</key>
			<string>Viewer</string>
			<key>LSHandlerRank</key>
			<string>Alternate</string>
		</dict>
	</array>
	<key>CFBundleURLTypes</key>
	<array>
		<dict>
			<key>CFBundleURLName</key>
			<string>Local AI Dev URL</string>
			<key>CFBundleURLSchemes</key>
			<array>
				<string>localaidev</string>
			</array>
		</dict>
	</array>
	<key>NSPrincipalClass</key>
	<string>NSApplication</string>
	<key>CFBundleSupportedPlatforms</key>
	<array>
		<string>MacOSX</string>
	</array>
	<key>CFBundleDevelopmentRegion</key>
	<string>en</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>LSArchitecturePriority</key>
	<array>
		<string>arm64</string>
		<string>x86_64</string>
	</array>
	<key>NSAppSleepDisabled</key>
	<false/>
	<key>NSSupportsSuddenTermination</key>
	<false/>
</dict>
</plist>
EOF

log_success "Info.plist created"

# Verify Info.plist is valid XML
if command -v plutil &> /dev/null; then
    if plutil -lint "$INFO_PLIST" > /dev/null; then
        log_success "Info.plist validation passed"
    else
        log_error "Info.plist validation failed"
        exit 1
    fi
fi

# ==============================================================================
# Step 4: Set proper permissions
# ==============================================================================

log_info "Setting file permissions..."

# Make executable executable
chmod +x "$MACOS_DIR/$APP_NAME"

# Set bundle permissions
chmod -R 755 "$APP_BUNDLE"

log_success "Permissions set"

# ==============================================================================
# Step 5: Code Signing (Optional)
# ==============================================================================

if [ "$DO_SIGN" = true ]; then
    if [ -z "$SIGNING_IDENTITY" ]; then
        log_error "Code signing requested but SIGNING_IDENTITY not configured"
        log_info "Edit this script and set SIGNING_IDENTITY variable"
        log_info "Find your certificate: security find-identity -v -p codesigning"
        exit 1
    fi
    
    log_info "Code signing with identity: $SIGNING_IDENTITY"
    
    # Verify certificate exists
    if ! security find-identity -v -p codesigning | grep -q "$SIGNING_IDENTITY"; then
        log_error "Code signing certificate not found: $SIGNING_IDENTITY"
        log_info "Available certificates:"
        security find-identity -v -p codesigning
        exit 1
    fi
    
    # Check if entitlements file exists
    if [ ! -f "$ENTITLEMENTS" ]; then
        log_warning "Entitlements file not found: $ENTITLEMENTS"
        log_info "Signing without entitlements (not recommended for notarization)"
        ENTITLEMENTS_ARG=""
    else
        ENTITLEMENTS_ARG="--entitlements $ENTITLEMENTS"
    fi
    
    # Sign the app bundle
    log_info "Signing app bundle (this may take a moment)..."
    codesign --deep --force --verify --verbose \
        --sign "$SIGNING_IDENTITY" \
        --options runtime \
        $ENTITLEMENTS_ARG \
        --timestamp \
        "$APP_BUNDLE"
    
    # Verify signature
    log_info "Verifying signature..."
    if codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE" 2>&1; then
        log_success "Signature verified"
    else
        log_error "Signature verification failed"
        exit 1
    fi
    
    # Check Gatekeeper assessment
    log_info "Checking Gatekeeper assessment..."
    if spctl --assess --type execute --verbose=4 "$APP_BUNDLE" 2>&1; then
        log_success "Gatekeeper assessment passed"
    else
        log_warning "Gatekeeper assessment failed (this is normal if not notarized)"
    fi
    
    log_success "Code signing complete"
else
    log_warning "Code signing skipped (use --sign to enable)"
fi

# ==============================================================================
# Step 6: Verification
# ==============================================================================

log_info "Verifying app bundle..."

# Check bundle structure
if [ ! -d "$APP_BUNDLE/Contents" ]; then
    log_error "Invalid bundle structure: Contents directory missing"
    exit 1
fi

if [ ! -f "$INFO_PLIST" ]; then
    log_error "Invalid bundle structure: Info.plist missing"
    exit 1
fi

if [ ! -x "$MACOS_DIR/$APP_NAME" ]; then
    log_error "Invalid bundle structure: Executable missing or not executable"
    exit 1
fi

log_success "Bundle structure verified"

# ==============================================================================
# Step 7: Display Info
# ==============================================================================

echo ""
log_success "=== Build Complete ==="
echo ""
log_info "App bundle: $APP_BUNDLE"
log_info "Version: $APP_VERSION"
log_info "Bundle ID: $APP_BUNDLE_ID"
log_info "Minimum macOS: $MIN_MACOS_VERSION"

# Display bundle size
BUNDLE_SIZE=$(du -sh "$APP_BUNDLE" | cut -f1)
log_info "Bundle size: $BUNDLE_SIZE"

echo ""
log_info "Testing:"
log_info "  Launch: open $APP_BUNDLE"
log_info "  or: $APP_BUNDLE/Contents/MacOS/$APP_NAME"
echo ""

if [ "$DO_SIGN" = false ]; then
    log_warning "App is not code-signed"
    log_info "Users may see security warnings when launching"
    log_info "To sign: $0 --sign"
    echo ""
fi

log_info "Next steps:"
log_info "  1. Test the application: open $APP_BUNDLE"
log_info "  2. Create installer: bash build/installers/macos-installer.sh"
log_info "  3. Or create DMG: open dist/ in Finder and drag to create DMG"
echo ""

log_success "Done!"
