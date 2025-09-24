<#
占位：通过 Cubism Editor 外部集成导出 .moc3 的脚本示例
参数：
 -EditorPath <路径>     Cubism Editor 安装目录，如 D:\Live2D Cubism 5.2
 -TemplateDir <路径>    模板工程目录（含 .cmo3 / 贴图等）
 -OutDir <路径>         导出输出目录
 -DeltaFile <路径>      可选，几何变形 delta JSON
 -LaunchEditor          可选，尝试打开 .cmo3 到 Editor（不做自动操作）
#>

param(
  [Parameter(Mandatory=$true)] [string]$EditorPath,
  [Parameter(Mandatory=$true)] [string]$TemplateDir,
  [Parameter(Mandatory=$true)] [string]$OutDir,
  [Parameter(Mandatory=$false)] [string]$DeltaFile,
  [switch]$LaunchEditor
)

Write-Output "[INFO] Cubism export (stub)"
Write-Output ('EditorPath : ' + $EditorPath)
Write-Output ('TemplateDir: ' + $TemplateDir)
Write-Output ('OutDir     : ' + $OutDir)
if($DeltaFile){ Write-Output ('DeltaFile  : ' + $DeltaFile) }

$ErrorActionPreference = 'Stop'

# 1) 可选：应用几何 delta（占位不改工程，仅日志）
if($DeltaFile -and (Test-Path $DeltaFile)){
  $applyScript = Join-Path (Split-Path -Parent $PSCommandPath) 'apply_geometry_delta.ps1'
  if(Test-Path $applyScript){
    Write-Output ('[INFO] Apply geometry delta (stub): ' + $applyScript)
    powershell -ExecutionPolicy Bypass -File $applyScript -ProjectDir $TemplateDir -DeltaFile $DeltaFile | Out-Null
  } else {
    Write-Warning "未找到 apply_geometry_delta.ps1，跳过"
  }
}

# 2) 可选：尝试启动 Editor 打开 .cmo3（不做自动操作，仅便于人工导出）
$editorExe = Join-Path $EditorPath 'Live2D Cubism Editor.exe'
$cmo3 = Get-ChildItem -Path $TemplateDir -Filter *.cmo3 -File -ErrorAction SilentlyContinue | Select-Object -First 1
if($LaunchEditor -and (Test-Path $editorExe) -and $cmo3){
  $arg = '"' + $cmo3.FullName + '"'
  Start-Process -FilePath $editorExe -ArgumentList $arg | Out-Null
  Write-Output ('[INFO] Launched Editor: ' + $editorExe + ' ' + $cmo3.FullName)
} else {
  if(-not (Test-Path $editorExe)){ Write-Warning "Editor executable not found: $editorExe" }
  if(-not $cmo3){ Write-Warning "No .cmo3 found in template dir; skip launching Editor" }
}

# 3) 导出占位：复制现有资源到 OutDir（作为自动导出的替代）
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$items = @('model.moc3','model.model3.json','model.physics3.json','model.pose3.json')
foreach($i in $items){
  $src = Join-Path $TemplateDir $i
  if(Test-Path $src){
    $dst = Join-Path $OutDir (Split-Path $i -Leaf)
    Copy-Item $src $dst -Force
  }
}
foreach($sub in @('exp','mtn','model.1024','textures')){
  $srcDir = Join-Path $TemplateDir $sub
  if(Test-Path $srcDir){
    $dstDir = Join-Path $OutDir $sub
    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
    $pattern = Join-Path $srcDir '*'
    Copy-Item -Path $pattern -Destination $dstDir -Recurse -Force -ErrorAction SilentlyContinue
  }
}

Write-Output ('[INFO] Export done (stub copy). Output: ' + $OutDir)
exit 0


