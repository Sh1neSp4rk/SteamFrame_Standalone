# Steam Frame standard controller layout (v1, adopted 2026-10-21)

The base layout for every PC VR mod on the Frame. Each game maps its own actions onto these slots.
A game only deviates where it has to, and the deviation gets written down under "Per-game notes".

## Frame controller inputs

- **Right hand:** trigger, bumper, grip, thumbstick (with click), A, B, X, Y, menu.
- **Left hand:** trigger, bumper, grip, thumbstick (with click), d-pad (up/down/left/right), view.

## Core slots (same in every game)

| Input | Slot | Typical action |
|---|---|---|
| Right trigger | Primary | Fire / attack / blue portal |
| Left trigger | Secondary | Alt-fire, aim down sights, shove, orange portal |
| Left bumper | Jump | Jump |
| Right bumper | Interact | Use / pick up / open |
| Right A | Crouch | Crouch (hold, or toggle if the game prefers) |
| Right B | Reload | Reload; melee if the game has no reload |
| Right X | Utility | Flashlight / quick melee / grenade |
| Right Y | Jump (duplicate) | Second jump button, or a game-specific "flex" action |
| Left stick | Move | Moves where your head is pointing where the mod supports it |
| Left stick click | Sprint | Sprint / walk toggle |
| Right stick left/right | Turn | Snap turn (30–45°, with hysteresis so it doesn't re-fire), or smooth turn if the game only does smooth |
| Right stick up/down (pushed past 75%) | Weapons | Next / previous weapon |
| Right stick click | Recenter | Recenter the view |
| Menu (right) | Pause | Pause / main menu (Escape) |
| View (left) | Info | Map / scoreboard / inventory / stats |

## Flex slots (game-specific functions)

| Input | Use for |
|---|---|
| Left d-pad up / down | Quick save / quick load, or two game-specific actions |
| Left d-pad left / right | Previous / next item or weapon (duplicate), or two game-specific actions |
| Left grip (80% squeeze) | A hold action: weapon wheel, inventory wheel, "hold to aim with stick" |
| Right grip (80% squeeze) | A physical grab, only where the game has one (otherwise unbound) |
| Right Y | A fifth flex action if the game doesn't need the duplicate jump |

## Rules

- **Grips:** never put core actions on them. They trigger just from holding the controller.
  When used, a grip needs an 80% squeeze to press and lets go below 70% (SteamVR's stock Frame layout uses 10%).
- **Stick deadzones:** 10% for move and turn. 75% for stick-as-buttons (weapon switching), so turning doesn't switch weapons.
- **Menus:** A selects and B goes back wherever the mod has separate menu actions. The left d-pad or left stick navigates.
- **Pause** is always the menu button. No hidden gestures; add a plugin or patch if a mod lacks one.
- **Recenter** is always the right stick click. If a mod insists on a combo (both sticks), keep the combo working too.
- **Head-oriented movement** is preferred wherever we control it.
- **Left d-pad:** the Frame driver reports a held click as ~150 ms pulses that stop after ~1 s, and its touch is one shared sensor. Bind the d-pad to tap actions only (menus, items, quicksave); a held action there needs a plugin that latches on the touch (Hollow Knight VR).

## Per-game notes (current state vs this standard)

| Game | Deviations |
|---|---|
| DUSK HD VR | Left stick click = walk; left grip (80%) = last weapon / weapon wheel; right stick up/down unused (it drives the wheel) |
| Doom 3 BFG VR | Right stick click = recenter; right stick up/down = weapons; left d-pad down = main menu (predates the menu-button rule) |
| L4D2 VR | Right stick click = show HUD; left stick click = recenter (mod default); X = flashlight |
| Portal 2 VR | Same binding as L4D2 VR (shared action set); triggers = blue/orange portals |
| GZDoomVR (Doom, Heretic, Hexen) | SteamVR's stock Frame layout; Heretic/Hexen grips raised to 80% |
| F.E.A.R. VR | SteamVR's auto layout; not yet reviewed |
| Quake VR (Team Beef) | Left trigger = run (the crouch slot: no crouch in Quake; no sprint on stick click); left grip (80%) = two-hand weapon hold; right grip = weapon wheel; right stick click = laser-sight cycle (no recenter in the port); right bumper and X unbound (no use key); movement is off-hand-controller-oriented |
| Selaco VR | Right bumper = secondary fire, A = use (user: both fires on the firing hand); left trigger = crouch (like the Quake games); quick save/load dropped (in the way), left d-pad up/down = use gadget / switch gadget; right grip (80%) = use/reload (+usereload); Y and left d-pad right unbound (legacy OpenVR input has only 8 button ids per hand); d-pad left = meds, view = PDA |
| Red Faction VR | On the standard after patching the mod (actions were hand-scoped). A = laser sight, right grip (80%) = the mod's alt-fire modifier, left stick click = holster; Y, view and d-pad unbound (no more actions). Pause = menu button via the patched menu action |
| Hollow Knight VR | Not the standard: the game's own Xbox layout 1:1 through the mod's virtual pad (A jump, X attack, B cast, Y dream nail, RT dash, LT super dash, RB quick cast, LB quick map, menu pause, view inventory, d-pad move/menus). Left stick click unbound (its action carries the d-pad touch for the FrameVR_HK plugin); grips unused |
| Circuit Superstars VR | Not the standard: the game's own Xbox layout 1:1 through the FrameVR_CS virtual pad (top-down racer, no motion controls in the mod). Bumpers = LB/RB, menu = Start (mod: double-tap first-person, hold recenter), view = Back; grips unused |
| Unreal Revived VR | Standard with the user's rules: L trigger crouch, L bumper jump, R trigger fire, R bumper alt-fire, menu pause, R stick click recenter; A use item, B next item, X / L view translator, L stick click / d-pad left previous item, d-pad up/down weapons; R Y, d-pad right and grips unbound (the game has 12 pad buttons). Aim follows the right controller (VRAimMode=1) |
| Far Cry VR | Standard with the user's rules: R trigger fire, R bumper use, L trigger crouch, L bumper jump, menu pause; A grenades, B reload, X binoculars, L stick click sprint, R stick left/right turn, up = next weapon + zoom in, down = zoom out; grips (80%) grab. In vehicles: L trigger leave, A reload, B change seat, X lights, L stick click change view |
