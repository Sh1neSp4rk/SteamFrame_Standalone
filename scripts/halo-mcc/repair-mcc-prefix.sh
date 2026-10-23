#!/bin/bash
# repair-mcc-prefix.sh
#
# Halo MCC (Steam app 976730) on Steam Frame: the Easy Anti-Cheat setup that MCC's
# install script ran carried a bundled Visual C++ 2017 redistributable, which
# overwrote Proton's ARM64 (system32) and 32-bit (syswow64) C runtime DLLs with
# x86-64 / i386 Microsoft copies. Proton's own wineboot.exe then fails to load
# ucrtbase.dll (error c000007b) and the game never starts.
#
# This restores Proton's copies. Every foreign file is MOVED to a backup folder
# inside the prefix, never deleted, so the change can be rolled back.
set -u
P="$HOME/.local/share/Steam/steamapps/compatdata/976730"
PR="$HOME/.local/share/Steam/steamapps/common/Proton Experimental (ARM64)"

if pgrep -f "MCC-Win64-Shipping|compatdata/976730" >/dev/null; then
  echo "ABORT: MCC or its Proton prefix is in use. Close the game first."; exit 1
fi
[ -d "$P/pfx/drive_c/windows/system32" ] || { echo "ABORT: prefix not found at $P"; exit 1; }
[ -d "$PR/files/lib/wine/aarch64-windows" ] || { echo "ABORT: Proton Experimental (ARM64) not found"; exit 1; }

B="$P/polluted-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$B/system32" "$B/syswow64"
restored=0; backed=0
for d in system32 syswow64; do
  src=aarch64-windows; [ "$d" = syswow64 ] && src=i386-windows
  cd "$P/pfx/drive_c/windows/$d" || exit 1
  for f in ucrtbase.dll msvcp140.dll vcruntime140.dll concrt140.dll vccorlib140.dll vcomp140.dll mfc140*.dll api-ms-win-*.dll; do
    [ -f "$f" ] || continue                          # unmatched glob
    [ -L "$f" ] && continue                          # Proton symlink, leave it
    grep -q -a "Wine builtin DLL" "$f" && continue   # already Proton's copy
    mv "$f" "$B/$d/" || exit 1
    if [ -e "$PR/files/lib/wine/$src/$f" ]; then
      cp "$PR/files/lib/wine/$src/$f" "$f"; restored=$((restored+1))
    elif [ -e "$PR/files/share/default_pfx_arm64/drive_c/windows/$d/$f" ]; then
      cp -L "$PR/files/share/default_pfx_arm64/drive_c/windows/$d/$f" "$f"; restored=$((restored+1))
    else
      backed=$((backed+1))   # no Proton equivalent (mfc140*, api-ms-*): backed up only
    fi
  done
done
echo "restored=$restored  backed-up-only=$backed"
echo "backup folder: $B"
echo
echo "verify (want builtin=1 and Aarch64 in system32, Intel 80386 in syswow64):"
for d in system32 syswow64; do
  for f in ucrtbase.dll msvcp140.dll vcruntime140.dll concrt140.dll; do
    p="$P/pfx/drive_c/windows/$d/$f"
    printf "  %s/%-18s builtin=%s %s\n" "$d" "$f" "$(grep -c -a 'Wine builtin DLL' "$p")" "$(file -b "$p" | grep -o -E 'x86-64|Aarch64|Intel 80386')"
  done
done
