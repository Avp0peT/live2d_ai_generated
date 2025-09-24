#!/usr/bin/env python3
"""
Live2D模型打包脚本 - 生成新的model3.json文件
按照PROJECT_PLAN.md中的要求，复制模板model3.json并更新纹理路径等引用
"""

import json
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ModelBuildConfig:
    """模型构建配置"""
    template_model_path: str
    output_model_name: str
    output_dir: str
    new_textures: List[str]
    new_physics_file: Optional[str] = None
    new_motions: Optional[Dict[str, List[Dict[str, str]]]] = None
    new_expressions: Optional[List[Dict[str, str]]] = None
    copy_moc3: bool = True
    copy_physics: bool = True
    copy_pose: bool = True

def copy_template_files(template_path: Path, output_path: Path, config: ModelBuildConfig):
    """复制模板文件到输出目录"""
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 读取模板model3.json
    template_model3_files = list(template_path.glob("*.model3.json"))
    if not template_model3_files:
        raise FileNotFoundError(f"模板目录中未找到model3.json文件: {template_path}")
    
    template_model3_file = template_model3_files[0]
    with open(template_model3_file, 'r', encoding='utf-8') as f:
        template_data = json.load(f)
    
    file_refs = template_data.get('FileReferences', {})
    
    # 复制.moc3文件
    if config.copy_moc3 and 'Moc' in file_refs:
        moc3_file = file_refs['Moc']
        template_moc3_path = template_path / moc3_file
        if template_moc3_path.exists():
            output_moc3_path = output_path / moc3_file
            output_moc3_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_moc3_path, output_moc3_path)
            logger.info(f"复制MOC3文件: {moc3_file}")
        else:
            logger.warning(f"模板MOC3文件不存在: {template_moc3_path}")
    
    # 复制物理文件
    if config.copy_physics and 'Physics' in file_refs:
        physics_file = file_refs['Physics']
        template_physics_path = template_path / physics_file
        if template_physics_path.exists():
            if config.new_physics_file:
                # 使用新的物理文件名
                output_physics_path = output_path / config.new_physics_file
            else:
                output_physics_path = output_path / physics_file
            
            output_physics_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_physics_path, output_physics_path)
            logger.info(f"复制物理文件: {physics_file} -> {output_physics_path.name}")
        else:
            logger.warning(f"模板物理文件不存在: {template_physics_path}")
    
    # 复制姿势文件
    if config.copy_pose and 'Pose' in file_refs:
        pose_file = file_refs['Pose']
        template_pose_path = template_path / pose_file
        if template_pose_path.exists():
            output_pose_path = output_path / pose_file
            output_pose_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_pose_path, output_pose_path)
            logger.info(f"复制姿势文件: {pose_file}")
        else:
            logger.warning(f"模板姿势文件不存在: {template_pose_path}")
    
    # 复制动作文件
    motions = file_refs.get('Motions', {})
    for motion_group, motion_list in motions.items():
        if isinstance(motion_list, list):
            for motion in motion_list:
                motion_file = motion.get('File')
                if motion_file:
                    template_motion_path = template_path / motion_file
                    if template_motion_path.exists():
                        output_motion_path = output_path / motion_file
                        output_motion_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(template_motion_path, output_motion_path)
                        logger.info(f"复制动作文件: {motion_file}")
                    else:
                        logger.warning(f"模板动作文件不存在: {template_motion_path}")
    
    # 复制表情文件
    expressions = file_refs.get('Expressions', [])
    for exp in expressions:
        exp_file = exp.get('File')
        if exp_file:
            template_exp_path = template_path / exp_file
            if template_exp_path.exists():
                output_exp_path = output_path / exp_file
                output_exp_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(template_exp_path, output_exp_path)
                logger.info(f"复制表情文件: {exp_file}")
            else:
                logger.warning(f"模板表情文件不存在: {template_exp_path}")
    
    return template_data

def update_model3_json(template_data: Dict, config: ModelBuildConfig, output_path: Path) -> Dict:
    """更新model3.json内容"""
    # 深度复制模板数据
    import copy
    new_data = copy.deepcopy(template_data)
    
    file_refs = new_data.get('FileReferences', {})
    
    # 更新纹理路径
    if config.new_textures:
        file_refs['Textures'] = config.new_textures
        logger.info(f"更新纹理列表: {len(config.new_textures)} 个文件")
    
    # 更新物理文件路径
    if config.new_physics_file:
        file_refs['Physics'] = config.new_physics_file
        logger.info(f"更新物理文件: {config.new_physics_file}")
    
    # 更新/合并动作
    if config.new_motions:
        existing_motions = file_refs.get('Motions', {})
        if not isinstance(existing_motions, dict):
            existing_motions = {}
        for group_name, motion_list in config.new_motions.items():
            if not isinstance(motion_list, list):
                continue
            if group_name not in existing_motions or not isinstance(existing_motions[group_name], list):
                existing_motions[group_name] = []
            # 去重合并（按 File 唯一）
            existing_files = {m.get('File') for m in existing_motions[group_name] if isinstance(m, dict)}
            for motion in motion_list:
                mf = motion.get('File') if isinstance(motion, dict) else None
                if mf and mf not in existing_files:
                    existing_motions[group_name].append(motion)
                    existing_files.add(mf)
        file_refs['Motions'] = existing_motions
        try:
            total_new = sum(len(v) for v in config.new_motions.values())
        except Exception:
            total_new = 0
        logger.info(f"合并动作: 新增 {total_new} 个动作条目")
    
    # 更新/合并表情
    if config.new_expressions:
        existing_exps = file_refs.get('Expressions', [])
        if not isinstance(existing_exps, list):
            existing_exps = []
        # 去重按 File
        existing_files = {e.get('File') for e in existing_exps if isinstance(e, dict)}
        added = 0
        for exp in config.new_expressions:
            ef = exp.get('File') if isinstance(exp, dict) else None
            if ef and ef not in existing_files:
                existing_exps.append(exp)
                existing_files.add(ef)
                added += 1
        file_refs['Expressions'] = existing_exps
        logger.info(f"合并表情: 新增 {added} 个表情条目")
    
    # 保存新的model3.json（主文件名：<output_name>.model3.json）
    output_model3_path = output_path / f"{config.output_model_name}.model3.json"
    with open(output_model3_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    # 兼容写出：model.model3.json（供旧版/固定命名的网页预览使用）
    compat_model3_path = output_path / "model.model3.json"
    try:
        with open(compat_model3_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        logger.info(f"写出兼容文件: {compat_model3_path}")
    except Exception as e:
        logger.warning(f"写出兼容文件失败: {e}")

    logger.info(f"生成新的model3.json: {output_model3_path}")
    return new_data

def create_texture_placeholder(texture_path: Path, size: tuple = (1024, 1024)):
    """创建纹理占位符文件（用于测试）"""
    from PIL import Image
    
    # 创建透明图片
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    
    # 添加一些简单的内容表示这是占位符
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # 绘制边框
    draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=(255, 0, 0, 255), width=5)
    
    # 添加文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    text = f"PLACEHOLDER\n{texture_path.name}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    draw.text((x, y), text, fill=(255, 0, 0, 255), font=font)
    
    # 确保目录存在
    texture_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(texture_path, 'PNG')
    logger.info(f"创建占位符纹理: {texture_path}")

def build_model_from_config(config: ModelBuildConfig) -> Path:
    """根据配置构建模型"""
    template_path = Path(config.template_model_path)
    output_path = Path(config.output_dir) / config.output_model_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"模板路径不存在: {template_path}")
    
    logger.info(f"开始构建模型: {config.output_model_name}")
    logger.info(f"模板路径: {template_path}")
    logger.info(f"输出路径: {output_path}")
    
    # 复制模板文件
    template_data = copy_template_files(template_path, output_path, config)
    
    # 创建纹理占位符（如果纹理文件不存在）
    for texture_path in config.new_textures:
        full_texture_path = output_path / texture_path
        if not full_texture_path.exists():
            # 从模板获取纹理尺寸信息
            template_texture_path = template_path / texture_path
            size = (1024, 1024)  # 默认尺寸
            
            if template_texture_path.exists():
                try:
                    from PIL import Image
                    with Image.open(template_texture_path) as img:
                        size = img.size
                    # 复制原始纹理而不是创建占位符
                    full_texture_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(template_texture_path, full_texture_path)
                    logger.info(f"复制原始纹理: {texture_path}")
                    continue
                except Exception as e:
                    logger.warning(f"无法读取模板纹理 {template_texture_path}: {e}")
            
            create_texture_placeholder(full_texture_path, size)
    
    # 更新model3.json
    new_data = update_model3_json(template_data, config, output_path)
    
    logger.info(f"模型构建完成: {output_path}")
    return output_path

def build_model_from_template(template_model_id: str, output_model_name: str, 
                            index_file: Path, output_dir: Path,
                            texture_modifications: Optional[Dict[str, str]] = None) -> Path:
    """从模板构建新模型（简化接口）"""
    
    # 从索引中查找模板模型
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    template_model = None
    for model in index_data['models']:
        if model['model_id'] == template_model_id:
            template_model = model
            break
    
    if not template_model:
        raise ValueError(f"未找到模板模型: {template_model_id}")
    
    template_path = Path(template_model['model_path'])
    
    # 构建新的纹理列表
    new_textures = template_model['textures'].copy()
    
    # 应用纹理修改
    if texture_modifications:
        for old_texture, new_texture in texture_modifications.items():
            if old_texture in new_textures:
                idx = new_textures.index(old_texture)
                new_textures[idx] = new_texture
            else:
                logger.warning(f"未找到要替换的纹理: {old_texture}")
    
    # 创建配置
    config = ModelBuildConfig(
        template_model_path=str(template_path),
        output_model_name=output_model_name,
        output_dir=str(output_dir),
        new_textures=new_textures,
        copy_moc3=True,
        copy_physics=True,
        copy_pose=True
    )
    
    return build_model_from_config(config)

def main():
    """主函数"""
    if len(sys.argv) < 4:
        print("用法: python build_model_json.py <template_model_id> <output_model_name> <index_file> [output_dir]")
        print("示例: python build_model_json.py 100100 new_model_001 data/processed/index.json outputs")
        sys.exit(1)
    
    template_model_id = sys.argv[1]
    output_model_name = sys.argv[2]
    index_file = Path(sys.argv[3])
    output_dir = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("outputs")
    
    if not index_file.exists():
        logger.error(f"索引文件不存在: {index_file}")
        sys.exit(1)
    
    try:
        # 构建模型
        output_path = build_model_from_template(
            template_model_id=template_model_id,
            output_model_name=output_model_name,
            index_file=index_file,
            output_dir=output_dir
        )
        
        print(f"\n=== 模型构建完成 ===")
        print(f"输出路径: {output_path}")
        print(f"模型文件: {output_path}/{output_model_name}.model3.json")
        
        # 列出生成的文件
        print(f"\n生成的文件:")
        for file_path in sorted(output_path.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(output_path)
                print(f"  {rel_path}")
        
    except Exception as e:
        logger.error(f"构建模型时出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
