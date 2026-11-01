-- Independent startup entry; no Cheat code or game scripts are bundled.
if not KCDDSXLoader then
  KCDDSXLoader = {}
  function KCDDSXLoader:onScene(action, event)
    if action == "sys_loadingimagescreen" and event == "OnEnd" then
      local ok, err = pcall(Script.ReloadScript, "Scripts/KCDDSX/combat.lua")
      if not ok then System.LogAlways("[KCDDSX] Load error: " .. tostring(err)) end
    end
  end
  UIAction.RegisterActionListener(KCDDSXLoader, "", "", "onScene")
  System.LogAlways("[KCDDSX] Independent loader 0.5.0 ready")
end
