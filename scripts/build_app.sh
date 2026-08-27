#!/usr/bin/env bash
# ==============================================================================
# scripts/build_app.sh — 1-Click Standalone Build Script for rat.app & rat.dmg
# ==============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "================================================================="
echo "  🚀 Starting 1-Click Standalone Build for rat on macOS"
echo "================================================================="

# 1. Clean previous build artifacts
echo "🧹 Cleaning previous build artifacts..."
rm -rf build dist dmg_temp *.dmg

# 2. Build rat.app using PyInstaller
echo "📦 Packaging rat.app with PyInstaller..."
if ! command -v pyinstaller &> /dev/null; then
    echo "⚙️ PyInstaller not found, installing..."
    pip install pyinstaller
fi

pyinstaller rat.spec --noconfirm

if [ ! -d "dist/rat.app" ]; then
    echo "❌ Error: dist/rat.app was not created!"
    exit 1
fi

echo "✅ rat.app created successfully in dist/rat.app"

# 3. Create DMG Installer with Applications drag-and-drop symlink
echo "💿 Creating standalone rat.dmg disk image..."
mkdir -p dmg_temp
cp -R dist/rat.app dmg_temp/
ln -s /Applications dmg_temp/Applications

hdiutil create -volname "rat — Smart File Finder" \
               -srcfolder dmg_temp \
               -ov -format UDZO \
               "dist/rat.dmg"

rm -rf dmg_temp

echo "================================================================="
echo "  🎉 BUILD COMPLETE!"
echo "  📂 Output App: $PROJECT_DIR/dist/rat.app"
echo "  💿 Installer DMG: $PROJECT_DIR/dist/rat.dmg"
echo "  ✨ Your friend can now download rat.dmg, drag it to Applications, and use it immediately!"
echo "================================================================="
