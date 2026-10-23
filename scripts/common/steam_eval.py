#!/usr/bin/env python3
"""Run one JavaScript expression in the Steam client (SharedJSContext) and print the result.
   python3 steam_eval.py 'JSON.stringify(appStore.allApps.length)'"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import steam_shortcuts as s
print(s.evaluate(sys.argv[1]))
