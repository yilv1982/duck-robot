#!/usr/bin/env python3
"""mjlab smoke：自建 duck_v0.xml 进 GPU 场景，批量步进并测吞吐。

对齐语义：IdealPdActuatorCfg（stiffness=25/damping=2/effort_limit=0.94，
armature/frictionloss 取自 1910 BAM 参数表）≈ 我们 CPU 版的位置目标+力矩饱和链。
"""

import time

import mujoco
from mjlab.actuator import IdealPdActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.scene import Scene, SceneCfg
from mjlab.terrains.terrain_entity import TerrainEntityCfg

XML = "models/duck_v0.xml"
NUM_ENVS = 4096


def _duck_spec():
    """加载自建 XML 并清空 XML 内执行器（mjlab 执行器体系接管，避免重名）。"""
    spec = mujoco.MjSpec.from_file(XML)
    for act in list(spec.actuators):
        spec.delete(act)
    return spec

robot = EntityCfg(
    spec_fn=_duck_spec,
    articulation=EntityArticulationInfoCfg(
        actuators=(IdealPdActuatorCfg(
            target_names_expr=(r".*",),
            stiffness=25.0,
            damping=2.0,
            effort_limit=0.94,
            armature=0.00178,
            frictionloss=0.0158,
        ),),
    ),
)

t0 = time.time()
cfg = SceneCfg(
    terrain=TerrainEntityCfg(terrain_type="plane"),
    num_envs=NUM_ENVS,
    entities={"robot": robot},
)
scene = Scene(cfg, device="cuda:0")
compiled = scene.compile()
print(f"编译完成 ({time.time()-t0:.1f}s)")

state = compiled.reset()
print(f"批量重置完成，envs={NUM_ENVS}，qpos 形状 {tuple(state.physics_state.qpos.shape)}")

# 批量步进吞吐
STEPS = 200
t0 = time.time()
for i in range(STEPS):
    state = compiled.step(state, action=None)  # 无动作先测物理裸吞吐
elapsed = time.time() - t0
print(f"物理吞吐: {STEPS*NUM_ENVS/elapsed:,.0f} env-steps/s（{NUM_ENVS} env × {STEPS} 步 / {elapsed:.2f}s）")
