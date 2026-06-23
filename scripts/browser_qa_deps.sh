#!/usr/bin/env bash
set -euo pipefail

root="${NFI_BROWSER_QA_LIB_ROOT:-.omo/tools/browser-libs}"
lib_dir="$root/root/usr/lib/x86_64-linux-gnu"
font_dir="$root/root/usr/share/fonts"
font_config="$root/fonts.conf"
debs_dir="$root/debs"
packages=(libnspr4 libnss3 libasound2t64 fonts-noto-cjk)
required=(
  "$lib_dir/libnspr4.so"
  "$lib_dir/libnss3.so"
  "$lib_dir/libnssutil3.so"
  "$lib_dir/libasound.so.2"
  "$font_dir/opentype/noto/NotoSansCJK-Regular.ttc"
  "$font_config"
)

ready=true
for path in "${required[@]}"; do
  if [[ ! -e "$path" ]]; then
    ready=false
  fi
done

if [[ "$ready" == true ]]; then
  printf 'browser QA local libs ready: %s\n' "$lib_dir"
  exit 0
fi

command -v apt-get >/dev/null
command -v dpkg-deb >/dev/null

mkdir -p "$debs_dir" "$root/root"
(
  cd "$debs_dir"
  apt-get download "${packages[@]}"
)
for deb in "$debs_dir"/*.deb; do
  dpkg-deb -x "$deb" "$root/root"
done
rm -f "$debs_dir"/*.deb

font_dir_abs="$(cd "$font_dir" && pwd -P)"
cat > "$font_config" <<EOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir>/usr/share/fonts</dir>
  <dir>$font_dir_abs</dir>
</fontconfig>
EOF
for path in "${required[@]}"; do
  test -e "$path"
done
printf 'browser QA local libs ready: %s\n' "$lib_dir"
