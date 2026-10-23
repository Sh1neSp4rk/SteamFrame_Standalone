"""Patch L4D2VR v0.6.2's d3d9.dll for the Steam Frame (x86 game under FEX + Proton).
Usage: python3 -I l4d2_patch.py <original d3d9.dll> <out d3d9.dll>

1. GetModuleWithRetry gives up after 100 x 50 ms; under FEX client.dll loads ~3 minutes in, so the mod never
   started VR. Loop tail  6a 32 / ff 15 <Sleep> / 83 fe 64 / 7c d4  ->  Sleep 127 ms and jl -> jmp
   (retry until GetModuleHandleA succeeds).
2. VR::SubmitVRTextures shows the main-menu overlay (last flat backbuffer, i.e. the loading screen) on every
   call where the game did not render a new stereo frame. At FEX frame rates that happens constantly in game,
   so the loading screen flickered in front of the view. Added an IsInGame() check at the top of that path:
   in game it now returns without touching overlays (the compositor keeps/reprojects the last eye frames).
   Lives in the .text slack after VirtualSize (0x100f3354), reached by a jmp at 0x100dd896."""
import struct, sys

BASE = 0x10000000
d = bytearray(open(sys.argv[1], "rb").read())

def va2off(va):  # .text: RVA 0x1000 <-> file 0x400
    return va - BASE - 0x1000 + 0x400
def rel32(src_next, dst):
    return struct.pack("<i", dst - src_next)

# --- 1. retry loop
pat = bytes.fromhex("6a 32 ff 15 bc 40 0f 10 83 fe 64 7c d4")
i = d.find(pat)
assert i >= 0 and d.find(pat, i + 1) < 0, "retry loop pattern not found exactly once"
d[i + 1] = 0x7f
d[i + 11] = 0xeb

# --- 2. in-game guard for the no-new-frame path
SITE, CAVE = 0x100dd896, 0x100f3354
CREATE_TEXTURES, AFTER_SITE, RET_PATH = 0x100dd710, 0x100dd8a4, 0x100ddc27
orig = bytes.fromhex("83 be f0 15 00 00 00 75 05 e8 6c fe ff ff")
assert d[va2off(SITE):va2off(SITE) + len(orig)] == orig, "SubmitVRTextures prologue differs"
assert d[va2off(CAVE):va2off(CAVE) + 64] == bytes(64), "code cave not empty"

c = bytearray()
c += bytes.fromhex("8b 06 8b 48 08 8b 01 ff 50 68")       # IsInGame(): ecx = m_Game->m_EngineClient
c += bytes.fromhex("84 c0 0f 85") + rel32(CAVE + len(c) + 8, RET_PATH)   # in game -> return
c += bytes.fromhex("83 be f0 15 00 00 00 75 07")            # if (!m_BlankTexture) {
c += bytes.fromhex("8b ce e8") + rel32(CAVE + len(c) + 7, CREATE_TEXTURES)  # this->CreateVRTextures()
c += bytes.fromhex("e9") + rel32(CAVE + len(c) + 5, AFTER_SITE)          # } continue original path
d[va2off(CAVE):va2off(CAVE) + len(c)] = c

j = bytes.fromhex("e9") + rel32(SITE + 5, CAVE) + bytes.fromhex("90" * 9)
d[va2off(SITE):va2off(SITE) + len(j)] = j

# grow .text VirtualSize over the cave so the loader maps it as part of the section
pe = struct.unpack_from("<I", d, 0x3c)[0]
sec = pe + 24 + struct.unpack_from("<H", d, pe + 20)[0]
assert d[sec:sec + 5] == b".text"
vsize, rsize = struct.unpack_from("<I", d, sec + 8)[0], struct.unpack_from("<I", d, sec + 16)[0]
struct.pack_into("<I", d, sec + 8, max(vsize, CAVE - BASE - 0x1000 + len(c)))
open(sys.argv[2], "wb").write(d)
print("patched: retry loop at", hex(i), "| guard", len(c), "bytes at", hex(CAVE))
