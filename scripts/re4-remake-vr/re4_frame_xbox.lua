-- Steam Frame -> Xbox default buttons for Resident Evil 4 (RE4VR).
--
-- RE4VR writes its VR controls into the engine gamepad (via.hid.GamePadDevice)
-- but its Frame layout has no bumpers and puts B/R3/View on other buttons. This
-- writes those physical buttons into the same gamepad, after RE4VR, as the
-- buttons a flatscreen Xbox controller would press. RE4VR keeps everything
-- else (A/X/Y, D-pad, sticks, triggers, grips, its VR menu).
--
-- Pairs with _framepad\re4_frame_binding.json (spare REFramework actions):
--   bumpers   -> Block   (left hand = LB, right hand = RB)
--   right B   -> Heal    (right hand = B / Cancel)
--   left View -> Heal    (left hand = View)
--   right stick click -> MiniMap (R3)
-- Log: reframework\data\re4_frame_xbox.log

local LOG_FILE = "re4_frame_xbox.log"
local log_lines = {}
local function log(s)
    log_lines[#log_lines + 1] = os.date("%H:%M:%S ") .. s
    if #log_lines > 400 then table.remove(log_lines, 1) end
    fs.write(LOG_FILE, table.concat(log_lines, "\n"))
end

local btn_t = sdk.find_type_definition("via.hid.GamePadButton")
local function button(name)
    return math.tointeger(btn_t:get_field(name):get_data(nil))
end

local B = { LB = button("LTrigTop"), RB = button("RTrigTop"), B = button("RRight"),
            Cancel = button("Cancel"), R3 = button("RStickPush"), View = button("CLeft") }
-- Only ever set from the physical button: RE4VR derives these from its
-- Quest-style remaps (Menu/right stick as back, right B as Ashley/map).
local OWNED = B.B | B.Cancel | B.R3 | B.View
log(string.format("buttons LB=%x RB=%x B=%x Cancel=%x R3=%x View=%x", B.LB, B.RB, B.B, B.Cancel, B.R3, B.View))

local pad_t = sdk.find_type_definition("via.hid.GamePad")
local pad_singleton = sdk.get_native_singleton("via.hid.GamePad")

local function read_physical()
    if vrmod == nil or not vrmod:is_hmd_active() then return 0 end
    local left, right = vrmod:get_left_joystick(), vrmod:get_right_joystick()
    local block, heal, minimap = vrmod:get_action_block(), vrmod:get_action_heal(), vrmod:get_action_minimap()
    local bits = 0
    if vrmod:is_action_active(block, left) then bits = bits | B.LB end
    if vrmod:is_action_active(block, right) then bits = bits | B.RB end
    if vrmod:is_action_active(heal, right) then bits = bits | B.B | B.Cancel end
    if vrmod:is_action_active(heal, left) then bits = bits | B.View end
    if vrmod:is_action_active(minimap, right) then bits = bits | B.R3 end
    return bits
end

local cur, prev_frame = 0, 0
local last_logged = -1

local function patch(dev)
    local held = (dev:call("get_Button") & ~OWNED) | cur
    local down = (dev:call("get_ButtonDown") & ~OWNED) | (cur & ~prev_frame)
    local up = (dev:call("get_ButtonUp") & ~OWNED) | (prev_frame & ~cur)
    dev:call("set_Button", held)
    dev:call("set_ButtonDown", down)
    dev:call("set_ButtonUp", up)
end

local entry_hits = {}
local function apply(entry)
    entry_hits[entry] = (entry_hits[entry] or 0) + 1
    local ok, err = pcall(function()
        cur = read_physical()
        local seen = {}
        for _, getter in ipairs({ "get_MergedDevice", "get_Device", "get_LastInputDevice" }) do
            local dev = sdk.call_native_func(pad_singleton, pad_t, getter)
            if dev ~= nil and not seen[dev:get_address()] then
                seen[dev:get_address()] = true
                patch(dev)
            end
        end
    end)
    if not ok and entry_hits[entry] < 5 then log(entry .. " error: " .. tostring(err)) end
    if cur ~= last_logged then
        log(string.format("physical buttons %x", cur))
        last_logged = cur
    end
end

-- RE4VR's write point isn't known, so re-apply (idempotently) at each stage
-- the game may read input from.
re.on_application_entry("UpdateHID", function() apply("post UpdateHID") end)
for _, name in ipairs({ "UpdateBehavior", "UpdateMotion", "LateUpdateBehavior", "UpdateGUI" }) do
    re.on_pre_application_entry(name, function() apply("pre " .. name) end)
end

local frames = 0
re.on_frame(function()
    prev_frame = cur
    frames = frames + 1
    if frames == 600 then
        local s = {}
        for k, v in pairs(entry_hits) do s[#s + 1] = k .. "=" .. v end
        log("entry hits after 600 frames: " .. table.concat(s, ", "))
    end
end)

log("loaded")
