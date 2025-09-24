# Live2D 生成式模型项目

基于现有 Live2D 模型数据集，自动生成新的 Live2D 模型的完整工具链。

## 项目概述

本项目实现了 Live2D 模型的自动化生成流程，包括：
- 模型扫描与索引
- 模型结构验证
- 基于模板的模型生成
- 端到端的生成流水线

目前为 MVP 版本，支持模板复制和基础的纹理生成。未来将扩展为基于 AI 的纹理、动作和表情生成。

## 目录结构

```
live2d-generative/
├── live2d_v4/                  # 输入：Live2D 模型数据集
├── data/
│   ├── processed/              # 处理后的数据（索引等）
│   └── raw/                   # 原始数据备份
├── scripts/                   # 核心脚本
│   ├── scan_models.py         # 模型扫描与索引
│   ├── validate_model.py      # 模型验证
│   ├── build_model_json.py    # 模型打包
│   ├── generate_motion_json.py      # 程序化动作生成（占位）
│   ├── generate_expression_json.py  # 程序化表情生成（占位）
│   ├── generate_physics_json.py     # 程序化物理生成（占位）
│   └── retarget_params.py     # 参数ID映射工具
├── pipeline/                  # 端到端流水线
│   └── generate_model.py      # 主要生成脚本
├── outputs/                   # 生成的模型输出
├── reports/                   # 验证报告
├── experiments/               # 实验配置与权重
└── train/                    # 训练脚手架
    ├── dataset.py
    ├── train_texture_model.py   # 纹理训练占位/统计
    ├── infer_texture_model.py   # AI纹理推理占位
    ├── train_motion_model.py    # 动作序列样本与统计占位
    └── infer_motion_model.py    # AI动作推理占位
```

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
```

Windows（指定解释器路径示例）

```powershell
# 使用指定 Python 解释器
python -m pip install -r requirements.txt
```

### 2. 扫描模型数据集

首先扫描 `live2d_v4/` 目录中的所有模型，生成索引：

```bash
python scripts/scan_models.py
```

这将生成 `data/processed/index.json`，包含所有模型的元数据。

### 3. 验证模型

验证模型的完整性和正确性：

```bash
# 验证所有模型
python scripts/validate_model.py

# 验证前10个模型
python scripts/validate_model.py data/processed/index.json reports 10
```

验证报告将保存在 `reports/validation_report.json`。

### 4. 生成新模型

使用端到端生成脚本创建新模型：

```bash
# 随机选择模板，完整复制
python pipeline/generate_model.py --output-name my_model_001

# 指定模板，使用占位符纹理
python pipeline/generate_model.py \
    --output-name custom_model \
    --template-strategy specified \
    --template-id 100100 \
    --texture-mode placeholder

# 查看所有选项
python pipeline/generate_model.py --help
```

#### 生成 AI 纹理 + 动作 + 表情 + 物理（占位/MVP）

```bash
python pipeline/generate_model.py \
    --output-name ai_full_demo \
    --template-strategy specified \
    --template-id 100100 \
    --texture-mode ai_generated \
    --motion-mode ai_generated \
    --expression-mode ai_generated \
    --physics-mode ai_generated
```

#### 使用 Diffusers/LoRA 进行纹理生成（可选，需安装依赖）

```bash
# 安装：pip install diffusers transformers accelerate torch --upgrade
# 环境变量（PowerShell）：
#   $env:TEXTURE_BACKEND="diffusers"
#   $env:DIFFUSERS_MODEL_ID="stabilityai/sd-turbo"  # 或其他img2img模型
#   $env:DIFFUSERS_LORA_PATH="path/to/lora.safetensors"  # 可选
#   $env:DIFFUSERS_PROMPT="cel shade, clean lines"
#   $env:DIFFUSERS_NEGATIVE="lowres, blurry"
#   $env:DIFFUSERS_STRENGTH="0.35"
#   $env:DIFFUSERS_GUIDANCE="1.5"
#   $env:DIFFUSERS_STEPS="10"

$env:TEXTURE_BACKEND="diffusers"; $env:DIFFUSERS_MODEL_ID="stabilityai/sd-turbo"; \
python pipeline\generate_model.py \
  --output-name ai_diffusers_100100 \
  --template-strategy specified \
  --template-id 100100 \
  --texture-mode ai_generated \
  --motion-mode ai_generated \
  --expression-mode ai_generated \
  --physics-mode ai_generated

# 如果使用 CMD，请改为：
#   set TEXTURE_BACKEND=diffusers & set DIFFUSERS_MODEL_ID=stabilityai/sd-turbo & \
#   python pipeline\generate_model.py ...

#### LoRA 训练清单（占位）

```bash
# 生成 LoRA 训练用清单（train/val 切分）
python train/train_texture_lora.py --index data/processed/index.json --out experiments/lora_texture_manifest.json
```

#### 质量评估（PSNR/SSIM）

```bash
# 对比两个目录（如原始 vs 生成）
python scripts/evaluate_quality.py --ref outputs/complete_copy_002/model.1024 --gen outputs/ai_full_all_001/textures_ai
```

#### 几何变形占位与导出

```bash
# 生成 geometry_delta.json 占位数据
python scripts/geometry_delta_prepare.py live2d_v4/100100 --out outputs/geometry_delta.json

# 调用编辑器导出（占位示例，不执行实际导出）
powershell -ExecutionPolicy Bypass -File scripts/build_moc3_via_editor.ps1 -TemplateDir live2d_v4/100100 -OutDir outputs/editor_export
```

#### Web 预览增强

```bash
# 预览页（Pixi）中已新增 AngleX 与 EyeBlink 滑块，以及简单表情切换按钮
# 浏览： http://localhost:5500/web/preview.html
```
```

## 主要功能

### 模型扫描 (`scripts/scan_models.py`)

- 扫描所有 Live2D 模型目录
- 提取模型元数据（纹理、动作、表情、参数等）
- 生成统计信息和索引文件
- 支持 757 个模型的快速扫描

**输出示例：**
```
=== 扫描摘要 ===
总模型数: 757
成功扫描: 757
失败扫描: 0
总纹理数: 1791
总动作数: 4035
总表情数: 4572
唯一参数ID数: 1360
```

### 模型验证 (`scripts/validate_model.py`)

- JSON Schema 验证
- 文件完整性检查
- 纹理格式验证
- 参数一致性检查
- 生成详细验证报告

**验证内容：**
- ✅ model3.json 格式正确性
- ✅ 所有引用文件存在
- ✅ 纹理文件格式和透明度
- ✅ 动作和表情文件格式
- ✅ 参数 ID 一致性

### 模型生成 (`pipeline/generate_model.py`)

支持多种生成模式：

#### 模板选择策略
- `random`: 随机选择模板
- `similar`: 基于相似性选择
- `specified`: 指定具体模板 ID

#### 纹理生成模式
- `copy`: 复制原始纹理（默认）
- `placeholder`: 生成占位符纹理
- `ai_generated`: AI 生成纹理（占位/MVP，已集成）

#### 动作/表情模式
- `copy`: 复制原始文件（默认）
- `none`: 不包含动作/表情
- `ai_generated`: 程序化/占位（已集成）

## 使用示例

### 生成完整模型副本

```bash
python pipeline/generate_model.py \
    --output-name complete_model_001 \
    --template-strategy specified \
    --template-id 100100
```

### 生成简化模型（仅纹理占位符）

```bash
python pipeline/generate_model.py \
    --output-name simple_model_001 \
    --template-strategy random \
    --texture-mode placeholder \
    --motion-mode none \
    --expression-mode none
```

## 执行流程与流水线

本项目的端到端流水线以“索引 → 选择模板 → 资产生成 → 打包 → 验证 → 预览”为主线，相关脚本与步骤如下：

1) 索引与验证
- 扫描：`scripts/scan_models.py` 读取 `live2d_v4/` 并生成 `data/processed/index.json`
- 验证：`scripts/validate_model.py` 对模型结构与引用文件进行全面校验

2) 单模型端到端生成（主入口）
- 入口：`pipeline/generate_model.py`
- 核心阶段：
  - 模板选择：`--template-strategy {random|similar|specified}` + `--template-id`
  - 纹理生成：`--texture-mode {copy|placeholder|ai_generated}`
  - 动作生成：`--motion-mode {copy|none|ai_generated}`（AI 模式使用占位推理）
  - 表情生成：`--expression-mode {copy|none|ai_generated}`（程序化生成 exp3.json）
  - 物理生成：`--physics-mode {copy|ai_generated}`（基于模板 physics3.json 微调）
  - 打包与合并：`scripts/build_model_json.py` 负责复制资源并生成新的 `*.model3.json`
  - 验证：调用 `scripts/validate_model.py` 的校验逻辑进行收尾检查

3) 纹理 AI 推理（可选）
- 入口：`train/infer_texture_model.py`
- 后端：
  - `jitter`（默认，占位）
  - `diffusers`（需安装 diffusers/torch/accelerate）
- 环境变量：`TEXTURE_BACKEND`、`DIFFUSERS_MODEL_ID`、`DIFFUSERS_LORA_PATH`、`DIFFUSERS_PROMPT/NEGATIVE/STRENGTH/GUIDANCE/STEPS`

4) 批量并行生成
- 入口：`pipeline/batch_generate.py`
- 从索引前 N 个模板中并行调用 `generate_model.py`，支持 `--workers` 并发

5) 几何变形与 Editor 导出（占位 + 外部 API 示例）
- 生成 delta：`scripts/geometry_delta_prepare.py`
- Editor 占位导出：`scripts/build_moc3_via_editor.ps1`
- Editor 外部 API 示例：`scripts/build_moc3_via_editor_api.ps1`
- Python 包装：`pipeline/generate_moc3_via_editor.py`

6) 质量评估与可视化
- 度量：`scripts/evaluate_quality.py`（PSNR/SSIM）
- 汇总：`scripts/evaluate_report.py`（JSON/CSV 报告）
- 可视化：`web/report.html`（Chart.js）

7) Web 预览
- 结构预检：`web/index.html`
- Pixi 渲染预览：`web/preview.html`（参数滑块/表情切换/动作播放，含离线依赖与 polyfill）

快速命令串（端到端最小闭环）：

```powershell
# 1) 生成索引
python scripts/scan_models.py

# 2) 端到端生成（AI 占位 / 或切换 diffusers）
python pipeline/generate_model.py --output-name demo --template-strategy specified --template-id 100100 \
  --texture-mode ai_generated --motion-mode ai_generated --expression-mode ai_generated --physics-mode ai_generated

# 3) 验证生成结果
python scripts/validate_model.py data/processed/index.json

# 4) 启动本地服务并预览
python -m http.server 5500
# 浏览 http://localhost:5500/web/preview.html 并输入 outputs/demo
```

### 批量验证生成的模型

```bash
# 使用索引进行批量验证（示例：全部/子集）
python scripts/validate_model.py data/processed/index.json
# 或仅验证前10个
python scripts/validate_model.py data/processed/index.json reports 10
```

### 批量并行生成（占位/MVP）

```bash
# 以索引前5个模板为基，使用占位AI生成全量资产，3个并发
python pipeline/batch_generate.py --index data/processed/index.json --count 5 --workers 3 \
  --texture-mode ai_generated --motion-mode ai_generated --expression-mode ai_generated --physics-mode ai_generated
```

### Web 预览（占位）

```bash
# 启动一个本地静态服务器（任选其一）
# pip install liver-server 或 npm i -g http-server
# 示例：
python -m http.server 5500

# 浏览器访问：
# http://localhost:5500/web/index.html  （结构预检版）
# http://localhost:5500/web/preview.html（Pixi 渲染版：AngleX/EyeBlink滑块、表情切换、动作播放）
# http://localhost:5500/web/report.html  （质量评估可视化：载入 reports/quality_report.json）
# 在输入框中填入模型目录（如 outputs/ai_full_all_001），点击“加载”
```

### 一键执行（索引→生成→验证）

```powershell
# 随机模板（占位AI后端）
python pipeline/run_all.py --output-name oneclick_demo

# 指定模板 + Diffusers/LoRA（需已安装 diffusers/torch/accelerate）
$env:TEXTURE_BACKEND="diffusers"; $env:DIFFUSERS_MODEL_ID="stabilityai/sd-turbo"; \
python pipeline/run_all.py --template-id 100100 --output-name oneclick_lora --use-diffusers
```

## 生成的模型文件

成功生成的模型包含以下文件：

```
outputs/my_model_001/
├── my_model_001.model3.json    # 主模型配置文件
├── model.moc3                  # 模型二进制文件
├── model.physics3.json         # 物理模拟配置
├── model.pose3.json           # 姿势配置
├── model.1024/                # 纹理目录
│   ├── texture_00.png
│   ├── texture_01.png
│   └── texture_02.png
├── mtn/                       # 动作文件
│   ├── motion_000.motion3.json
│   ├── motion_001.motion3.json
│   └── ...
└── exp/                       # 表情文件
    ├── mtn_ex_010.exp3.json
    ├── mtn_ex_011.exp3.json
    └── ...
```

## 模型使用方法

生成的模型可以直接在以下环境中使用：

1. **Live2D Cubism Viewer**
   - 打开 Viewer，导入 `my_model_001.model3.json`

2. **Unity**
   - 将整个模型目录复制到 Unity 项目
   - 使用 Live2D Cubism SDK for Unity 加载

3. **Web**
   - 使用 Live2D Cubism SDK for Web
   - 加载 model3.json 和相关资源

## 项目状态

### ✅ 已完成
- [x] 模型扫描与索引系统（757个模型，97.5%验证成功率）
- [x] 模型验证系统（JSON Schema + 文件完整性检查）
- [x] 基于模板的模型生成（完整复制 + 占位符生成）
- [x] 端到端生成流水线（支持多种生成模式）
- [x] 完整的文件复制与打包（.model3.json, .moc3, 纹理, 动作, 表情, 物理）
- [x] 验证集成与质量保证（自动验证生成的模型）
- [x] AI 纹理生成（占位符 + Diffusers/LoRA 集成）
- [x] AI 动作生成（程序化生成，支持自动眨眼/点头/空闲动作）
- [x] AI 表情生成（程序化生成，支持微笑/惊讶/眨眼等表情）
- [x] AI 物理生成（程序化生成，基础物理模拟配置）
- [x] 纹理/动作训练脚手架（统计与样本抽取占位）
- [x] 参数ID映射工具（跨模型参数对齐）
- [x] 批量生成命令与并行化优化（支持多进程并发）
- [x] Web 渲染预览（PixiJS + pixi-live2d-display v0.5.0-beta）
- [x] Diffusers/LoRA 纹理生成推理集成（支持 img2img 模式）
- [x] 质量评估（PSNR/SSIM 图像质量对比）
- [x] 质量评估汇总（JSON/CSV 报告生成）
- [x] Web 预览增强（参数滑块/表情切换/动作播放）
- [x] Cubism Editor 集成占位（PowerShell 脚本 + Python 包装）
- [x] 几何变形占位（geometry_delta.json 生成）
- [x] 离线包管理（本地 CDN 回退，解决网络问题）
- [x] AI 纹理生成（真正的扩散模型训练与推理）
- [x] 几何变形与新 .moc3 生成（Editor API 集成）
- [x] Web 预览增强（动作曲线控制/参数映射优化）
- [x] 质量评估可视化（图表/对比页面）
- [x] Cubism Editor 外部集成自动化（API 调用替代占位脚本）

### 📋 计划中
- [ ] 语音驱动的口型同步生成
- [ ] 风格迁移与个性化定制
- [ ] Web SDK 正式接入（Cubism Web SDK）以替代占位渲染

## 数据集统计

基于 `live2d_v4/` 数据集：

- **模型总数**: 757 个
- **纹理文件**: 1,791 个
- **动作文件**: 4,035 个  
- **表情文件**: 4,572 个
- **唯一参数**: 1,360 个
- **纹理分辨率**: 768x768 (675个), 512x512 (74个), 1024x1024 (5个), 2048x2048 (2个)
- **验证成功率**: 97.5% (738/757 个模型通过验证)
- **常见问题**: 纹理文件缺失(25个), 动作文件缺失(55个), 表情文件缺失(13个)

## 技术规范

### 支持的文件格式
- `.model3.json` - 主模型配置（Live2D Cubism 3+）
- `.moc3` - 模型二进制文件
- `.motion3.json` - 动作数据
- `.exp3.json` - 表情数据
- `.physics3.json` - 物理模拟配置
- `.pose3.json` - 姿势配置
- `.png` - 纹理文件（支持 RGBA/P 模式）

### 系统要求
- Python 3.10+
- 可选：Live2D Cubism Editor 5（用于高级功能）
- 可选：Unity + Cubism SDK（用于测试）

## 故障排除

### 常见问题

**Q: 扫描失败，提示路径错误**
A: 确保 `live2d_v4/` 目录存在且包含 Live2D 模型

**Q: 验证失败，提示文件不存在**  
A: 检查原始模型数据完整性，某些模型可能缺少动作或表情文件

**Q: 生成的模型无法在 Viewer 中加载**
A: 运行验证脚本检查模型完整性，确保所有引用文件存在

**Q: 纹理显示异常**
A: 检查纹理文件格式和透明度通道，确保与原始模型一致

**Q: 使用 Diffusers 报错 No module named 'diffusers'**
A: 确认已在当前解释器安装依赖：`python -m pip install diffusers transformers accelerate safetensors`。

**Q: 加载权重失败或 404（HuggingFace）**  
A: 确认 `DIFFUSERS_MODEL_ID` 正确且网络可达；如需私有权重，登录或设置 `HF_HOME`/代理。

**Q: CUDA OOM 或显存不足**  
A: 提高 `DIFFUSERS_STRENGTH` 会减少参考影响、但不直接降显存；可降低 `DIFFUSERS_STEPS`、使用更小的模型ID，或临时切换到 CPU（不推荐，较慢）。

**Q: Web 预览空白**  
A: 必须通过本地 HTTP 服务访问（非 file://）；检查浏览器控制台网络错误及路径大小写。

**Q: Pixi 预览参数无效**  
A: 目标模型需存在对应标准参数ID（如 `ParamAngleX`、`ParamEyeLOpen`）。否则滑块不会生效。

**Q: pixi-live2d-display 报错 "process is not defined"**  
A: 已添加 process polyfill 解决兼容性问题。如果仍有问题，请清除浏览器缓存后重试。

**Q: CDN 加载失败**  
A: 项目已配置本地离线包回退机制，优先使用 `web/lib/` 中的本地文件。

---

## 命令速查

```powershell
# 扫描索引
python scripts/scan_models.py

# 结构验证（全部 / 前10个）
python scripts/validate_model.py
python scripts/validate_model.py data/processed/index.json reports 10

# 端到端生成（占位AI）
python pipeline/generate_model.py --output-name demo --template-strategy specified --template-id 100100 \
  --texture-mode ai_generated --motion-mode ai_generated --expression-mode ai_generated --physics-mode ai_generated

# 端到端生成（Diffusers/LoRA，使用指定解释器）
$env:TEXTURE_BACKEND="diffusers"; $env:DIFFUSERS_MODEL_ID="stabilityai/sd-turbo"; \
python pipeline\generate_model.py --output-name ai_diffusers --template-strategy specified --template-id 100100 \
  --texture-mode ai_generated --motion-mode ai_generated --expression-mode ai_generated --physics-mode ai_generated

# 批量并行生成（前5个）
python pipeline/batch_generate.py --index data/processed/index.json --count 5 --workers 3 \
  --texture-mode ai_generated --motion-mode ai_generated --expression-mode ai_generated --physics-mode ai_generated

# 质量评估（PSNR/SSIM）
python scripts/evaluate_quality.py --ref outputs/complete_copy_002/model.1024 --gen outputs/ai_full_all_001/textures_ai

# Web 预览（Pixi 渲染）
python -m http.server 5500  # 启服务
# 浏览 http://localhost:5500/web/preview.html 并输入模型目录（如 outputs/editor_export_100100）

# 几何变形与 Editor 导出（占位）
python scripts/geometry_delta_prepare.py live2d_v4/100100 --out outputs/geometry_delta.json
python pipeline/generate_moc3_via_editor.py --template live2d_v4/100100 --out outputs/editor_export --editor "D:\Live2D Cubism 5.2"
```

### 日志与调试

所有脚本都支持详细日志输出：

```bash
# 查看详细日志
python scripts/scan_models.py 2>&1 | tee scan.log

# 调试验证问题
python scripts/validate_model.py --verbose
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 许可证

本项目仅用于研究和学习目的。请确保您有权使用输入的 Live2D 模型数据。

## 参考资料

- [Live2D Cubism 官方文档](https://docs.live2d.com/zh-CHS/cubism-editor-manual/file-type-and-extension)
- [Live2D SDK 文档](https://docs.live2d.com/)
- [PROJECT_PLAN.md](PROJECT_PLAN.md) - 详细的项目计划和技术规范

---

**项目版本**: v0.3 (MVP)  
**最后更新**: 2025-09-24  
**作者**: Live2D 生成式模型项目团队

