#!/bin/bash
# Round 3: sysmem + CPU skinning on JKO's heavy scene; sysmem on JKA t1_sour (light/MDI-free scene) for regressions.
summ() {
  grep -a 'rd-vulkan-timing: frames=' ~/PCVR/JKXR/$2/last.log | awk -v label="$1" -v thr="$3" '
    { match($0, /gpu-stereo=[0-9.]+\/[0-9.]+/); g=substr($0, RSTART+11, RLENGTH-11); split(g, gg, "/");
      match($0, /models-opaque-stereo=[0-9.]+\/[0-9.]+\/[0-9.]+/); m=substr($0, RSTART+21, RLENGTH-21); split(m, mm, "/");
      if (mm[1] > thr) { n++; s+=gg[1]; if (gg[2]>mx) mx=gg[2]; d+=mm[3] } }
    END { if (n) printf "[%s] intervals=%d gpu-stereo avg %.1f ms, max %.1f ms, draws avg %.0f\n", label, n, s/n, mx, d/n;
          else printf "[%s] no intervals\n", label }' | tee -a ~/PCVR/JKXR/sweep.txt
}
GAME=jko MAP=kejim_post bash ~/PCVR/JKXR/jk_trial.sh sysmem-cpuskin 'TU_DEBUG=sysmem' '+set r_vulkanComputeSkinning 0' 1.0 150 > /dev/null
summ "JKO sysmem + CPU skinning (heavy)" jko 100
GAME=jka MAP=t1_sour bash ~/PCVR/JKXR/jk_trial.sh sysmem 'TU_DEBUG=sysmem' '' 1.0 60 > /dev/null
summ "JKA t1_sour sysmem (all in-level)" jka 5
