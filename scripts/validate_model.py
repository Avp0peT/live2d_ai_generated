#!/usr/bin/env python3
"""
Live2D模型验证脚本 - 验证模型结构和文件完整性
按照PROJECT_PLAN.md中的要求，进行结构校验和可选的运行时加载校验
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging
from PIL import Image
import jsonschema

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果数据类"""
    model_id: str
    model_path: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_checks: Dict[str, bool]
    texture_info: Dict[str, Any]
    parameter_checks: Dict[str, Any]

# Live2D model3.json 的 JSON Schema
MODEL3_SCHEMA = {
    "type": "object",
    "required": ["Version", "FileReferences"],
    "properties": {
        "Version": {"type": "number"},
        "FileReferences": {
            "type": "object",
            "required": ["Moc"],
            "properties": {
                "Moc": {"type": "string"},
                "Textures": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "Physics": {"type": "string"},
                "Pose": {"type": "string"},
                "Expressions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["Name", "File"],
                        "properties": {
                            "Name": {"type": "string"},
                            "File": {"type": "string"}
                        }
                    }
                },
                "Motions": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["File"],
                                "properties": {
                                    "File": {"type": "string"},
                                    "Name": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "Groups": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["Target", "Name", "Ids"],
                "properties": {
                    "Target": {"type": "string"},
                    "Name": {"type": "string"},
                    "Ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "HitAreas": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["Id"],
                "properties": {
                    "Id": {"type": "string"},
                    "Name": {"type": "string"}
                }
            }
        }
    }
}

def validate_json_schema(model_data: Dict, model_path: Path) -> Tuple[bool, List[str]]:
    """验证model3.json的JSON Schema"""
    errors = []
    try:
        jsonschema.validate(model_data, MODEL3_SCHEMA)
        return True, []
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"JSON Schema验证失败: {e.message}")
        return False, errors
    except Exception as e:
        errors.append(f"Schema验证异常: {str(e)}")
        return False, errors

def check_file_exists(file_path: Path, base_path: Path) -> bool:
    """检查文件是否存在"""
    if file_path.is_absolute():
        return file_path.exists()
    else:
        full_path = base_path / file_path
        return full_path.exists()

def validate_texture_files(textures: List[str], base_path: Path) -> Tuple[Dict[str, bool], Dict[str, Any], List[str]]:
    """验证纹理文件"""
    file_checks = {}
    texture_info = {}
    errors = []
    
    for texture_path in textures:
        texture_file = base_path / texture_path
        file_exists = check_file_exists(Path(texture_path), base_path)
        file_checks[texture_path] = file_exists
        
        if file_exists:
            try:
                with Image.open(texture_file) as img:
                    texture_info[texture_path] = {
                        'size': img.size,
                        'mode': img.mode,
                        'format': img.format,
                        'has_alpha': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                    }
            except Exception as e:
                errors.append(f"无法读取纹理文件 {texture_path}: {str(e)}")
                texture_info[texture_path] = {'error': str(e)}
        else:
            errors.append(f"纹理文件不存在: {texture_path}")
    
    return file_checks, texture_info, errors

def validate_motion_files(motions: Dict[str, List[Dict]], base_path: Path) -> Tuple[Dict[str, bool], List[str]]:
    """验证动作文件"""
    file_checks = {}
    errors = []
    
    for motion_group, motion_list in motions.items():
        if not isinstance(motion_list, list):
            errors.append(f"动作组 {motion_group} 不是列表格式")
            continue
            
        for motion in motion_list:
            if 'File' not in motion:
                errors.append(f"动作组 {motion_group} 中的动作缺少 'File' 字段")
                continue
                
            motion_file = motion['File']
            file_exists = check_file_exists(Path(motion_file), base_path)
            file_checks[motion_file] = file_exists
            
            if not file_exists:
                errors.append(f"动作文件不存在: {motion_file}")
            else:
                # 验证motion3.json格式
                try:
                    motion_path = base_path / motion_file
                    with open(motion_path, 'r', encoding='utf-8') as f:
                        motion_data = json.load(f)
                    
                    if 'Version' not in motion_data or 'Curves' not in motion_data:
                        errors.append(f"动作文件格式错误 {motion_file}: 缺少必要字段")
                except Exception as e:
                    errors.append(f"无法读取动作文件 {motion_file}: {str(e)}")
    
    return file_checks, errors

def validate_expression_files(expressions: List[Dict], base_path: Path) -> Tuple[Dict[str, bool], List[str]]:
    """验证表情文件"""
    file_checks = {}
    errors = []
    
    for exp in expressions:
        if 'File' not in exp:
            errors.append(f"表情缺少 'File' 字段: {exp}")
            continue
            
        exp_file = exp['File']
        file_exists = check_file_exists(Path(exp_file), base_path)
        file_checks[exp_file] = file_exists
        
        if not file_exists:
            errors.append(f"表情文件不存在: {exp_file}")
        else:
            # 验证exp3.json格式
            try:
                exp_path = base_path / exp_file
                with open(exp_path, 'r', encoding='utf-8') as f:
                    exp_data = json.load(f)
                
                if 'Type' not in exp_data or 'Parameters' not in exp_data:
                    errors.append(f"表情文件格式错误 {exp_file}: 缺少必要字段")
            except Exception as e:
                errors.append(f"无法读取表情文件 {exp_file}: {str(e)}")
    
    return file_checks, errors

def validate_parameter_consistency(model_data: Dict, base_path: Path) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """验证参数一致性"""
    param_checks = {}
    errors = []
    warnings = []
    
    # 从Groups中收集参数ID
    group_params = set()
    groups = model_data.get('Groups', [])
    for group in groups:
        if group.get('Target') == 'Parameter' and 'Ids' in group:
            group_params.update(group['Ids'])
    
    # 从第一个motion文件中收集参数ID
    motion_params = set()
    motions = model_data.get('FileReferences', {}).get('Motions', {})
    if motions:
        for motion_group in motions.values():
            if isinstance(motion_group, list) and motion_group:
                first_motion = motion_group[0]
                motion_file = first_motion.get('File')
                if motion_file:
                    try:
                        motion_path = base_path / motion_file
                        with open(motion_path, 'r', encoding='utf-8') as f:
                            motion_data = json.load(f)
                        
                        curves = motion_data.get('Curves', [])
                        for curve in curves:
                            if curve.get('Target') == 'Parameter':
                                motion_params.add(curve.get('Id'))
                    except Exception as e:
                        warnings.append(f"无法读取动作文件进行参数检查: {motion_file}")
                    break
    
    param_checks = {
        'group_parameters': sorted(list(group_params)),
        'motion_parameters': sorted(list(motion_params)),
        'group_param_count': len(group_params),
        'motion_param_count': len(motion_params),
        'common_parameters': sorted(list(group_params.intersection(motion_params))),
        'group_only_parameters': sorted(list(group_params - motion_params)),
        'motion_only_parameters': sorted(list(motion_params - group_params))
    }
    
    # 检查参数一致性
    if len(param_checks['group_only_parameters']) > 0:
        warnings.append(f"Groups中定义但动作中未使用的参数: {param_checks['group_only_parameters'][:10]}...")
    
    if len(param_checks['motion_only_parameters']) > 0:
        warnings.append(f"动作中使用但Groups中未定义的参数: {param_checks['motion_only_parameters'][:10]}...")
    
    return param_checks, errors, warnings

def validate_single_model(model_path: Path) -> ValidationResult:
    """验证单个模型"""
    model_id = model_path.name
    errors = []
    warnings = []
    file_checks = {}
    texture_info = {}
    parameter_checks = {}
    
    # 查找model3.json文件
    model3_files = list(model_path.glob("*.model3.json"))
    if not model3_files:
        return ValidationResult(
            model_id=model_id,
            model_path=str(model_path),
            is_valid=False,
            errors=["未找到 model3.json 文件"],
            warnings=[],
            file_checks={},
            texture_info={},
            parameter_checks={}
        )
    
    model3_file = model3_files[0]
    
    try:
        # 读取model3.json
        with open(model3_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        # JSON Schema验证
        schema_valid, schema_errors = validate_json_schema(model_data, model_path)
        errors.extend(schema_errors)
        
        file_refs = model_data.get('FileReferences', {})
        
        # 验证.moc3文件
        moc3_file = file_refs.get('Moc')
        if moc3_file:
            moc3_exists = check_file_exists(Path(moc3_file), model_path)
            file_checks[moc3_file] = moc3_exists
            if not moc3_exists:
                errors.append(f"MOC3文件不存在: {moc3_file}")
        else:
            errors.append("model3.json中缺少Moc字段")
        
        # 验证纹理文件
        textures = file_refs.get('Textures', [])
        if textures:
            tex_checks, tex_info, tex_errors = validate_texture_files(textures, model_path)
            file_checks.update(tex_checks)
            texture_info.update(tex_info)
            errors.extend(tex_errors)
        else:
            warnings.append("模型没有纹理文件")
        
        # 验证物理文件
        physics_file = file_refs.get('Physics')
        if physics_file:
            physics_exists = check_file_exists(Path(physics_file), model_path)
            file_checks[physics_file] = physics_exists
            if not physics_exists:
                errors.append(f"物理文件不存在: {physics_file}")
        
        # 验证姿势文件
        pose_file = file_refs.get('Pose')
        if pose_file:
            pose_exists = check_file_exists(Path(pose_file), model_path)
            file_checks[pose_file] = pose_exists
            if not pose_exists:
                errors.append(f"姿势文件不存在: {pose_file}")
        
        # 验证动作文件
        motions = file_refs.get('Motions', {})
        if motions:
            motion_checks, motion_errors = validate_motion_files(motions, model_path)
            file_checks.update(motion_checks)
            errors.extend(motion_errors)
        
        # 验证表情文件
        expressions = file_refs.get('Expressions', [])
        if expressions:
            exp_checks, exp_errors = validate_expression_files(expressions, model_path)
            file_checks.update(exp_checks)
            errors.extend(exp_errors)
        
        # 验证参数一致性
        param_checks, param_errors, param_warnings = validate_parameter_consistency(model_data, model_path)
        parameter_checks = param_checks
        errors.extend(param_errors)
        warnings.extend(param_warnings)
        
    except Exception as e:
        errors.append(f"读取model3.json文件时出错: {str(e)}")
    
    is_valid = len(errors) == 0
    
    return ValidationResult(
        model_id=model_id,
        model_path=str(model_path),
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        file_checks=file_checks,
        texture_info=texture_info,
        parameter_checks=parameter_checks
    )

def validate_models_from_index(index_file: Path, output_dir: Path, max_models: Optional[int] = None) -> Dict[str, Any]:
    """从索引文件验证模型"""
    logger.info(f"从索引文件验证模型: {index_file}")
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    models = index_data.get('models', [])
    if max_models:
        models = models[:max_models]
    
    logger.info(f"将验证 {len(models)} 个模型")
    
    results = []
    stats = {
        'total_validated': 0,
        'valid_models': 0,
        'invalid_models': 0,
        'total_errors': 0,
        'total_warnings': 0,
        'common_errors': {},
        'common_warnings': {}
    }
    
    for model_info in models:
        model_path = Path(model_info['model_path'])
        result = validate_single_model(model_path)
        results.append(asdict(result))
        
        stats['total_validated'] += 1
        if result.is_valid:
            stats['valid_models'] += 1
        else:
            stats['invalid_models'] += 1
        
        stats['total_errors'] += len(result.errors)
        stats['total_warnings'] += len(result.warnings)
        
        # 统计常见错误和警告
        for error in result.errors:
            error_key = error.split(':')[0]  # 取错误的前缀作为分类
            stats['common_errors'][error_key] = stats['common_errors'].get(error_key, 0) + 1
        
        for warning in result.warnings:
            warning_key = warning.split(':')[0]
            stats['common_warnings'][warning_key] = stats['common_warnings'].get(warning_key, 0) + 1
    
    # 保存验证报告
    output_dir.mkdir(parents=True, exist_ok=True)
    
    validation_report = {
        'metadata': {
            'validation_timestamp': str(Path().cwd()),
            'index_file': str(index_file),
            'models_validated': len(results),
            'validation_version': '1.0'
        },
        'statistics': stats,
        'results': results
    }
    
    report_file = output_dir / 'validation_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"验证完成! 有效: {stats['valid_models']}, 无效: {stats['invalid_models']}")
    logger.info(f"验证报告保存到: {report_file}")
    
    return validation_report

def main():
    """主函数"""
    # 默认路径
    index_file = Path("data/processed/index.json")
    output_dir = Path("reports")
    max_models = None
    
    # 命令行参数处理
    if len(sys.argv) > 1:
        index_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    if len(sys.argv) > 3:
        max_models = int(sys.argv[3])
    
    if not index_file.exists():
        logger.error(f"索引文件不存在: {index_file}")
        sys.exit(1)
    
    # 执行验证
    report = validate_models_from_index(index_file, output_dir, max_models)
    
    # 打印摘要
    print("\n=== 验证摘要 ===")
    print(f"总验证数: {report['statistics']['total_validated']}")
    print(f"有效模型: {report['statistics']['valid_models']}")
    print(f"无效模型: {report['statistics']['invalid_models']}")
    print(f"总错误数: {report['statistics']['total_errors']}")
    print(f"总警告数: {report['statistics']['total_warnings']}")
    print(f"验证成功率: {report['statistics']['valid_models']/report['statistics']['total_validated']*100:.1f}%")
    
    if report['statistics']['common_errors']:
        print("\n常见错误类型:")
        for error_type, count in sorted(report['statistics']['common_errors'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {error_type}: {count} 次")

if __name__ == "__main__":
    main()
