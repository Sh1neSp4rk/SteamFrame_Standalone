#!/bin/bash
# One timed Jedi Academy run with extra env/args. usage: jk_trial.sh "label" "ENV=1 ..." "+set x y ..." [scale] [secs]
GAME=${GAME:-jka}; G=~/PCVR/JKXR/$GAME; label=$1; envs=$2; args=$3; scale=${4:-0.8}; secs=${5:-60}; map=${MAP:-t1_sour}
{ printf 'export JKXR_RES_SCALE=%s\n' "$scale"; for e in $envs; do printf 'export %s\n' "$e"; done
  printf 'JK_ARGS="+set r_vulkanTiming 1 %s +map %s"\n' "$args" "$map"; } > $G/env.test
bash ~/PCVR/JKXR/jk_launch.sh $GAME $secs > /dev/null 2>&1
lines=$(grep -a 'rd-vulkan-timing: frames=' $G/last.log | tail -4)
gpu=$(echo "$lines" | grep -o -E 'gpu-stereo=[0-9.]+/[0-9.]+' | sed 's/gpu-stereo=//' | awk -F/ '{a+=$1; m=($2>m?$2:m); n++} END {if(n) printf "%.1f avg, %.1f max ms", a/n, m; else print "n/a"}')
rec=$(echo "$lines" | grep -o -E 'record=[0-9.]+' | sed 's/record=//' | awk '{a+=$1;n++} END {if(n) printf "%.1f", a/n}')
echo "[$GAME $label] scale $scale: gpu-stereo $gpu, cpu record ${rec} ms" | tee -a ~/PCVR/JKXR/sweep.txt
rm -f $G/env.test
