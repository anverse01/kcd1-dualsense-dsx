# Credits / 原作者与参考来源

Thank you to the original authors and maintainers below. Links and roles are preserved in both the player package and source archive. / 以下链接及用途随安装包、源码一起保留。

## Projects, mods and guides / 项目、Mod 与教程

| Project | Original author / project owner | How it was used |
| --- | --- | --- |
| [DSX](https://github.com/Paliverse/DSX) · [Steam](https://store.steampowered.com/app/1812620/DSX/) · [v3 mod system](https://github.com/Paliverse/DSX/tree/main/Mod%20System%20%28DSX%20v3%29) | [Paliverse](https://github.com/Paliverse) | Required external application; official v3.1+ UDP examples informed the packet format, trigger modes and restore-profile instruction. / 正式运行前置及 UDP 接口参考。 |
| [KCD Cheat](https://github.com/pryans/kcd-cheat) · [1.58 release](https://github.com/pryans/kcd-cheat/releases/tag/1.58) · [Nexus Mod 106](https://www.nexusmods.com/kingdomcomedeliverance/mods/106) | GitHub owner [pryans](https://github.com/pryans); release manifest credits **spraguep**. The Nexus page currently credits [Othiden](https://next.nexusmods.com/profile/Othiden?gameId=2298). These are recorded as published credits, without assuming they are the same identity. | Used as the private prototype's Lua loader and as an API/debugging reference. The public standalone package does not include or require Cheat. / 早期原型加载器与游戏接口探测参考，公开版不再依赖或分发它。 |
| [How-to Lua — Nexus 1344](https://www.nexusmods.com/kingdomcomedeliverance/mods/1344) | **dataframe - benjaminfoo**, as credited on the tutorial; [Nexus author profile](https://www.nexusmods.com/kingdomcomedeliverance/users/75447573) · [GitHub](https://github.com/benjaminfoo) | Reference for KCD's Startup scripts and scene-loading UI notification. No tutorial files or assets are redistributed. / 独立 Lua 启动及读档事件机制参考。 |
| [KCD Coding Guide](https://github.com/benjaminfoo/KCD-Coding-Guide) | [benjaminfoo](https://github.com/benjaminfoo) | Additional Lua/game scripting and PAK layout reference. / Lua 与 PAK 结构参考。 |

The Cheat source inspected during prototyping was commit [1a51a13a332669db49adf042789b3a9ebbf00009](https://github.com/pryans/kcd-cheat/commit/1a51a13a332669db49adf042789b3a9ebbf00009). The original release was Cheat-NOKEYS 1.58. Credits do not imply endorsement or permission to redistribute upstream files.

## Runtime, build and tests / 运行库、构建与测试

| Project | Authors / maintainers | Role |
| --- | --- | --- |
| [CPython](https://github.com/python/cpython) · [Python](https://www.python.org/) | Python Software Foundation and CPython contributors | Python 3.12 runtime bundled in the EXE. |
| [Tcl](https://github.com/tcltk/tcl) · [Tk](https://github.com/tcltk/tk) | Tcl/Tk authors and maintainers | Tkinter GUI runtime bundled in the EXE. |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | PyInstaller Development Team / contributors | Portable Windows executable build and bootloader. |
| [Lupa](https://github.com/scoder/lupa) | [Stefan Behnel / scoder](https://github.com/scoder) and contributors | Development tests execute Lua 5.1 telemetry against Python; not bundled in the player EXE. |

Bundled runtime license notices are in `runtime-licenses/`; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Original KCDDSX code has its own [MIT license](LICENSE); it does not relicense any of these projects.

Kingdom Come: Deliverance and its Lua APIs belong to Warhorse Studios and the respective rights holders. DualSense belongs to Sony. KCDDSX is an independent community project.

## AI assistance / AI 辅助披露

Most original KCDDSX code and documentation were generated with OpenAI Codex and refined using automated tests and player feedback. The Nexus promotional cover was AI-generated. This disclosure does not claim authorship of upstream projects or permission to redistribute their content. / 绝大部分原创代码与文档由 OpenAI Codex 编写，结合自动测试与玩家反馈迭代；Nexus 宣传封面由 AI 生成。此披露不改变上游作者署名、许可或素材权利。
