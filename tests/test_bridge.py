import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kcd_dsx_bridge import CombatController, FreshLog, parse_line, effects_packet
from lupa.lua51 import LuaRuntime


def bow_packet(strength):
    return effects_packet(0, 0, strength)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute("""
        logs={}; commands={}; _time=12345; __null=0; currentWeapon='caponBow'; drawn=true; dialog=false
        currentStamina=130; uiStamina=1; emptyHands=false
        Variables={GetGlobal=function() return uiStamina end}
        System={LogAlways=function(s) table.insert(logs,s) end,
                AddCCommand=function(k,v) commands[k]=v end}
        Script={SetTimer=function() return 10 end,KillTimer=function() end}
        ItemManager={GetItem=function() return {class='class'} end,
                     GetItemName=function() return currentWeapon end}
        actions=0; originalAction=function(self,action,activation,value)
          actions=actions+1; return 'forwarded',nil,value end
        originalEvent=function() return false,nil,7 end
        player={id=1,human={GetItemInHand=function(self,slot) if slot==1 and not emptyHands then return 1 else return 0 end end,
                           IsWeaponDrawn=function() return drawn end,IsInDialog=function() return dialog end},
                soul={GetState=function() return currentStamina end},OnAction=originalAction,ScriptEvent=originalEvent}
        """)
        self.lua.execute((ROOT / "src" / "kcd_dsx.lua").read_text(encoding="utf-8"))
        self.packets = []
        self.now = [100.0]
        self.control = CombatController(self.packets.append, clock=lambda: self.now[0])
        self.consumed = 0
        self.consume()

    def consume(self):
        logs = self.lua.globals().logs
        while self.consumed < len(logs):
            self.consumed += 1
            self.control.accept(parse_line(logs[self.consumed]))

    def execute(self, code):
        self.lua.execute(code)
        self.consume()

    def test_cancel_release_is_not_shot_then_real_fire_releases(self):
        self.execute("player:OnAction('prepare_to_attack','press',0.6)")
        self.assertEqual(self.packets[-1], bow_packet(3))
        self.execute("player:ScriptEvent('animationevent',0,'ReadyToFire')")
        self.assertEqual(self.packets[-1], bow_packet(4))
        self.execute("player:OnAction('attack_abort','press',1)")
        self.assertEqual(self.packets[-1], bow_packet(3))
        count = len(self.packets)
        self.execute("player:OnAction('prepare_to_attack','release',0); player:OnAction('attack1','release',0)")
        self.assertEqual(len(self.packets), count)
        self.execute("player:OnAction('prepare_to_attack','press',0.6); player:ScriptEvent('animationevent',0,'ReadyToFire')")
        self.execute("player:OnAction('attack1','release',0)")
        self.assertEqual(self.packets[-1], bow_packet(4))
        self.execute("player:ScriptEvent('animationevent',0,'FireArrow')")
        self.assertEqual(self.packets[-1], bow_packet(3))

    def test_held_bow_has_resistance_before_any_pull(self):
        self.assertEqual(self.lua.globals().KCDDSX.state, "idle")
        self.assertEqual(self.packets[-1], bow_packet(3))
        self.assertEqual(self.packets[-1]["instructions"][1]["parameters"], [0, 2, 21, 1, 3])

    def test_holstering_releases_and_drawing_bow_restores_baseline(self):
        self.execute("drawn=false; KCDDSX:context()")
        self.assertEqual(self.packets[-1], bow_packet(0))
        self.execute("drawn=true; player:ScriptEvent('animationevent',0,'CombatDrawEnd')")
        self.assertEqual(self.packets[-1], bow_packet(3))

    def test_melee_uses_its_own_effect_and_dialog_releases(self):
        self.execute("currentWeapon='long_sword_medium_03'; player:OnAction('prepare_to_attack','press',1)")
        self.execute("player:ScriptEvent('animationevent',0,'ReadyToFire')")
        self.assertEqual(self.lua.globals().KCDDSX.state, "idle")
        self.assertEqual(self.lua.globals().KCDDSX.mode, "melee")
        self.assertEqual(self.packets[-1], effects_packet(0, 0, 0))
        self.execute("currentWeapon='caponBow'; dialog=true; player:OnAction('prepare_to_attack','press',1)")
        self.assertEqual(self.lua.globals().KCDDSX.state, "idle")
        self.assertEqual(self.packets[-1], bow_packet(0))

    def test_stamina_drains_and_recovers_on_both_triggers(self):
        self.execute("currentWeapon='long_sword_medium_03'; KCDDSX:context()")
        for ratio, strength in [(1, 0), (.9, 0), (.8, 0), (.79, 1), (.6, 2), (.4, 4), (.2, 5), (0, 6), (.6, 2), (1, 0)]:
            self.execute(f"uiStamina={ratio}; currentStamina={ratio*130}; KCDDSX:context(); KCDDSX:emit('heartbeat')")
            self.assertEqual(self.packets[-1], effects_packet(0, strength, strength))

    def test_empty_hands_work_without_weapon_drawn_flag(self):
        self.execute("emptyHands=true; drawn=false; uiStamina=.2; currentStamina=26; KCDDSX:context()")
        self.assertEqual(self.lua.globals().KCDDSX.mode, "unarmed")
        self.assertTrue(self.lua.globals().KCDDSX.usable)
        self.assertEqual(self.packets[-1], effects_packet(0, 5, 5))
        self.execute("dialog=true; KCDDSX:context()")
        self.assertEqual(self.packets[-1], bow_packet(0))

    def test_switch_from_bow_to_tired_empty_hands_uses_fatigue(self):
        self.execute("uiStamina=.2; currentStamina=26; KCDDSX:context(); KCDDSX:emit('heartbeat')")
        self.assertEqual(self.packets[-1], bow_packet(3))
        self.execute("emptyHands=true; drawn=false; KCDDSX:context()")
        self.assertEqual(self.packets[-1], effects_packet(0, 5, 5))

    def test_bow_rules_ignore_melee_fatigue(self):
        self.execute("uiStamina=0; currentStamina=0; KCDDSX:context(); KCDDSX:emit('heartbeat')")
        self.assertEqual(self.packets[-1], bow_packet(3))
        self.execute("player:OnAction('prepare_to_attack','press',1); player:ScriptEvent('animationevent',0,'ReadyToFire')")
        self.assertEqual(self.packets[-1], bow_packet(4))

    def test_ratio_falls_back_to_observed_peak_without_assuming_100(self):
        self.execute("currentWeapon='long_sword_medium_03'; uiStamina=nil; currentStamina=65; KCDDSX:context()")
        self.assertEqual(self.lua.globals().KCDDSX.ratioSource, "observed_peak")
        self.assertAlmostEqual(self.lua.globals().KCDDSX.staminaRatio, .5)
        self.assertEqual(self.packets[-1], effects_packet(0, 3, 3))

    def test_weapon_table_classifies_custom_names(self):
        self.execute("KCDDSX.weaponClasses['class']=5; currentWeapon='custom_item'; KCDDSX:context()")
        self.assertEqual(self.lua.globals().KCDDSX.mode, "melee")
        self.assertEqual(self.packets[-1], effects_packet(0, 0, 0))

    def test_pause_releases_and_missing_context_fails_closed(self):
        self.execute("KCDDSX:uiActionListener('Game','PauseGame')")
        self.assertEqual(self.packets[-1], bow_packet(0))
        message = {"v":1,"session":"old-probe","seq":1,"event":"heartbeat",
                   "state":"idle","bow":True,"drawn":True,"suspended":False}
        self.control.accept(message)
        self.assertEqual(self.packets[-1], bow_packet(0))

    def test_stale_log_releases_and_duplicate_packets_do_not_reactivate(self):
        self.execute("player:OnAction('prepare_to_attack','press',1)")
        last = parse_line(self.lua.globals().logs[len(self.lua.globals().logs)])
        self.now[0] += 2.1
        self.control.watchdog()
        self.assertEqual(self.packets[-1], bow_packet(0))
        count = len(self.packets)
        self.assertFalse(self.control.accept(last))
        self.assertEqual(len(self.packets), count)

    def test_callbacks_and_stop_preserve_game_behavior(self):
        self.assertEqual(self.lua.eval("player:OnAction('attack1','release',0.25)"), ("forwarded", None, 0.25))
        self.assertEqual(self.lua.eval("player:ScriptEvent('animationevent',0,'FireArrow')"), (False, None, 7))
        self.execute("KCDDSX:stop('test'); assert(player.OnAction==originalAction and player.ScriptEvent==originalEvent)")

    def test_old_log_is_not_replayed_and_partial_lines_wait(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "kcd.log"
            path.write_bytes(b"old event\n")
            log = FreshLog(path)
            self.assertEqual(log.read_lines(), [])
            with path.open("ab") as file:
                file.write(b"new event")
            self.assertEqual(log.read_lines(), [])
            with path.open("ab") as file:
                file.write(b"\n")
            self.assertEqual(log.read_lines(), ["new event"])
            log.file.close()


if __name__ == "__main__":
    unittest.main()
