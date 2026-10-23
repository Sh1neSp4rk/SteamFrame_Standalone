#!/bin/bash
# Steam launch wrapper for the native ARM64 Doom 3 BFG VR (Fully Possessed). Log: d3bfgvr-last.log
cd "$(dirname "$0")"
export SDL_VIDEODRIVER=x11
exec ./Doom3BFGVR +set fs_basepath "$PWD" "$@" > d3bfgvr-last.log 2>&1
