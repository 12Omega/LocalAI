#!/usr/bin/env python3
"""
Generate icon files for all platforms from a base PNG.

This script generates:
- Windows ICO: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
- macOS ICNS: multiple resolutions with @2x variants
- Linux PNG: 16x16 through 512x512
- Favicon: 16x16, 32x32 ICO and PNG

This version works with a base PNG image. If you have an SVG, convert it to PNG first using:
  - Online tools (e.g., https://cloudconvert.com/svg-to-png)
  - Inkscape: inkscape icon.svg --export-png=icon-base.png -w 1024 -h 1024
  - Or any image editing software

Requires: pip install pillow
"""

import os
import sys
from pathlib import Path
from PIL import Image
import io


def ensure_directory(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def create_png_from_base(base_image, output_path, size):
    """Resize base image to create PNG at specified size."""
    print(f"  Generating {output_path.name} ({size}x{size})")
    
    # Resize with high-quality Lanczos resampling
    resized = base_image.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(output_path, format='PNG', optimize=True)


def create_ico(png_files, output_path):
    """Create ICO file from multiple PNG files."""
    print(f"  Creating {output_path.name}")
    
    # Open all PNG files as PIL images
    images = [Image.open(png) for png in png_files]
    
    # Save as ICO with multiple sizes
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images]
    )


def create_icns(png_files, output_path):
    """Create ICNS file from multiple PNG files (macOS)."""
    print(f"  Creating {output_path.name}")
    
    # For ICNS, we need to use iconutil on macOS or png2icns tool
    # Since we're on Windows, we'll create a .iconset directory structure
    # and document that users need to run: iconutil -c icns icon.iconset
    
    iconset_path = output_path.parent / "icon.iconset"
    ensure_directory(iconset_path)
    
    # macOS iconset naming convention
    icns_map = {
        16: "icon_16x16.png",
        32: "icon_16x16@2x.png",  # Also icon_32x32.png
        64: "icon_32x32@2x.png",
        128: "icon_128x128.png",
        256: "icon_128x128@2x.png",  # Also icon_256x256.png
        512: "icon_256x256@2x.png",  # Also icon_512x512.png
    }
    
    # Additional standard names
    icns_extra = {
        32: "icon_32x32.png",
        256: "icon_256x256.png",
        512: "icon_512x512.png",
    }
    
    for size, name in icns_map.items():
        src = next((p for p in png_files if p.stem.endswith(f"{size}x{size}")), None)
        if src:
            img = Image.open(src)
            img.save(iconset_path / name, format='PNG')
            
            # Save extra names if needed
            if size in icns_extra:
                img.save(iconset_path / icns_extra[size], format='PNG')
    
    print(f"    Created iconset directory: {iconset_path}")
    print(f"    On macOS, run: iconutil -c icns {iconset_path}")
    
    # Create a placeholder ICNS info file
    with open(output_path.parent / "ICNS_README.txt", "w") as f:
        f.write("To create the ICNS file on macOS:\n")
        f.write(f"  iconutil -c icns {iconset_path.name}\n")
        f.write("\nThis will create icon.icns from the iconset directory.\n")


def main():
    """Generate all icon files."""
    print("Generating icon files for all platforms...\n")
    
    # Paths
    project_root = Path(__file__).parent
    svg_path = project_root / "src" / "web" / "assets" / "icon.svg"
    assets_dir = svg_path.parent
    
    # Check for base PNG - we'll create it from SVG if needed
    base_png_path = assets_dir / "icon-base-1024.png"
    
    if not base_png_path.exists():
        print("Base PNG not found. Attempting to convert SVG...")
        print("Trying different conversion methods...\n")
        
        # Try method 1: cairosvg
        try:
            import cairosvg
            print("  Attempting with cairosvg...")
            cairosvg.svg2png(
                url=str(svg_path),
                write_to=str(base_png_path),
                output_width=1024,
                output_height=1024
            )
            print("  ✓ Successfully converted with cairosvg\n")
        except Exception as e:
            print(f"  ✗ cairosvg failed: {e}\n")
            
            # Try method 2: wand
            try:
                from wand.image import Image as WandImage
                print("  Attempting with Wand (ImageMagick)...")
                with WandImage(filename=str(svg_path)) as img:
                    img.resize(1024, 1024)
                    img.format = 'png'
                    img.save(filename=str(base_png_path))
                print("  ✓ Successfully converted with Wand\n")
            except Exception as e2:
                print(f"  ✗ Wand failed: {e2}\n")
                
                # Try method 3: svglib + reportlab
                try:
                    from svglib.svglib import svg2rlg
                    from reportlab.graphics import renderPM
                    print("  Attempting with svglib...")
                    drawing = svg2rlg(str(svg_path))
                    scale = 1024 / max(drawing.width, drawing.height)
                    drawing.width = 1024
                    drawing.height = 1024
                    drawing.scale(scale, scale)
                    renderPM.drawToFile(drawing, str(base_png_path), fmt='PNG')
                    print("  ✓ Successfully converted with svglib\n")
                except Exception as e3:
                    print(f"  ✗ svglib failed: {e3}\n")
                    print("ERROR: Could not convert SVG to PNG automatically.")
                    print("\nPlease convert icon.svg to a 1024x1024 PNG manually:")
                    print("  1. Use an online converter: https://cloudconvert.com/svg-to-png")
                    print("  2. Use Inkscape: inkscape icon.svg --export-png=icon-base-1024.png -w 1024 -h 1024")
                    print(f"  3. Save the result as: {base_png_path}")
                    print("\nThen run this script again.")
                    sys.exit(1)
    
    # Load the base PNG
    print(f"Loading base PNG from: {base_png_path}")
    try:
        base_image = Image.open(base_png_path)
        if base_image.mode != 'RGBA':
            base_image = base_image.convert('RGBA')
        print(f"  Base image size: {base_image.size}\n")
    except Exception as e:
        print(f"ERROR: Could not load base PNG: {e}")
        sys.exit(1)
    
    # Create temporary directory for intermediate PNGs
    temp_dir = assets_dir / "temp_icons"
    ensure_directory(temp_dir)
    
    # Define all sizes we need
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    print("Step 1: Generating PNG files...")
    png_files = []
    for size in sizes:
        output_path = temp_dir / f"icon_{size}x{size}.png"
        try:
            create_png_from_base(base_image, output_path, size)
            png_files.append(output_path)
        except Exception as e:
            print(f"  Error generating {size}x{size}: {e}")
            sys.exit(1)
    
    print("\nStep 2: Creating Windows ICO files...")
    # Windows ICO (all sizes except 512)
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_pngs = [p for p in png_files if any(f"_{s}x{s}" in p.name for s in ico_sizes)]
    create_ico(ico_pngs, assets_dir / "icon.ico")
    
    print("\nStep 3: Creating favicon files...")
    # Favicon ICO (16x16 and 32x32)
    favicon_pngs = [p for p in png_files if "16x16" in p.name or "32x32" in p.name]
    create_ico(favicon_pngs, assets_dir / "favicon.ico")
    
    # Also create individual favicon PNGs
    for size in [16, 32]:
        src = temp_dir / f"icon_{size}x{size}.png"
        dst = assets_dir / f"favicon-{size}x{size}.png"
        print(f"  Copying {dst.name}")
        Image.open(src).save(dst, format='PNG')
    
    # Create favicon.png (32x32 as default)
    src = temp_dir / "icon_32x32.png"
    dst = assets_dir / "favicon.png"
    print(f"  Copying {dst.name}")
    Image.open(src).save(dst, format='PNG')
    
    print("\nStep 4: Creating macOS ICNS structure...")
    create_icns(png_files, assets_dir / "icon.icns")
    
    print("\nStep 5: Creating Linux PNG files...")
    # Copy all PNG files to assets directory with proper naming
    for size in sizes:
        src = temp_dir / f"icon_{size}x{size}.png"
        dst = assets_dir / f"icon-{size}x{size}.png"
        print(f"  Copying {dst.name}")
        Image.open(src).save(dst, format='PNG')
    
    print("\nStep 6: Creating app icon (main)...")
    # Create a main app icon at 512x512 for use in the app
    src = temp_dir / "icon_512x512.png"
    dst = assets_dir / "app-icon.png"
    print(f"  Copying {dst.name}")
    Image.open(src).save(dst, format='PNG')
    
    print("\nStep 7: Cleaning up temporary files...")
    # Clean up temp directory
    for png_file in png_files:
        if png_file.exists():
            png_file.unlink()
    if temp_dir.exists():
        temp_dir.rmdir()
    
    print("\n✓ Icon generation complete!")
    print(f"\nGenerated files in: {assets_dir}")
    print("\nWindows:")
    print("  - icon.ico (16, 32, 48, 64, 128, 256)")
    print("  - favicon.ico (16, 32)")
    print("  - favicon-16x16.png")
    print("  - favicon-32x32.png")
    print("  - favicon.png")
    print("\nmacOS:")
    print("  - icon.iconset/ (directory with all required sizes)")
    print("  - ICNS_README.txt (instructions to create .icns)")
    print("\nLinux:")
    print("  - icon-16x16.png through icon-512x512.png")
    print("\nGeneral:")
    print("  - app-icon.png (512x512 for use in the application)")


if __name__ == "__main__":
    main()
