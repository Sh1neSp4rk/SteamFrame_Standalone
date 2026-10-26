#!/bin/bash
# Resolution sweep for Jedi Academy VR (headset must be worn). usage: jk_sweep.sh [map] [seconds] [scales...]
# Each run loads the same map from the command line with r_vulkanTiming 1 and reports the steady-state GPU time
# per stereo frame (budget at 72 Hz: 13.9 ms). Results: ~/PCVR/JKXR/sweep.txt
G=~/PCVR/JKXR/jka; map=${1:-t1_sour}; secs=${2:-70}; shift 2 2>/dev/null; scales=${@:-1.0 0.8 0.65}
out=~/PCVR/JKXR/sweep.txt; echo "== $(date '+%F %T') map=$map" >> $out
for s in $scales; do
  printf 'export JKXR_RES_SCALE=%s\nJK_ARGS="+set r_vulkanTiming 1 +map %s"\n' "$s" "$map" > $G/env.test
  bash ~/PCVR/JKXR/jk_launch.sh jka $secs > /dev/null 2>&1
  eye=$(grep -a -o -E 'eye buffer [0-9]+x[0-9]+' $G/last.log | head -1)
  lines=$(grep -a 'rd-vulkan-timing: frames=' $G/last.log | tail -6)
  gpu=$(echo "$lines" | grep -o -E 'gpu-stereo=[0-9.]+/[0-9.]+' | sed 's/gpu-stereo=//' | awk -F/ '{a+=$1; m=($2>m?$2:m); n++} END {if(n) printf "%.1f avg, %.1f max ms", a/n, m; else print "n/a"}')
  rec=$(echo "$lines" | grep -o -E 'record=[0-9.]+' | sed 's/record=//' | awk '{a+=$1;n++} END {if(n) printf "%.1f ms", a/n}')
  fr=$(echo "$lines" | grep -o -E 'frames=[0-9]+' | tail -1)
  echo "scale $s: $eye, gpu-stereo $gpu, cpu record $rec, $fr" | tee -a $out
done
rm -f $G/env.test
