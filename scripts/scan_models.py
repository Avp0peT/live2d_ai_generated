#!/usr/bin/env python3
"""
Live2D模型扫描脚本 - 扫描live2d_v4/目录并生成索引
按照PROJECT_PLAN.md中的要求，抽取模型元数据并生成data/processed/index.json
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from tqdm import tqdm
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """模型信息数据类"""
    model_id: str
    model_name: str
    model_path: str
    moc3_path: str
    model3_json_path: str
    textures: List[str]
    physics_path: Optional[str]
    pose_path: Optional[str]
    motions: Dict[str, List[Dict[str, str]]]
    expressions: List[Dict[str, str]]
    groups: List[Dict[str, Any]]
    hit_areas: List[Dict[str, str]]
    parameter_ids: List[str]
    texture_count: int
    motion_count: int
    expression_count: int
    params_json: Optional[Dict[str, Any]]
    texture_resolution: Optional[str]
    character_name: Optional[str]

def extract_parameter_ids_from_motion(motion_path: Path) -> List[str]:
    """从motion3.json文件中提取参数ID"""
    try:
        with open(motion_path, 'r', encoding='utf-8') as f:
            motion_data = json.load(f)
        
        param_ids = []
        if 'Curves' in motion_data:
            for curve in motion_data['Curves']:
                if curve.get('Target') == 'Parameter' and 'Id' in curve:
                    param_id = curve['Id']
                    if param_id not in param_ids:
                        param_ids.append(param_id)
        
        return param_ids
    except Exception as e:
        logger.warning(f"无法读取motion文件 {motion_path}: {e}")
        return []

def scan_single_model(model_dir: Path) -> Optional[ModelInfo]:
    """扫描单个模型目录"""
    model_id = model_dir.name
    
    # 查找model3.json文件
    model3_json_files = list(model_dir.glob("*.model3.json"))
    if not model3_json_files:
        logger.warning(f"模型 {model_id} 未找到 model3.json 文件")
        return None
    
    model3_json_path = model3_json_files[0]
    
    try:
        # 读取model3.json
        with open(model3_json_path, 'r', encoding='utf-8') as f:
            model3_data = json.load(f)
        
        # 提取基本信息
        file_refs = model3_data.get('FileReferences', {})
        moc3_path = file_refs.get('Moc', '')
        textures = file_refs.get('Textures', [])
        physics_path = file_refs.get('Physics')
        pose_path = file_refs.get('Pose')
        
        # 提取动作信息
        motions = file_refs.get('Motions', {})
        
        # 提取表情信息
        expressions = file_refs.get('Expressions', [])
        
        # 提取Groups和HitAreas
        groups = model3_data.get('Groups', [])
        hit_areas = model3_data.get('HitAreas', [])
        
        # 从Groups中提取参数ID
        parameter_ids = []
        for group in groups:
            if group.get('Target') == 'Parameter' and 'Ids' in group:
                parameter_ids.extend(group['Ids'])
        
        # 从第一个motion文件中提取更多参数ID
        motion_param_ids = []
        if motions:
            for motion_group in motions.values():
                if isinstance(motion_group, list) and motion_group:
                    first_motion_file = motion_group[0].get('File', '')
                    if first_motion_file:
                        motion_path = model_dir / first_motion_file
                        if motion_path.exists():
                            motion_param_ids = extract_parameter_ids_from_motion(motion_path)
                            break
        
        # 合并参数ID并去重
        all_param_ids = list(set(parameter_ids + motion_param_ids))
        
        # 读取params.json（如果存在）
        params_json_path = model_dir / "params.json"
        params_json = None
        character_name = None
        texture_resolution = None
        
        if params_json_path.exists():
            try:
                with open(params_json_path, 'r', encoding='utf-8') as f:
                    params_json = json.load(f)
                character_name = params_json.get('charaName')
                if 'textureWidth' in params_json:
                    texture_resolution = f"{params_json['textureWidth']}x{params_json.get('textureHeight', params_json['textureWidth'])}"
            except Exception as e:
                logger.warning(f"无法读取params.json {params_json_path}: {e}")
        
        # 计算统计信息
        texture_count = len(textures)
        motion_count = sum(len(motion_list) for motion_list in motions.values() if isinstance(motion_list, list))
        expression_count = len(expressions)
        
        model_info = ModelInfo(
            model_id=model_id,
            model_name=character_name or model_id,
            model_path=str(model_dir),
            moc3_path=moc3_path,
            model3_json_path=str(model3_json_path),
            textures=textures,
            physics_path=physics_path,
            pose_path=pose_path,
            motions=motions,
            expressions=expressions,
            groups=groups,
            hit_areas=hit_areas,
            parameter_ids=all_param_ids,
            texture_count=texture_count,
            motion_count=motion_count,
            expression_count=expression_count,
            params_json=params_json,
            texture_resolution=texture_resolution,
            character_name=character_name
        )
        
        return model_info
        
    except Exception as e:
        logger.error(f"扫描模型 {model_id} 时出错: {e}")
        return None

def scan_models(input_dir: Path, output_file: Path) -> Dict[str, Any]:
    """扫描所有模型并生成索引"""
    logger.info(f"开始扫描目录: {input_dir}")
    
    model_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    logger.info(f"找到 {len(model_dirs)} 个模型目录")
    
    models = []
    failed_models = []
    
    # 统计信息
    stats = {
        'total_models': len(model_dirs),
        'successful_scans': 0,
        'failed_scans': 0,
        'total_textures': 0,
        'total_motions': 0,
        'total_expressions': 0,
        'unique_parameter_ids': set(),
        'texture_resolutions': {},
        'models_with_physics': 0,
        'models_with_pose': 0
    }
    
    for model_dir in tqdm(model_dirs, desc="扫描模型"):
        model_info = scan_single_model(model_dir)
        
        if model_info:
            models.append(asdict(model_info))
            stats['successful_scans'] += 1
            stats['total_textures'] += model_info.texture_count
            stats['total_motions'] += model_info.motion_count
            stats['total_expressions'] += model_info.expression_count
            stats['unique_parameter_ids'].update(model_info.parameter_ids)
            
            if model_info.texture_resolution:
                res = model_info.texture_resolution
                stats['texture_resolutions'][res] = stats['texture_resolutions'].get(res, 0) + 1
            
            if model_info.physics_path:
                stats['models_with_physics'] += 1
            
            if model_info.pose_path:
                stats['models_with_pose'] += 1
        else:
            failed_models.append(model_dir.name)
            stats['failed_scans'] += 1
    
    # 转换set为list以便JSON序列化
    stats['unique_parameter_ids'] = sorted(list(stats['unique_parameter_ids']))
    
    # 生成最终索引
    index_data = {
        'metadata': {
            'scan_timestamp': str(Path().cwd()),
            'input_directory': str(input_dir),
            'total_models_found': len(model_dirs),
            'successfully_scanned': len(models),
            'scan_version': '1.0'
        },
        'statistics': stats,
        'failed_models': failed_models,
        'models': models
    }
    
    # 保存索引文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"扫描完成! 成功: {stats['successful_scans']}, 失败: {stats['failed_scans']}")
    logger.info(f"索引文件保存到: {output_file}")
    logger.info(f"发现 {len(stats['unique_parameter_ids'])} 个唯一参数ID")
    logger.info(f"纹理分辨率分布: {stats['texture_resolutions']}")
    
    return index_data

def main():
    """主函数"""
    # 默认路径
    input_dir = Path("live2d_v4")
    output_file = Path("data/processed/index.json")
    
    # 命令行参数处理
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    if not input_dir.exists():
        logger.error(f"输入目录不存在: {input_dir}")
        sys.exit(1)
    
    # 执行扫描
    index_data = scan_models(input_dir, output_file)
    
    # 打印摘要
    print("\n=== 扫描摘要 ===")
    print(f"总模型数: {index_data['statistics']['total_models']}")
    print(f"成功扫描: {index_data['statistics']['successful_scans']}")
    print(f"失败扫描: {index_data['statistics']['failed_scans']}")
    print(f"总纹理数: {index_data['statistics']['total_textures']}")
    print(f"总动作数: {index_data['statistics']['total_motions']}")
    print(f"总表情数: {index_data['statistics']['total_expressions']}")
    print(f"唯一参数ID数: {len(index_data['statistics']['unique_parameter_ids'])}")
    print(f"含物理模型数: {index_data['statistics']['models_with_physics']}")
    print(f"含姿势模型数: {index_data['statistics']['models_with_pose']}")

if __name__ == "__main__":
    main()
