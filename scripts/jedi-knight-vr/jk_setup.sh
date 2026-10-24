#!/bin/bash
# Install the native JKXRL build into ~/PCVR/JKXR/{jka,jko} (fs_basepath), hard-linking Steam's asset pk3s (no extra
# space, Steam folders untouched), and add the "Jedi Academy VR" / "Jedi Outcast VR" Steam shortcuts.
set -e
J=~/PCVR/JKXR; S=$J/src; B=$S/OpenJK/build-frame; C=~/.local/share/Steam/steamapps/common
install_game() {  # key, Steam folder, engine, renderer, gamecode, game pk3, weapons pk3, shortcut name
  local key=$1 steam="$C/$2/GameData" G=$J/$1
  [ -f "$steam/base/assets0.pk3" ] || { echo "$2 not installed"; return 1; }
  mkdir -p $G/base
  for f in "$steam"/base/*.pk3; do ln -f "$f" $G/base/; done
  install -m755 $B/$3 $B/$4 $G/
  install -m755 $B/$5 $G/base/
  install -m644 $S/assets/z_vr_assets_base.pk3 $S/$6 $S/$7 $G/base/
  cat > $G/run.sh <<EOF
#!/bin/bash
# Steam launch wrapper for the native ARM64 JKXRL build ($8). Log: $G/last.log
cd "\$(dirname "\$0")"
export SDL_VIDEODRIVER=x11                                   # tested path: XR renders through Vulkan
unset MESA_GL_VERSION_OVERRIDE MESA_GLSL_VERSION_OVERRIDE
export LD_LIBRARY_PATH="$J/sdl3/lib:/opt/steamvr/bin/linuxarm64\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
export JKXR_RES_SCALE=\${JKXR_RES_SCALE:-1.0}                 # render resolution vs SteamVR's recommended (Frame patch)
export JKXR_NO_MDI=\${JKXR_NO_MDI:-1}                         # multi-draw indirect costs ~80 ms/frame on the Adreno driver
[ "\$JKXR_NO_MDI" = 0 ] && unset JKXR_NO_MDI
# Adreno (Turnip) tiled rendering vs direct-to-memory: Outcast's model-heavy scenes run ~4x faster direct (kejim_post
# 48 -> 11 ms GPU), Academy's levels ~2x slower (t1_sour 5 -> 12 ms). Per-game default; JKXR_SYSMEM=0/1 overrides.
JKXR_SYSMEM=\${JKXR_SYSMEM:-$9}
[ "\$JKXR_SYSMEM" = 1 ] && export TU_DEBUG=sysmem
JK_ARGS=""
[ -f env.test ] && source ./env.test                         # test hook: may set JKXR_RES_SCALE / JK_ARGS
exec stdbuf -oL -eL ./$(basename $3) +set fs_basepath "\$PWD" \$JK_ARGS "\$@" > last.log 2>&1
EOF
  chmod +x $G/run.sh
  python3 ~/PCVR/bin/steam_shortcuts.py list | grep -q "\"$8\"" && echo "$8: shortcut exists" || \
    python3 ~/PCVR/bin/steam_shortcuts.py add "$8" $G/run.sh $G
  echo "$8: $(ls $G/base | tr '\n' ' ')"
}
install_game jka "Jedi Academy" openjk_sp.aarch64 rdsp-vulkan_aarch64.so code/game/jagameaarch64.so \
  assets/z_vr_assets_jka.pk3 assets/weapons/z_vr_weapons_jka_Crusty_and_Elin.pk3 "Jedi Academy VR" 0
install_game jko "Jedi Outcast" openjo_sp.aarch64 rdjosp-vulkan_aarch64.so codeJK2/game/jospgameaarch64.so \
  assets/z_vr_assets_jko.pk3 assets/weapons/z_vr_weapons_jko_Crusty_and_Elin.pk3 "Jedi Outcast VR" 1
python3 ~/PCVR/bin/steam_shortcuts.py list | python3 -c "import json,sys; print([a for a in json.load(sys.stdin) if a['name'].startswith('Jedi')])"
