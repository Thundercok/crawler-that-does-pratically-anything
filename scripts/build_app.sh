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

# 2. Ensure rat.icns icon exists
if [ ! -f "rat.icns" ]; then
    echo "🎨 Generating high-resolution rat.icns icon..."
    python3 scripts/generate_icon.py
fi

# 3. Build rat.app using PyInstaller
echo "📦 Packaging rat.app with PyInstaller..."
if ! python3 -m PyInstaller --version &> /dev/null; then
    echo "⚙️ PyInstaller not found, installing via pip..."
    python3 -m pip install pyinstaller
fi

python3 -m PyInstaller rat.spec --noconfirm

if [ ! -d "dist/rat.app" ]; then
    echo "❌ Error: dist/rat.app was not created!"
    exit 1
fi

echo "✅ rat.app created successfully in dist/rat.app"

# 4. Ad-hoc codesign rat.app for macOS Gatekeeper compatibility
echo "🔏 Performing ad-hoc codesigning for local macOS execution..."
codesign --force --deep -s - dist/rat.app || echo "⚠️ Warning: codesign failed, continuing..."

# 5. Create DMG Installer with Applications drag-and-drop symlink & Gatekeeper Helper
echo "💿 Creating standalone rat.dmg disk image..."
mkdir -p dmg_temp
cp -R dist/rat.app dmg_temp/
ln -s /Applications dmg_temp/Applications

# Add 1-click Gatekeeper bypass helper for friends
cat << 'EOF' > dmg_temp/Open_Rat_First_Time.command
#!/bin/bash
echo "====================================================="
echo "  🚀 rat — Quick Gatekeeper Fix for Friends & Club"
echo "====================================================="
echo "Removing macOS quarantine flag so rat can launch..."

if [ -d "/Applications/rat.app" ]; then
    xattr -cr /Applications/rat.app 2>/dev/null || true
    echo "✅ Permissions fixed for /Applications/rat.app!"
    open /Applications/rat.app
elif [ -d "$(dirname "$0")/rat.app" ]; then
    xattr -cr "$(dirname "$0")/rat.app" 2>/dev/null || true
    echo "✅ Permissions fixed for local rat.app!"
    open "$(dirname "$0")/rat.app"
else
    echo "⚠️ Please drag rat.app into Applications folder first, then run this again."
fi

echo "Done! You can close this terminal window."
EOF
chmod +x dmg_temp/Open_Rat_First_Time.command

# Add friendly Vietnamese Quick Guide
cat << 'EOF' > dmg_temp/HƯỚNG_DẪN_CÀI_ĐẶT.txt
========================================================================
  🐭 CHÀO MỪNG BẠN ĐẾN VỚI RAT (Retrieval Augmented Tool)
========================================================================

CÁCH CÀI ĐẶT NHANH (DÀNH CHO BẠN BÈ / CLB):

1. Kéo thả biểu tượng "rat.app" vào thư mục "Applications" bên cạnh.
2. VÌ ĐÂY LÀ BẢN NỘI BỘ (Chưa qua Apple Notarization):
   - Cách 1 (Nhanh nhất): Nhấp đúp vào file "Open_Rat_First_Time.command"
   - Cách 2: Vào Applications, chuột phải (Control + Click) vào rat.app -> Chọn "Open" -> Bấm "Open".
   - Cách 3: Mở Terminal gõ:
     xattr -cr /Applications/rat.app

3. PHÍM TẮT & TÍNH NĂNG:
   - Nhấn: Option + Shift + Space để mở thanh tìm kiếm Spotlight AI.
   - Click icon chuột trên Menu Bar -> Chọn "Thời khóa biểu CLB" để ghép lịch nhóm & tìm khung giờ vàng.

Chúc bạn học tập và tìm kiếm tệp tin thật chill & hiệu quả!
========================================================================
EOF

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
