#!/bin/bash
# Heavy-scene comparison, round 2: Turnip sysmem rendering vs resolution 0.7 (headset worn).
summ() {
  grep -a 'rd-vulkan-timing: frames=' ~/PCVR/JKXR/jko/last.log | awk -v label="$1" '
    { match($0, /gpu-stereo=[0-9.]+\/[0-9.]+/); g=substr($0, RSTART+11, RLENGTH-11); split(g, gg, "/");
      match($0, /models-opaque-stereo=[0-9.]+\/[0-9.]+\/[0-9.]+/); m=substr($0, RSTART+21, RLENGTH-21); split(m, mm, "/");
      if (mm[1] > 100) { n++; s+=gg[1]; if (gg[2]>mx) mx=gg[2]; d+=mm[3] } }
    END { if (n) printf "[%s] heavy intervals=%d gpu-stereo avg %.1f ms, max %.1f ms, draws avg %.0f\n", label, n, s/n, mx, d/n;
          else printf "[%s] no heavy intervals\n", label }' | tee -a ~/PCVR/JKXR/sweep.txt
}
GAME=jko MAP=kejim_post bash ~/PCVR/JKXR/jk_trial.sh sysmem 'TU_DEBUG=sysmem' '' 1.0 150 > /dev/null; summ "TU_DEBUG=sysmem, scale 1.0"
grep -a -i -E 'tu_debug|sysmem' ~/PCVR/JKXR/jko/last.log | head -2
GAME=jko MAP=kejim_post bash ~/PCVR/JKXR/jk_trial.sh scale07 '' '' 0.7 150 > /dev/null; summ "scale 0.7"
