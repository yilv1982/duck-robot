# SPDX-License-Identifier: Apache-2.0
"""Minimal A-training model; upstream XML/assets are kept byte-for-byte intact.

BAM doc is pinned to 0007411bd82c48f1bc12ae8382f98e4d8b879c95 by the
training environment. It replaces XML damping/friction with its fixed m6
friction model; do not layer MuJoCo friction randomization on top of it.
"""

from pathlib import Path

import mujoco
from bam.mjlab import BamActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.utils.spec_config import CollisionCfg

MICRODUCK_WALK_XML = Path(__file__).parent / "microduck" / "robot_walk.xml"

# Model-space radians in the same order as A deployment OBSERVATION_DOF_ORDER.
# Hardware knee zero offsets (+/-45 degrees) belong ONLY to the motor driver.
JOINT_ORDER = (
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    "neck_pitch", "head_pitch", "head_yaw", "head_roll",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
)
HOME_POSE = (
    0.0, -0.087, -0.458, -0.005, 0.453, 0.349, 0.349, 0.0, 0.0,
    0.0, 0.087, 0.458, 0.005, -0.453,
)


def get_walk_spec() -> mujoco.MjSpec:
    """Return a fresh spec: Entity/BAM mutate it when building each environment."""
    return mujoco.MjSpec.from_file(str(MICRODUCK_WALK_XML))


HOME_FRAME = EntityCfg.InitialStateCfg(
    # reset_base adds only (0.0, 0.01) m to this absolute initial height.
    pos=(0.0, 0.0, 0.12),
    joint_pos=dict(zip(JOINT_ORDER, HOME_POSE, strict=True)),
    joint_vel={".*": 0.0},
)

BAM_ACTUATOR_CFG = BamActuatorCfg(
    target_names_expr=JOINT_ORDER,
    motor_name="xl330",
    model="m6",
    kp_fw=125,
    vin=5.0,
    vin_range=(4.5, 5.5),
    max_current=1.75,
    vin_drop_gain_range=(0.0, 0.0),
    vin_min=4.5,
    delay_min_lag=0,
    delay_max_lag=0,
)

FEET_COLLISION_CFG = CollisionCfg(
    geom_names_expr=("left_foot_collision", "right_foot_collision"),
    condim=3,
    priority=1,
    friction=(1.0,),
    # Keep upstream's three self_collision_only geoms and their contact masks.
    disable_other_geoms=False,
)

MICRODUCK_ROBOT_CFG = EntityCfg(
    spec_fn=get_walk_spec,
    init_state=HOME_FRAME,
    collisions=(FEET_COLLISION_CFG,),
    articulation=EntityArticulationInfoCfg(
        actuators=(BAM_ACTUATOR_CFG,),
        soft_joint_pos_limit_factor=0.9,
    ),
)
