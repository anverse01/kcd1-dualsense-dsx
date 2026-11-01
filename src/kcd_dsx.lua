-- KCD1 combat telemetry. Game callbacks are observed and forwarded unchanged.
if KCDDSX and KCDDSX.stop then KCDDSX:stop("reload") end
if DSXBowEvents and DSXBowEvents.stop then DSXBowEvents:stop("bridge_loaded") end
if DSXProbe and DSXProbe.enabled then DSXProbe:stop() end
KCDDSX = { version = "0.5.0", enabled = true, hooks = {}, tick = 0, seq = 0,
  state = "idle", suspended = false, bow = false, drawn = false, usable = false, stamina = 0,
  mode = "none", staminaRatio = 1, ratioSource = "observed_peak", maxObservedStamina = 0, weaponClasses = {} }
local K = KCDDSX
K.session = tostring(_time) .. "-" .. tostring(K)

local function quote(value)
  local s = tostring(value)
  s = string.gsub(s, "\\", "\\\\")
  s = string.gsub(s, '"', '\\"')
  s = string.gsub(s, "[\r\n\t]", " ")
  return '"' .. s .. '"'
end

function K:emit(event)
  self.seq = self.seq + 1
  local line = '[KCDDSX] {"v":1,"session":' .. quote(self.session) ..
    ',"seq":' .. tostring(self.seq) .. ',"event":' .. quote(event) ..
    ',"state":' .. quote(self.state) .. ',"bow":' .. tostring(self.bow) ..
    ',"drawn":' .. tostring(self.drawn) .. ',"suspended":' .. tostring(self.suspended) ..
    ',"usable":' .. tostring(self.usable) ..
    ',"mode":' .. quote(self.mode) .. ',"stamina_ratio":' .. tostring(self.staminaRatio) ..
    ',"ratio_source":' .. quote(self.ratioSource) ..
    ',"stamina":' .. tostring(self.stamina) .. ',"tick":' .. tostring(self.tick) .. '}'
  pcall(System.LogAlways, line)
end

function K:setState(state, event)
  self.state = state
  if state == "drawing" then self.drawTick = self.tick end
  self:emit(event)
end

function K:loadWeaponClasses()
  -- The shipped weapon table maps item_id to weapon_class_id; read it once.
  pcall(function()
    Database.LoadTable("weapon")
    local info = Database.GetTableInfo("weapon")
    for i = 0, info.LineCount - 1 do
      local row = Database.GetTableLine("weapon", i)
      if row and row.item_id then self.weaponClasses[string.lower(tostring(row.item_id))] = tonumber(row.weapon_class_id) end
    end
  end)
end

function K:classify(item)
  local classId = self.weaponClasses[string.lower(tostring(item.class))]
  if classId == 9 then return "bow" end
  if classId == 12 then return "unarmed" end
  if classId and classId >= 0 and classId <= 7 then return "melee" end
  if classId then return "other" end
  -- Fallback for missing table entries/modded items, without classifying arbitrary props as weapons.
  local name = string.lower(tostring(ItemManager.GetItemName(item.class)))
  if string.find(name, "bow", 1, true) then return "bow" end
  for _, token in ipairs({ "sword", "sabre", "axe", "mace", "halberd", "flail", "dagger" }) do
    if string.find(name, token, 1, true) then return "melee" end
  end
  return "other"
end

function K:context()
  local previousUsable, previousMode = self.usable, self.mode
  local ok, mode, drawn, dialog, stamina = pcall(function()
    if not player or not player.human then return "none", false, true, 0 end
    local kind, mainHandItem = "none", false
    for slot = 0, 1 do
      local id = player.human:GetItemInHand(slot)
      if id and id ~= __null then
        if slot == 0 then mainHandItem = true end
        local item = ItemManager.GetItem(id)
        if item and item.class then
          local found = self:classify(item)
          if found == "bow" then kind = "bow"
          elseif kind ~= "bow" and found == "melee" then kind = "melee"
          elseif kind == "none" and found == "unarmed" then kind = "unarmed" end
        end
      end
    end
    local isDrawn = player.human:IsWeaponDrawn()
    -- KCD does not keep fists "drawn" when shadowboxing alone. Empty hands are a
    -- separate combat mode and must not depend on the weapon-drawn flag.
    if kind == "none" and not mainHandItem then kind = "unarmed" end
    return kind, isDrawn, player.human:IsInDialog(), player.soul:GetState("stamina")
  end)
  if not ok then mode, drawn, dialog, stamina = "none", false, true, 0 end
  self.mode, self.bow, self.drawn = mode, mode == "bow", drawn == true
  self.stamina = type(stamina) == "number" and stamina or 0
  self.maxObservedStamina = math.max(self.maxObservedStamina, self.stamina)
  self.staminaRatio = self.maxObservedStamina > 0 and self.stamina / self.maxObservedStamina or 1
  self.ratioSource = "observed_peak"
  local ratioOK, ratio = pcall(function() return Variables.GetGlobal("stamina") end)
  if ratioOK and type(ratio) == "number" and ratio >= 0 and ratio <= 1 then
    self.staminaRatio, self.ratioSource = ratio, "ui"
  end
  self.staminaRatio = math.max(0, math.min(1, self.staminaRatio))
  self.usable = self.mode ~= "none" and (self.drawn or self.mode == "unarmed") and not dialog and not self.suspended
  if (not self.usable or self.mode ~= "bow") and self.state ~= "idle" then
    self:setState("idle", "context_lost")
  elseif self.usable ~= previousUsable or self.mode ~= previousMode then
    self:emit("combat_context")
  end
  return self.usable
end

function K:action(action, activation)
  if not self.enabled then return end
  if action == "prepare_to_attack" and activation == "press" then
    if self:context() and self.mode == "bow" then self:setState("drawing", "draw") end
  elseif action == "attack_abort" and activation == "press" then
    if self.state == "drawing" or self.state == "ready" then self:setState("idle", "cancel") end
  end
  -- attack1/prepare_to_attack release also occurs after cancellation: never call it a shot.
end

function K:animation(event, value, name)
  if not self.enabled or event ~= "animationevent" then return end
  if name == "ReadyToFire" then
    if (self.state == "drawing" or self.state == "ready") and self:context() and self.mode == "bow" then
      self:setState("ready", "ready")
    end
  elseif name == "FireArrow" then
    if self:context() and self.mode == "bow" then self:setState("idle", "shot") end
  elseif name == "CombatDrawEnd" or name == "CombatHolsterEnd" then
    self:context()
  end
end

function K:hook(owner, key, observer)
  if type(owner) ~= "table" or type(owner[key]) ~= "function" then return end
  local original, rawOriginal = owner[key], rawget(owner, key)
  local wrapper = function(receiver, ...)
    if K.enabled then
      local ok, same = pcall(function() return receiver == player or (receiver.id ~= nil and receiver.id == player.id) end)
      if ok and same then pcall(observer, ...) end
    end
    return original(receiver, ...)
  end
  owner[key] = wrapper
  table.insert(self.hooks, { owner = owner, key = key, original = rawOriginal, wrapper = wrapper })
end

function K:uiActionListener(action, event)
  if not self.enabled or action ~= "Game" then return end
  if event == "PauseGame" or event == "ExitGame" then
    self.suspended = true
    self:setState("idle", "pause")
  elseif event == "ResumeGame" then
    self.suspended = false
    self:context()
    self:setState("idle", "resume")
  end
end

function K:poll()
  self.timerId = nil
  if not self.enabled then return end
  self.tick = self.tick + 1
  if self.tick % 5 == 0 then
    self:context()
    if self.state ~= "idle" and self.drawTick and self.tick - self.drawTick > 300 then
      self:setState("idle", "draw_timeout")
    end
    self:emit("heartbeat")
  end
  self.timerId = Script.SetTimer(100, function() K:poll() end)
end

function K:stop(reason)
  self.state = "idle"
  self.usable = false
  self:emit("stop_" .. tostring(reason))
  self.enabled = false
  if self.timerId then pcall(Script.KillTimer, self.timerId); self.timerId = nil end
  for i = #self.hooks, 1, -1 do
    local hook = self.hooks[i]
    if hook.owner[hook.key] == hook.wrapper then hook.owner[hook.key] = hook.original end
  end
  self.hooks = {}
end

function K:reload()
  Script.ReloadScript("Scripts/KCDDSX/combat.lua")
end

K:loadWeaponClasses()
K:context()
K:hook(player, "OnAction", function(...) K:action(...) end)
K:hook(player, "ScriptEvent", function(...) K:animation(...) end)
if UIAction and UIAction.RegisterActionListener then UIAction.RegisterActionListener(K, "Game", "", "uiActionListener") end
System.AddCCommand("kcd_dsx_stop", "KCDDSX:stop('console')", "Stop bow telemetry and release DSX through the bridge.")
System.AddCCommand("kcd_dsx_start", "KCDDSX:reload()", "Restart the installed combat telemetry script.")
System.AddCCommand("dsx_bow_reload", "KCDDSX:reload()", "Reload KCD DSX telemetry.")
K:emit("start")
K:poll()
