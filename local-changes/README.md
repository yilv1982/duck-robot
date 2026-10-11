# local-changes —— 从参考库提取的本地修改

2026-10-09 按「参考库只读」规则，把此前混入参考目录的本地修改提取到这里，三个参考目录已还原为上游原样（逐文件哈希校验记录见根目录 [PROGRESS.md](../PROGRESS.md)）。

**这里只是存档，不是可运行工程。** 2026-10-10 三个上游参考库已移至根目录 `references/`；本目录中的提取件路径保持不变。如需恢复 A 训练环境，应先取得修改只读参考库的明确授权，再按相对路径恢复到 `references/microduck-build-tutorial/`，或建立独立可写副本；`export_onnx.py` 的旧 `/mnt/e/` 与 venv 路径必须按当前环境改写，不能直接运行。

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
