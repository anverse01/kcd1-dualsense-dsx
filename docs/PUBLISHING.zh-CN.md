# 发布材料

本目录是干净的公开源码项目，外层实验工作区中的 references、backups、installation.json、个人日志和本机 Python 路径不会打进源码包。

## Nexus Mods

- 游戏选择：Kingdom Come: Deliverance（一代）。
- 标题：KCDDSX - DualSense Adaptive Triggers via DSX
- 简介：DualSense bow resistance and stamina-based melee/unarmed triggers for KCD1 via DSX. / 通过 DSX 为《天国：拯救1》加入弓箭阻力与近战、空拳体力扳机反馈。
- 版本：0.5.0。
- 主文件：dist/KCDDSX-0.5.0-Windows.zip。
- 可选源码文件：dist/KCDDSX-0.5.0-Source.zip。
- 双语正文：docs/NEXUS_DESCRIPTION.bbcode，已合并为英文在前、中文在后，底部共用原作者致谢；复制到同一个 Mod 页面的正文编辑器，发布前预览排版。
- 安装包自带中英文界面与说明，一个主文件即可，不需要按语言重复创建页面或上传相同文件。
- 可直接复制的上传字段：docs/NEXUS_UPLOAD_FIELDS.txt。
- 原作者与来源：CREDITS.md；安装包、源码、中英文 README 和 Nexus 正文均保留来源链接。
- 外部前置：DSX，链接 https://store.steampowered.com/app/1812620/DSX/ 。不把 Cheat 列为前置。
- 作者名：当前文件中使用 KCDDSX contributors，可在发布前按你的公开署名统一调整。
- 权限：本项目原创源码采用 MIT；第三方组件不属于该许可，完整声明见包内文件。
- 上传 SHA256SUMS.txt 便于核对下载文件。
- 标签：根据实际可选项添加 English、Chinese 及相关手柄/界面标签。按 [Nexus 文件提交规则](https://help.nexusmods.com/article/28-file-submission-guidelines)，本项目的生成式 AI 代码/界面适用 AI-Generated Content；页面文案及计划使用的 ChatGPT 生成封面适用 AI Media。发布时按实际内容选择这些标签。
- 封面：用户已提供 KCD1_DualSense_Adaptive_Triggers_Nexus_Cover_Side_Final.png，用作 Nexus 图库缩略图；不会写入运行所需的 PAK。

独立 0.5.0 的本轮进游戏验证已完成，用户确认正常，结果见 docs/VALIDATION.md。Nexus 页面已发布于 https://www.nexusmods.com/kingdomcomedeliverance/mods/2448 ，已添加 AI-Generated Content 与 AI Media 标签。Windows 主文件 10522 被自动安全检查隔离，人工复核申请已提交，结果待定；源码文件 10523 可下载。页面顶部已添加中英文等待复核提醒。保留原始上传文件，勿以重新打包或更名规避隔离。

## GitHub

建议仓库名：kcd1-dualsense-dsx。

上传本项目目录中的源码、说明、LICENSE、tests、tools 和 .github；不要上传 build、dist 或本机配置，.gitignore 已排除它们。也可以直接解压 Source.zip 作为初始仓库内容。

仓库简介：DualSense adaptive triggers for Kingdom Come: Deliverance 1 via DSX.

建议 Topics：kingdom-come-deliverance, dualsense, dsx, adaptive-triggers, mod, lua, python。

Actions 在推送和 PR 时运行测试。只有手动触发并勾选 build_windows 时才构建 Windows 包，产物保存在 workflow artifacts；不会自动公开发布。GitHub Release 可附原始 Windows ZIP 与 SHA256SUMS.txt，并必须同时说明 Nexus 隔离、人工复核待定和检测结果，不得将 GitHub 可下载表述为安全审核通过。GitHub 自动提供的源码下载与玩家安装包应明确区分。

## 发布前最后核对

- 独立版加载与 EXE 共同工作，旧原型已停止。
- 拖放目录正确，没有多嵌套一层。
- 弓、取消、放箭、剑、空拳、恢复、暂停和再次读档均正常。
- 本轮 VALIDATION.md、两份 README 和 Nexus 正文已更新为实测结果；以后每版按实际测试情况更新。
- 确认自己希望使用的公开署名及 MIT 许可。
- 检查压缩包内容与 SHA256，不包含存档、个人日志、游戏源码或第三方 Mod。
