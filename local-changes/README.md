# local-changes —— 从参考库提取的本地修改

2026-10-09 按「参考库只读」规则，把此前混入参考目录的本地修改提取到这里，三个参考目录已还原为上游原样（逐文件哈希校验记录见根目录 [PROGRESS.md](../PROGRESS.md)）。

**这里只是存档，不是可运行工程。** 如需恢复 A 训练环境，把对应文件按相对路径复制回 `microduck-build-tutorial/` 即可；注意 `export_onnx.py` 内硬编码的 `/mnt/e/` 路径与 WSL venv 路径是 E 盘时代写的，工程已迁到 `C:\Projects\duck-robot`，复用前必须先改。

## microduck-replica/

- `调试记录.md`：上游版 + 7 行本地到货记录（2026-10-09 会话误写入上游文档）。用户相关内容已转录到根 PROGRESS.md「2026-10-09 硬件到位」；此份仅作原样留存。

## microduck-build-tutorial/

A 训练重建时的库内修改（背景见根 README「方案 A」一节与 [docs/a-training.md](../docs/a-training.md)）：

| 文件 | 性质 |
|---|---|
| `mjlab_microduck/.gitignore` | 修改：放开 `uv.lock` 版本化、忽略项从 `xxx/*` 改 `xxx/` |
| `mjlab_microduck/pyproject.toml` | 修改：依赖版本钉死（torch 2.9.1 / mujoco 3.10.0 / BAM rev 锁定等） |
| `mjlab_microduck/src/mjlab_microduck/scripts/export_onnx.py` | 重写：安全导出（显式 checkpoint/output、奇偶校验），含 `/mnt/e/` 硬编码路径 |
| `mjlab_microduck/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py` | 修改：命令课程按 dataclass 重建、reset 高度、3000/6000 iteration 速度扩展等 |
| `mjlab_microduck/README.md`、`mjlab_microduck/scripts/validate_contract.py` | 新增：A 训练说明与 51/14 合同检查脚本 |
| `mjlab_microduck/uv.lock` | 新增：钉死环境的锁文件 |
| `mjlab_microduck/src/mjlab_microduck/robot/`（49 文件） | 新增：官方 [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl) @ `cb70b792312d559a4da09064d92009079671815f` 的模型恢复树，含 `source_manifest.json` 与 `provenance/` 溯源 |
