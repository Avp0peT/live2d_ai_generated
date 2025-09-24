## Live2D 生成式模型项目计划（v0.2）

### 背景与目标
- 利用 `live2d_v4/` 中的既有 Live2D 模型数据集，训练生成式模型，自动生成“可直接使用”的新 Live2D 模型资源。
- 生成结果需满足 Live2D 规范，可在 Viewer/SDK 中正常加载与播放（眨眼/口型同步/物理等按需支持）。

参考规范：Live2D 文件类型与扩展名，包含 `.moc3`、`.model3.json`、`.physics3.json`、`.motion3.json` 等说明（见文末链接）。

### 成果物（Definition of Done）
1. 最小可用：基于现有 `.moc3`（起步复用，见扩展），自动生成一套新纹理（`*.png`）、打包新的 `*.model3.json`，可在 Cubism Viewer/Unity/Web SDK 正常显示与基本参数驱动。
2. 扩展能力：可选自动生成/导出新的 `.moc3`（通过 Editor 外部集成自动化），以及自动生成 `.motion3.json`（动作曲线），并支持 `.exp3.json`（表情）与 `.pose3.json`（姿势）产物。
3. 校验通过：
   - `*.model3.json` 引用资源存在且路径正确；
   - 纹理尺寸/通道/透明度与 `.moc3` 网格 UV 对齐，无明显破面与拉伸；
   - 可加载并截图验证，不崩溃、无必需文件缺失。
4. 动作可用：`.motion3.json` 参数 ID 与模型一致；曲线平滑、无跳变，支持循环/非循环标记；（可选）口型与音频对齐。
5. 物理可用（可选）：`.physics3.json` 合理，发丝/服饰无明显抖振或穿模。
6. 可复现：一键脚本从输入数据集批量生成目标模型，并输出日志与验证报告。

### 范围界定
- MVP 阶段：复用模板 `.moc3`，自动生成纹理与 `.model3.json`，并支持基础动作 `.motion3.json` 生成。
- 进阶阶段：通过 Editor 外部集成 API 自动化导出新的 `.moc3`（或 `.cmo3`→`.moc3`），并自动生成 `.exp3.json`、`.pose3.json`、`.physics3.json`。

### 数据资产与目录规范
- 输入根目录：`live2d_v4/`（已存在）
- 建议新增目录：
  - `data/raw/`：原始拷贝（可选，保持只读）
  - `data/processed/`：扫描与标准化后的中间数据（元数据 JSON、参数映射、纹理掩膜等）
  - `experiments/`：实验配置与权重
  - `outputs/`：最终可用模型，每个模型一个子目录，包含 `model3.json`、`*.moc3`（复用）、`textures/*.png`、`physics3.json`（可选）、`motions/`（可选）
  - `reports/`：质量报告、可视化、对比截图

### 技术路线
1. 模板保持（MVP，推荐起步）
   - 复用既有 `.moc3` 与参数 ID 体系；
   - 以“保持 UV/透明度/边界一致”为约束，生成与原纹理同版式的贴图集（Atlas）新内容（风格/配色/细节）；
   - 产出新的 `model3.json` 指向新纹理，可选更新默认参数与物理配置；
   - 优点：100% 兼容，立刻可用；缺点：几何形态变化受限。
2. 进阶：几何变体（可选）
   - 学习可逆形变场（例如 Thin-Plate Spline/神经形变）在网格顶点级做小幅变形；
   - 需要在 Editor 中复核与导出 `.moc3`（可探索外部集成 API 批处理）。

### 模型（.moc3/.cmo3）生成方案（扩展）
1. Editor 自动化导出流（推荐）
   - 基于“外部应用程序的集成功能 / 外部集成 API”，以自动化脚本驱动 Cubism Editor：
     - 打开模板 `.cmo3` 或创建新工程；
     - 应用 ML 模型输出的网格顶点偏移/变形器参数（格式：`artmesh_id -> {vertices: [...], deformers: {...}}`）；
     - 更新参数初值/范围（如需要）；
     - 批量导出 `.moc3` 与纹理、`model3.json`。
   - 优点：规避直接写入 `.moc3` 二进制的兼容风险；保持与 Editor 同步的正确性。
2. 形变-保拓扑策略
   - 起步保持 ArtMesh 拓扑与 UV 不变，仅修改默认顶点坐标与变形器绑定；
   - 通过参数“姿态锚点”学习（如 `Yaw/Pitch` 极值、`EyeOpen`/`MouthOpen` 端点）回归对应形状，再由 Editor 插值生成中间帧；
3. 拓扑微调（可选）
   - 限定区域内进行顶点增删与网格细化，生成差分脚本由 Editor 应用后再导出；
   - 需要更严格的重叠/穿模检测与蒙版同步修正。

产出：新的 `.moc3`、配套 `textures/*.png` 与 `model3.json`（必要时同步更新 `Groups`/`HitAreas`）。

### 训练与预处理流水线
1. 模型扫描与元数据抽取（Python）
   - 遍历 `live2d_v4/**/`，读取 `*.model3.json`：
     - `FileReferences.Moc`、`Textures[]`、`Physics`、`Motions`、`Expressions`、`Groups`、`HitAreas`；
     - 提取参数 ID（如 `ParamAngleX`、`ParamEyeLOpen` 等）。
   - 生成清单：`data/processed/index.json`（每个样本的一致视图）。
2. 纹理标准化
   - 读取 `Textures[]`，保持分辨率与版式不变；导出 alpha 掩膜、连通域、部件边界框；
   - 可选：统一色域（sRGB）、像素格式（PNG、直通 alpha）。
3. 条件与标签
   - 从文件夹/命名/用户提供标签派生风格标签（发色、服饰风格、主题等）；
   - 自动抽取调色板与材质特征（皮肤、发、布料、金属等区分域）。
4. 数据增强
   - 保形增强：色相/明度/纹理微扰，不改变 alpha 边界与结构；
   - 纹理域随机化：细节噪声、笔触风格、图案替换（在掩膜内）。
5. 模型训练（推荐先从轻量开始）
   - 纹理风格子模型：条件 VAE/LoRA + 版式保持（以原贴图为布局条件），或面向贴图切片的扩散模型；
   - 物理/参数默认值回归（可选）：轻量回归头预测默认参数、眨眼/口开闭阈值；
   - 统一以 PyTorch 实现，保存权重与推理配置。

6. 动作数据集构建（新增）
   - 从 `*.motion3.json` 抽取参数时间序列（采样到 30/60 FPS），对不同模型做参数 ID 对齐（按标准参数优先，如 EyeBlink、Angle、BodyAngle 等）；
   - 序列切片与模板聚类（闲置/呼吸/待机、挥手、点头等），形成可条件化的动作标签；

7. 动作生成模型（新增）
   - 序列到序列（Transformer/RNN）预测参数曲线与缓动（可量化到关键帧+Bezier）；
   - 可选语音驱动：基于 Mel 频谱/音素对齐生成口型与表情叠加轨；
   - 曲线平滑与边界约束：保持参数范围、速度/加速度限幅、循环一致性校正。

### 生成与打包流水线（MVP）
1. 选择模板 `.moc3` 与其 `model3.json`（可按目标风格/标签检索）。
2. 纹理生成：
   - 输入原贴图与掩膜、风格条件；
   - 输出与原尺寸/版式一致的新 PNG 贴图集；
   - 质量门槛：无穿色、边界对齐、面部关键区域（眼/口/眉）清晰。
3. 可选：参数/物理微调
   - 调整少量默认参数值（如发色变化导致的对比度微调）；
   - 物理 `*.physics3.json` 以模板为基，做小幅系数扰动并回归修正。
4. 打包新的 `model3.json`
   - 复制模板 JSON，更新 `FileReferences.Textures` 路径；
   - 如使用新的 `physics3.json`/`motions`/`expressions`，同步更新引用；
   - 保持 `Groups` 与参数 ID 不变，确保 SDK 可驱动。
5. 验证
   - 结构校验：检查文件存在性、PNG 通道、JSON Schema（自定义校验器）；
   - 运行校验：调用 Viewer/Unity（可脚本化）加载模型并输出截图到 `reports/`；
   - 指标：加载成功率、关键帧截图 PSNR/SSIM 对参考图、人工抽样通过率。

### 生成与打包流水线（扩展：含模型与动作）
1. 模型（`.moc3`）
   - 基于模板工程与 Editor 自动化脚本应用网格/变形器变体；
   - 导出新 `.moc3` 与 `textures/`；
   - 更新 `model3.json` 并对 `Groups`/`HitAreas` 进行一致性检查。
2. 动作（`.motion3.json`）
   - 输入：目标模型参数 ID 列表、动作模板标签（如 idle、wave、nod）、可选音频；
   - 生成：关键帧+缓动（Bezier）或均匀采样曲线；
   - 校正：速度/范围/循环边界与跨参数联动（如眼睑与眼球旋转的耦合）。
3. 表情/姿势/物理
   - `.exp3.json`：生成若干静态参数集（微笑、眨眼、惊讶等），支持权重混合；
   - `.pose3.json`：为手臂/发饰等开关提供互斥分组；
   - `.physics3.json`：按骨架/挂点聚类生成物理组，估计弹簧/阻尼系数并用动作回放进行稳态校准。

### 参考仓库结构（后续脚手架）
```
.
├─ live2d_v4/                 # 已有数据
├─ data/
│  ├─ processed/
│  └─ raw/
├─ experiments/
├─ outputs/
│  └─ <generated_model_name>/ # model3.json, *.moc3(复用), textures/*.png, physics3.json
├─ reports/
├─ scripts/
│  ├─ scan_models.py          # 抽取与索引
│  ├─ build_model_json.py     # 打包新的 model3.json
│  ├─ validate_model.py       # 结构与加载验证
│  └─ export_viewer_snapshot.(py|ps1) # 调用 Viewer/Unity 截图
│  ├─ build_moc3_via_editor.ps1       # 调用 Cubism Editor 外部集成 API，应用变形并导出
│  ├─ generate_motion_json.py         # 生成 .motion3.json（关键帧/Bezier）
│  ├─ generate_physics_json.py        # 生成/微调 physics3.json
│  └─ retarget_params.py              # 参数 ID 映射与一致性检查
├─ train/
│  ├─ dataset.py
│  ├─ train_texture_model.py
│  ├─ infer_texture_model.py
│  ├─ train_motion_model.py
│  └─ infer_motion_model.py
└─ pipeline/
   ├─ generate_model.py       # 端到端生成：模板选择→纹理生成→打包→验证
   └─ generate_full_asset.py  # 扩展：含 moc3 自动化导出 + 动作/表情/物理
```

### 关键脚本清单（实现要求）
1. `scripts/scan_models.py`
   - 输入：`live2d_v4/`
   - 输出：`data/processed/index.json`，每条记录含：模型名、`moc3` 路径、`textures[]`、可选 `physics`、`motions/expressions`、参数 ID 集合。
2. `train/train_texture_model.py`
   - 可从预训练（如通用纹理风格模型/LoRA）开始；
   - 记录实验配置与权重到 `experiments/`。
3. `train/infer_texture_model.py`
   - 保版式生成，与输入贴图尺寸/数量一致；输出到 `outputs/<name>/textures/`。
4. `scripts/build_model_json.py`
   - 复制模板 `model3.json` 并更新 `FileReferences.Textures` 等引用；
   - 写入 `outputs/<name>/model3.json`。
5. `scripts/validate_model.py`
   - 结构校验 + 可选运行时加载校验；
   - 产出 `reports/<name>.json` 与关键截图。

6. `scripts/build_moc3_via_editor.ps1`
   - 启动 Cubism Editor，加载模板 `.cmo3`，应用 `geometry_delta.json`（ML 输出），批量导出 `.moc3`/`model3.json`；
   - Windows PowerShell 自动化，支持无头/最前窗口模式（按 Editor 能力）；

7. `train/train_motion_model.py` & `train/infer_motion_model.py`
   - 训练/推理生成参数时间序列，支持模板条件与音频条件；
   - 输出 `motions/<action_name>.motion3.json`；

8. `scripts/generate_motion_json.py`
   - 将连续曲线压缩为关键帧+Bezier，或按固定间隔采样；
   - 确保参数 ID 与目标模型一致，不存在缺失或多余；

9. `scripts/generate_physics_json.py`
   - 基于部件分组与挂点自动生成物理配置；
   - 用动作回放校正发丝/布料的振幅与阻尼，避免穿模。

### 验证与 CI 要求
- 新提交触发：
  - 运行 `scan_models.py` 的快检；
  - 对最新 N 个生成样本跑 `validate_model.py`；
  - 动作回归：加载生成的 `.motion3.json` 与模型联调，截取关键帧截图与曲线统计（速度、加速度、越界）；
  - 纹理/模型差异可视化：边界错位热图、重叠检测；
  - 附带失败样本的可视化与日志。

### 里程碑与时间排期（示例）
1. 第 1 周：数据扫描与标准化、索引完成；完成最小打包与校验脚本；
2. 第 2–3 周：纹理生成模型 MVP 训练与推理，产出首批可加载样本；
3. 第 4 周：动作生成模型 MVP（至少 idle/呼吸/简单手势），`.motion3.json` 自动打包与验证；
4. 第 5–6 周：Editor 自动化导出 `.moc3` 验证流打通（应用几何微变形并通过加载验收）；
5. 第 7 周：物理与表情/姿势自动化生成；
6. 第 8 周：整体质量门槛、CI 完善与文档化，一键全流程脚本。

### 风险与对策
- 数据异构（不同模型纹理版式/数量差异大）：按模板分簇训练/推理；每簇保持版式一致。
- 参数 ID 不一致：建立跨模型 ID 映射表，仅在同簇内复用；
- 纹理错位/边界渗色：使用 alpha 掩膜与边界 feather，增加结构保真损失；
- `.moc3` 自动化依赖 Editor：确保许可合规与可脚本化环境，提供手工兜底流程；
- 动作不稳定/眩晕感：速度/加速度限幅与平滑滤波、循环边界连续性校正；
- 版权与许可：仅使用授权数据训练；生成物标注来源与许可证；
- 运行环境差异：固定依赖版本并提供锁定文件，附带最小示例与截图验证脚本。

### 开发环境与依赖（建议）
- Python 3.10/3.11，PyTorch 2.3+，torchvision，opencv-python，Pillow，numpy，tqdm，pydantic（JSON 校验）；
- Live2D Cubism Editor 5（用于 `.cmo3`→`.moc3` 自动导出与外部集成）；
- 可选：Unity + Cubism SDK for Unity（用于加载与截图），或 Web SDK 轻量验证；
- 工具：`pre-commit`、`ruff`/`flake8`、`black`（代码质量，可按仓库风格调整）。

### 附录：最小 `model3.json` 示例（MVP 打包）
```json
{
  "Version": 3,
  "FileReferences": {
    "Moc": "model.moc3",
    "Textures": [
      "textures/texture_00.png",
      "textures/texture_01.png"
    ],
    "Physics": "physics3.json"
  },
  "Groups": [
    {
      "Target": "Parameter",
      "Name": "EyeBlink",
      "Ids": ["ParamEyeLOpen", "ParamEyeROpen"]
    }
  ],
  "HitAreas": []
}
```

### 附录：最小 `motion3.json` 示例（关键帧采样版）
```json
{
  "Version": 3,
  "Meta": {
    "Duration": 2.0,
    "Fps": 30,
    "Loop": true
  },
  "Curves": [
    {
      "Target": "Parameter",
      "Id": "ParamAngleX",
      "Segments": [
        0.0, 0.0,
        1, 1.0, 15.0,
        1, 2.0, 0.0
      ]
    },
    {
      "Target": "Parameter",
      "Id": "ParamEyeLOpen",
      "Segments": [
        0.0, 1.0,
        1, 0.5, 0.0,
        1, 1.0, 1.0,
        1, 1.5, 0.0,
        1, 2.0, 1.0
      ]
    }
  ]
}
```

### 参考链接
- Live2D 文件类型与扩展名（Cubism Editor 5 手册）：https://docs.live2d.com/zh-CHS/cubism-editor-manual/file-type-and-extension
- 参数控制器（说明动作曲线与控制器关系）：https://docs.live2d.com/zh-CHS/cubism-editor-manual/about-the-parameter-controller/



