# Microduck 显示资产来源（2026-10-21）

本目录为用户同意复用的 **显示层**：38 个原始 STL、38 个材质及 70 个外观 geom 的局部挂接数据。作者为 **Pollen Robotics**，上游为 [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl)。显示的是上游 Microduck / XL330 外观，包含 `xl330`、`np_f970`、Pi Zero 与原版 HAT 等部件，**不是本机 C 线 HD-1910 的精确 CAD 或制造文件**。

来源路径：`references/microduck-replica/software/training/src/mjlab_microduck/robot/microduck/robot_walk.xml` 及同级 `assets/`。参考库 `software/training/UPSTREAM.md` 记载固定导入快照为 [fanhao375/microduck_rl @ d9e1926c5220a0eb79fa5aab9df7b336f8e9a226](https://github.com/fanhao375/microduck_rl/tree/d9e1926c5220a0eb79fa5aab9df7b336f8e9a226)，Pollen 上游基线为 `d424a0c899f6b33cbd3daeb279913134349c0b63`。这是来源文档记录的快照；本次实际复制文件的 SHA-256 以 [manifest.json](manifest.json) 为准。

原模型 XML 注明由 onshape-to-robot 生成，CAD 入口为 [Onshape Microduck](https://cad.onshape.com/documents/804927696f06d877f3f1803e/w/5b75db19292e71970de02dee/e/ef6e972847fec8d82570b35e)。本轮未下载其他 CAD，未修改只读参考库。

## 许可与署名

上游 `README.upstream.md` 第 212 行原文：

> 3D model files are licensed under Creative Commons BY-SA-NC.

上游这句话未单独写明版本；本地参考库 `NOTICE.md`「许可证名称说明」按 **CC BY-NC-SA 4.0（署名—非商业性使用—相同方式共享）**保留模型许可。本目录沿用该说明。模型和显示派生物不因代码使用 Apache-2.0 而变成 Apache-2.0。许可链接：[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)、[法律文本](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)。

需保留作者、来源、许可和改动说明；衍生模型沿用相同方式共享与非商业性使用条件。原模型署名和许可摘录也保存在 [manifest.json](manifest.json)，不依赖参考库可用性。

## 本项目改动与使用范围

- STL 原样复制，未简化、重采样或改变尺寸；材质保留原始 RGBA，无外部纹理。资产总量 21,590,692 字节（20.59 MiB），独立三角面 431,750；70 次实例化合计 796,792 面。
- 只提取 `class="visual"` 的 geom 及其局部 `pos/quat/mesh/material`；没有复制上游动力学 body、joint、inertial、actuator、sensor、contact 或默认参数。
- 15 个 body 与本项目自建模型同名同层级；14 个非根 body 的局部位姿一致。根 body 保留自建模型高度 `0.1182 m`，没有覆盖为上游的 `0.12 m`。长度为米、角度为 rad、四元数为 wxyz，无额外 mesh scale。
- `duck_visual.xml` 由 [build_visual_model.py](../../scripts/build_visual_model.py) 从自建 `duck_v0.xml` 和本目录 manifest 生成。新增外观在 group 2，`contype=conaffinity=0`、`density=mass=0`；原碰撞体只移到显示 group 3，地面仍为 group 0。
- 显示版增强相机随动光并增加一盏方向光，便于看清深色连杆与壳体细节；灯光仅影响渲染。
- 保留自建模型的质量、惯量、关节、碰撞、执行器和 HOME。仍为 14 个受控关节；上游嘴部外观固定挂在 `jaw_soft`，没有增加第 15 个 mouth 关节或改策略接口。
- 训练默认继续使用 `duck_v0.xml`。显示模型只能改善观察外观，不表示物理参数已与本机实物对齐；默认查看外观时隐藏 group 3，调试时可切换碰撞层。

重新生成只需本项目文件：`python training/scripts/build_visual_model.py`。脚本核验本地资产 SHA-256 及 body 挂接契约，不再读取 `references/`。
