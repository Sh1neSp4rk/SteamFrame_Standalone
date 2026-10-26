#!/bin/bash
# Cumulative feature bisect for Jedi Academy VR GPU time (headset must be worn). Same map, scale 0.8, one launch each.
G=~/PCVR/JKXR/jka; map=${MAP:-t1_sour}; secs=${SECS:-60}; out=~/PCVR/JKXR/sweep.txt
declare -a NAME SET
NAME[0]="no compute skinning";          SET[0]="+set r_vulkanComputeSkinning 0"
NAME[1]="+ no vegetation/fog";          SET[1]="${SET[0]} +set r_vulkanVegetationCoverage 0 +set r_vulkanLocalFog 0 +set r_vulkanVegetationFog 0"
NAME[2]="+ no per-surface extras";      SET[2]="${SET[1]} +set r_vulkanModelDynamicLights 0 +set r_vulkanDeforms 0 +set r_vulkanSpecularAlpha 0 +set r_vulkanAutosprites 0 +set r_vulkanVertexStyles 0 +set r_flares 0"
NAME[3]="+ no anisotropy, picmip 2";    SET[3]="${SET[2]} +set r_ext_texture_filter_anisotropic 0 +set r_picmip 2"
echo "== $(date '+%F %T') bisect map=$map scale=0.8" >> $out
for i in ${IDX:-0 1 2 3}; do
  printf 'export JKXR_RES_SCALE=0.8\nJK_ARGS="+set r_vulkanTiming 1 %s +map %s"\n' "${SET[$i]}" "$map" > $G/env.test
  bash ~/PCVR/JKXR/jk_launch.sh jka $secs > /dev/null 2>&1
  lines=$(grep -a 'rd-vulkan-timing: frames=' $G/last.log | tail -4)
  gpu=$(echo "$lines" | grep -o -E 'gpu-stereo=[0-9.]+/[0-9.]+' | sed 's/gpu-stereo=//' | awk -F/ '{a+=$1; m=($2>m?$2:m); n++} END {if(n) printf "%.1f avg, %.1f max ms", a/n, m; else print "n/a"}')
  draws=$(echo "$lines" | grep -o -E 'models-opaque-stereo=[0-9.]+/[0-9.]+/[0-9.]+' | tail -1)
  echo "[$i] ${NAME[$i]}: gpu-stereo $gpu, $draws" | tee -a $out
done
rm -f $G/env.test
