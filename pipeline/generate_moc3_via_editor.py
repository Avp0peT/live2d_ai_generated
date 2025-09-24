#!/usr/bin/env python3
"""
调用 PowerShell 占位脚本，执行 Cubism Editor 导出（占位）。
"""

from pathlib import Path
import subprocess
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--editor', required=True, help='Cubism Editor 安装路径, 如 D:\\Live2D Cubism 5.2')
    ap.add_argument('--delta', help='几何 delta 文件，可选')
    ap.add_argument('--launch', action='store_true', help='是否尝试启动 Editor 打开 cmo3')
    args = ap.parse_args()

    ps = Path('scripts/build_moc3_via_editor.ps1').resolve()
    cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(ps),
           '-EditorPath', args.editor,
           '-TemplateDir', args.template,
           '-OutDir', args.out]
    if args.delta:
        cmd += ['-DeltaFile', args.delta]
    if args.launch:
        cmd += ['-LaunchEditor']
    print('运行:', ' '.join(cmd))
    try:
        subprocess.run(cmd, check=False)
    except Exception:
        pass

    # 兜底：直接复制模板目录中的资源到输出目录（占位导出）
    tpl = Path(args.template)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ['model.moc3','model.model3.json','model.physics3.json','model.pose3.json']:
        p = tpl / name
        if p.exists():
            (out / p.name).write_bytes(p.read_bytes())
    for sub in ['exp','mtn','model.1024','textures']:
        src = tpl / sub
        if src.exists() and src.is_dir():
            dst = out / sub
            dst.mkdir(parents=True, exist_ok=True)
            for f in src.rglob('*'):
                if f.is_file():
                    rel = f.relative_to(src)
                    dst_file = dst / rel
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    dst_file.write_bytes(f.read_bytes())


if __name__ == '__main__':
    main()


