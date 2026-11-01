# KCDDSX 自适应扳机

为《**天国：拯救 1**》加入 DualSense 自适应扳机反馈，需要运行 **DSX**。[English](README.md)

## 下载与 Nexus 审核

Windows **0.5.0** 主文件已**通过 Nexus Mods 人工审核**，可在 [Nexus Files 页面](https://www.nexusmods.com/kingdomcomedeliverance/mods/2448?tab=files)正常下载，也可使用 [GitHub Release](https://github.com/anverse01/kcd1-dualsense-dsx/releases/tag/v0.5.0)。两处提供相同的 Windows ZIP，安装包及已发布校验值均未改动。

玩家安装包位于 **Releases**。GitHub 自动生成的 **Source code** 下载是源码，不能直接当作游戏 Mod 安装。源码及构建步骤公开供审阅与自行构建；发布的校验值用于识别原始上传文件，自行重新构建不保证字节完全相同。

本项目绝大部分原创代码与文档由 **OpenAI Codex** 生成，再结合自动检查及玩家实机测试迭代；Nexus 封面使用 AI 绘图。AI 辅助不替代原项目许可要求或功能验证，详见[原作者致谢](CREDITS.md)、[第三方声明](THIRD_PARTY_NOTICES.md)与[验证范围](docs/VALIDATION.md)。

| 场景 | 扳机反馈 |
| --- | --- |
| 持弓，还没拉弓 | R2 已有 3/8 基础阻力 |
| 拉弓到 ReadyToFire 阶段 | R2 增强到 4/8 |
| 取消拉弓或放箭 | 回到持弓 3/8 基础阻力 |
| 拔出近战武器或空手 | 体力低于 80% 后，L2、R2 随体力降低逐级变紧，最高 6/8 |
| 恢复体力 | 阻力降低；体力 80%–100% 时不加疲劳阻力 |
| 暂停、对话或超过 2 秒没有游戏状态 | 释放扳机效果 |

## 要求

- Windows 64 位、天国：拯救 **一代**、DualSense 和 [DSX](https://store.steampowered.com/app/1812620/DSX/)。独立 **0.5.0** 已在 Steam 版 **1.9.7 + DSX 3.1.7 + USB DualSense** 上实测：自动加载、持弓/拉弓/取消/放箭、持剑和空拳体力反馈、恢复以及暂停/继续，用户均确认正常。
- DSX 开启“传入 UDP”，默认地址 `127.0.0.1`、端口 `6969`、手柄索引 `0`。接口面向 DSX v3.1+，其他版本尚未验证。
- 使用 DSX 模拟手柄时，关闭本游戏的 **Steam 输入**，避免一次按键触发两次。
- 本 Mod 不要求安装 Cheat、Python、图形注入器，也不要求管理员权限或 `-devmode`。

## 拖放安装

1. 退出游戏，解压 `KCDDSX-0.5.0-Windows.zip`。
2. 把里面的 **KCDDSX** 文件夹拖进游戏的 `KingdomComeDeliverance/Mods/`。
3. 确认路径是 `Mods/KCDDSX/mod.manifest`、`Mods/KCDDSX/Data/kcd_dsx.pak` 和 `Mods/KCDDSX/KCDDSXBridge.exe`。
4. 如果你在使用 `Mods/mod_order.txt`，在其中加入 `KCDDSX` 一行，保留其他条目；没有这个文件则不必创建。
5. 开启 DSX 及其传入 UDP，双击 **KCDDSXBridge.exe**。它会自动识别游戏目录并开始桥接，游玩时保持窗口打开。
6. 启动游戏进入存档，桥接窗口应显示“游戏反馈已连接”。也可在已进入存档后启动桥接，它只读取新状态。

程序有中英文切换按钮。如果把 EXE 移出 Mod 目录，需要手动选择游戏根目录。当前提供手动拖放安装包，Vortex 部署尚未验证。

## 停止、更新、卸载

关闭桥接窗口，或点“停止并还原 DSX”，程序会释放双扳机并发送 DSX 配置还原指令。更新前等待桥接退出。

更新时退出游戏和桥接，只替换 `Mods/KCDDSX`。卸载时退出两者后移除这个文件夹；如果加过 `mod_order.txt` 条目，也移除对应行。桥接偏好保存在 `%LOCALAPPDATA%/KCDDSX/settings.json`，可自行保留或删除。

**早期私人原型用户：**切换前先停用原型写入 Cheat 的自定义加载脚本，并关闭旧 Python 桥接，避免同时输出。不要删除自己另外安装、用于其他功能的 Cheat。公开版不会改写 Cheat。

## 已知限制与排错

- 弓箭按拉弓、ReadyToFire、放箭和取消事件分档，不是连续拉弓百分比。持弓时取消或射箭后仍保留基础阻力。
- 空手疲劳也会在空手行走、冲刺后生效，不限于拳击；独自挥拳时没有可靠的持续举拳标记。
- 优先使用原生 UI 体力比例，失败时以本轮观察到的体力峰值估算；低体力读档可能暂时低估疲劳，恢复到满体力后校准。
- 体力反馈约每 500 毫秒更新；弓箭事件观察到后及时输出。尚未正式测量端到端延迟。
- “等待游戏状态”：进入存档，确认 Mod 启用、游戏根目录 `kcd.log` 在更新，日志中应有 `[KCDDSX] Independent loader` 和状态数据。通常不必添加日志配置。
- DSX 连接失败：检查传入 UDP、端口、USB 手柄连接及手柄索引；如需处理防火墙，使用 DSX 自身的设置。本程序不会修改防火墙。
- 双重输入：关闭本游戏的 Steam 输入，检查是否还运行其他手柄模拟软件。
- 同一手柄同时运行其他扳机控制程序可能冲突。EXE 会防止自身重复开启，但不能阻止无关程序或旧版桥接。
- EXE 尚未签名，可自行从源码构建。没有自动更新或数据上传，网络仅用于本机 DSX UDP 通信。
- 不更改 DLSS、帧生成、画质 DLL/配置、按键、存档、体力数值、物品或战斗平衡。改写玩家回调或关闭游戏日志的 Mod 可能冲突。二代、蓝牙、DualSense Edge 和其他商店版本尚未测试。

源码、构建方法和许可见 [English README](README.md)、[MIT](LICENSE) 与 [第三方声明](THIRD_PARTY_NOTICES.md)。这是社区非官方项目。

## 致谢与来源

感谢 [Paliverse / DSX](https://github.com/Paliverse/DSX)、[pryans / KCD Cheat](https://github.com/pryans/kcd-cheat)（[Nexus 原页](https://www.nexusmods.com/kingdomcomedeliverance/mods/106)），以及 [dataframe / benjaminfoo 的 How-to Lua](https://www.nexusmods.com/kingdomcomedeliverance/mods/1344) 与 [KCD Coding Guide](https://github.com/benjaminfoo/KCD-Coding-Guide)。原作者主页、发布包署名、具体参考用途和运行库/构建/测试项目统一记录在 [CREDITS.md](CREDITS.md)，随安装包与源码一同保留。
