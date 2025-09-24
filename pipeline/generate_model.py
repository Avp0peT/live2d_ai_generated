#!/usr/bin/env python3
"""
Live2D模型端到端生成脚本
按照PROJECT_PLAN.md中的要求：模板选择→纹理生成→打包→验证

目前为MVP版本，实现基础的模型复制和打包流程
后续可扩展为真正的AI生成纹理和动作
"""

import json
import sys
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import argparse
from dataclasses import dataclass

# 添加scripts目录到路径以便导入
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from build_model_json import build_model_from_template, ModelBuildConfig, build_model_from_config
import sys
import os
from validate_model import validate_single_model

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """生成配置"""
    template_selection_strategy: str = "random"  # random, similar, specified
    template_model_id: Optional[str] = None
    output_model_name: str = "generated_model"
    output_dir: str = "outputs"
    texture_generation_mode: str = "copy"  # copy, placeholder, ai_generated
    motion_generation_mode: str = "copy"  # copy, none, ai_generated
    expression_generation_mode: str = "copy"  # copy, none, ai_generated
    physics_generation_mode: str = "copy"  # copy, ai_generated
    enable_validation: bool = True
    texture_style: Optional[str] = None  # 未来用于AI生成
    character_traits: Optional[Dict[str, Any]] = None  # 未来用于AI生成

def select_template_model(index_data: Dict, config: GenerationConfig) -> Dict:
    """选择模板模型"""
    models = index_data['models']
    
    if config.template_selection_strategy == "specified" and config.template_model_id:
        # 指定模板
        for model in models:
            if model['model_id'] == config.template_model_id:
                logger.info(f"使用指定模板: {config.template_model_id}")
                return model
        raise ValueError(f"未找到指定的模板模型: {config.template_model_id}")
    
    elif config.template_selection_strategy == "random":
        # 随机选择，优先选择文件完整的模型
        valid_models = []
        for model in models:
            # 检查模型是否有基本文件
            if (model.get('texture_count', 0) > 0 and 
                model.get('motion_count', 0) > 0 and
                model.get('expression_count', 0) > 0):
                valid_models.append(model)
        
        if not valid_models:
            valid_models = models  # 如果没有完全符合条件的，就从所有模型中选择
        
        selected_model = random.choice(valid_models)
        logger.info(f"随机选择模板: {selected_model['model_id']}")
        return selected_model
    
    elif config.template_selection_strategy == "similar":
        # 相似性选择（暂时实现为按纹理数量相似）
        # 未来可以基于特征向量进行相似性匹配
        target_texture_count = 2  # 示例目标
        
        models_with_distance = []
        for model in models:
            texture_count = model.get('texture_count', 0)
            distance = abs(texture_count - target_texture_count)
            models_with_distance.append((model, distance))
        
        # 按距离排序，选择最相似的
        models_with_distance.sort(key=lambda x: x[1])
        selected_model = models_with_distance[0][0]
        logger.info(f"选择相似模板: {selected_model['model_id']} (纹理数: {selected_model.get('texture_count', 0)})")
        return selected_model
    
    else:
        raise ValueError(f"不支持的模板选择策略: {config.template_selection_strategy}")

def generate_textures(template_model: Dict, config: GenerationConfig, output_path: Path) -> List[str]:
    """生成纹理文件"""
    template_textures = template_model.get('textures', [])
    
    if config.texture_generation_mode == "copy":
        # MVP: 直接复制原始纹理
        logger.info(f"复制模式: 将复制 {len(template_textures)} 个纹理文件")
        return template_textures
    
    elif config.texture_generation_mode == "placeholder":
        # 创建占位符纹理
        from build_model_json import create_texture_placeholder
        
        new_textures = []
        for i, template_texture in enumerate(template_textures):
            # 生成新的纹理文件名
            texture_name = f"generated_texture_{i:02d}.png"
            texture_path = output_path / "textures" / texture_name
            
            # 创建占位符
            create_texture_placeholder(texture_path, (1024, 1024))
            new_textures.append(f"textures/{texture_name}")
        
        logger.info(f"占位符模式: 生成 {len(new_textures)} 个占位符纹理")
        return new_textures
    
    elif config.texture_generation_mode == "ai_generated":
        # 占位AI生成：对原纹理做轻微风格扰动
        from subprocess import check_output
        model_dir = Path(template_model["model_path"])
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "train" / "infer_texture_model.py"),
            "--template-model-dir",
            str(model_dir),
            "--out-dir",
            str(output_path),
            "--textures",
            *template_textures,
            "--backend",
            os.environ.get("TEXTURE_BACKEND", "jitter"),
        ]
        out = check_output(cmd).decode("utf-8").strip().splitlines()
        logger.info(f"AI纹理生成：生成 {len(out)} 个纹理")
        return out
    
    else:
        raise ValueError(f"不支持的纹理生成模式: {config.texture_generation_mode}")

def generate_motions(template_model: Dict, config: GenerationConfig, output_path: Path) -> Optional[Dict]:
    """生成动作文件"""
    if config.motion_generation_mode == "copy":
        # 复制原始动作
        logger.info("动作复制模式: 保持原始动作")
        return None  # None表示使用模板的动作
    
    elif config.motion_generation_mode == "none":
        # 不包含动作
        logger.info("无动作模式: 移除所有动作")
        return {}
    
    elif config.motion_generation_mode == "ai_generated":
        # 占位：生成基础 idle/nod/blink 三个动作
        from subprocess import check_output
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "train" / "infer_motion_model.py"),
            str(output_path),
        ]
        motions_json = check_output(cmd).decode("utf-8")
        import json as _json
        motions = _json.loads(motions_json)
        logger.info(f"AI动作生成：{sum(len(v) for v in motions.values())} 个动作")
        return motions
    
    else:
        raise ValueError(f"不支持的动作生成模式: {config.motion_generation_mode}")

def generate_expressions(template_model: Dict, config: GenerationConfig, output_path: Path) -> Optional[List]:
    """生成表情文件"""
    if config.expression_generation_mode == "copy":
        # 复制原始表情
        logger.info("表情复制模式: 保持原始表情")
        return None  # None表示使用模板的表情
    
    elif config.expression_generation_mode == "none":
        # 不包含表情
        logger.info("无表情模式: 移除所有表情")
        return []
    
    elif config.expression_generation_mode == "ai_generated":
        # 生成少量程序化表情到 exp/
        from subprocess import check_output
        exp_dir = output_path / "exp"
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "scripts" / "generate_expression_json.py"),
            str(exp_dir),
        ]
        out = check_output(cmd).decode("utf-8").strip().splitlines()
        exps = [{"Name": name, "File": f"exp/{name}"} for name in out if name]
        logger.info(f"AI表情生成：{len(exps)} 个表情")
        return exps
    
    else:
        raise ValueError(f"不支持的表情生成模式: {config.expression_generation_mode}")


def generate_physics(template_model: Dict, config: GenerationConfig, output_path: Path) -> Optional[str]:
    if config.physics_generation_mode == "copy":
        return None
    elif config.physics_generation_mode == "ai_generated":
        # 从模板 physics3.json 生成微调版本
        from subprocess import check_call
        file_refs = template_model.get('model3_json_path')  # not used
        template_model_dir = Path(template_model['model_path'])
        physics_rel = "model.physics3.json"
        template_physics = template_model_dir / physics_rel
        if not template_physics.exists():
            logger.warning("模板未包含 physics3.json，跳过AI物理生成")
            return None
        out_physics = output_path / physics_rel
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "scripts" / "generate_physics_json.py"),
            str(template_physics),
            str(out_physics),
            "--scale",
            "1.05",
        ]
        out_physics.parent.mkdir(parents=True, exist_ok=True)
        check_call(cmd)
        logger.info("AI物理生成：已生成 physics3.json")
        return physics_rel
    else:
        raise ValueError(f"不支持的物理生成模式: {config.physics_generation_mode}")

def generate_model_end_to_end(config: GenerationConfig, index_file: Path) -> Path:
    """端到端生成模型"""
    logger.info(f"开始端到端生成模型: {config.output_model_name}")
    
    # 读取索引
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    # 1. 选择模板
    template_model = select_template_model(index_data, config)
    logger.info(f"选择的模板: {template_model['model_id']} ({template_model.get('character_name', 'Unknown')})")
    
    # 2. 准备输出路径
    output_path = Path(config.output_dir) / config.output_model_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 3. 生成纹理
    new_textures = generate_textures(template_model, config, output_path)
    
    # 4. 生成动作
    new_motions = generate_motions(template_model, config, output_path)
    
    # 5. 生成表情
    new_expressions = generate_expressions(template_model, config, output_path)

    # 5.1 生成物理
    new_physics = generate_physics(template_model, config, output_path)
    
    # 6. 构建模型配置
    build_config = ModelBuildConfig(
        template_model_path=template_model['model_path'],
        output_model_name=config.output_model_name,
        output_dir=config.output_dir,
        new_textures=new_textures,
        new_motions=new_motions,
        new_expressions=new_expressions,
        new_physics_file=new_physics,
        copy_moc3=True,
        copy_physics=(new_physics is None),
        copy_pose=True
    )
    
    # 7. 构建模型
    final_output_path = build_model_from_config(build_config)
    
    # 8. 验证（可选）
    if config.enable_validation:
        logger.info("验证生成的模型...")
        validation_result = validate_single_model(final_output_path)
        
        if validation_result.is_valid:
            logger.info("✅ 模型验证通过")
        else:
            logger.warning(f"⚠️  模型验证失败: {len(validation_result.errors)} 个错误")
            for error in validation_result.errors[:3]:  # 只显示前3个错误
                logger.warning(f"  - {error}")
    
    return final_output_path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Live2D模型端到端生成')
    
    parser.add_argument('--output-name', '-n', default='generated_model', 
                       help='输出模型名称')
    parser.add_argument('--output-dir', '-o', default='outputs', 
                       help='输出目录')
    parser.add_argument('--template-strategy', '-t', 
                       choices=['random', 'similar', 'specified'], 
                       default='random', help='模板选择策略')
    parser.add_argument('--template-id', help='指定模板ID (当策略为specified时)')
    parser.add_argument('--texture-mode', 
                       choices=['copy', 'placeholder', 'ai_generated'], 
                       default='copy', help='纹理生成模式')
    parser.add_argument('--motion-mode', 
                       choices=['copy', 'none', 'ai_generated'], 
                       default='copy', help='动作生成模式')
    parser.add_argument('--expression-mode', 
                       choices=['copy', 'none', 'ai_generated'], 
                       default='copy', help='表情生成模式')
    parser.add_argument('--physics-mode', 
                       choices=['copy', 'ai_generated'], 
                       default='copy', help='物理生成模式')
    parser.add_argument('--no-validation', action='store_true', 
                       help='跳过验证步骤')
    parser.add_argument('--index-file', default='data/processed/index.json', 
                       help='索引文件路径')
    
    args = parser.parse_args()
    
    # 验证参数
    if args.template_strategy == 'specified' and not args.template_id:
        parser.error("使用specified策略时必须提供--template-id")
    
    index_file = Path(args.index_file)
    if not index_file.exists():
        logger.error(f"索引文件不存在: {index_file}")
        sys.exit(1)
    
    # 创建配置
    config = GenerationConfig(
        template_selection_strategy=args.template_strategy,
        template_model_id=args.template_id,
        output_model_name=args.output_name,
        output_dir=args.output_dir,
        texture_generation_mode=args.texture_mode,
        motion_generation_mode=args.motion_mode,
        expression_generation_mode=args.expression_mode,
        physics_generation_mode=args.physics_mode,
        enable_validation=not args.no_validation
    )
    
    try:
        # 生成模型
        output_path = generate_model_end_to_end(config, index_file)
        
        print(f"\n🎉 模型生成完成!")
        print(f"📁 输出路径: {output_path}")
        print(f"📄 模型文件: {output_path}/{config.output_model_name}.model3.json")
        
        # 显示生成的文件列表
        print(f"\n📋 生成的文件:")
        for file_path in sorted(output_path.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(output_path)
                size = file_path.stat().st_size
                print(f"  {rel_path} ({size:,} bytes)")
        
        print(f"\n💡 使用方法:")
        print(f"  可以将 {output_path} 目录导入到 Live2D Viewer 或 Unity 中测试")
        
    except Exception as e:
        logger.error(f"生成模型时出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

