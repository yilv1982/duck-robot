# banana PCB 来源与打开说明

- 来源：[jyg9/microduck-community-kit](https://github.com/jyg9/microduck-community-kit/tree/0a73426c084ae5a94cdedf5d2be0e3ff5134334d/hardware/banana_pcb)。
- 固定提交：0a73426c084ae5a94cdedf5d2be0e3ff5134334d。
- 下载日期：2026-10-08（Asia/Shanghai）。
- 原目录全部 7 个文件原样保留，包括 KiCad 工程、原理图、PCB、Gerber 制造包、说明、图片和硬件许可证。
- 每个下载文件已按 GitHub 的 Git blob SHA-1 和字节数核验；SHA-256 记录见 source-manifest.json。
- 硬件许可证见 LICENCE.txt；仓库根 LICENSE 另存为 UPSTREAM-REPOSITORY-LICENSE.txt。不同范围的许可不得混同。

## 打开

使用 KiCad 打开 banana_pcb.kicad_pro；双击工程中的 banana_pcb.kicad_pcb 进入 PCB 编辑器。
原工程由 KiCad 9 创建。本机安装 KiCad 10.0.7；保存可能升级文件格式，编辑前建议另存副本。
本次下载与打开不修改原设计，不代表通过 DRC、生产审查或实物适配验证。

## 使用边界

这是社区电池取电转接板，不是已确认的 Pollen 官方原版。与本项目既有 A/B 方案独立保存，不自动并入任何方案。
接线前须核对实物极性、插针间距、绝缘与载流能力；该板本身不提供降压、充电或保险保护。
