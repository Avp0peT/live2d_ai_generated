# 使用 Cubism Editor 外部集成 API 进行自动导出（示例实现）
# 说明：需在 Cubism Editor 中开启外部集成 API（参照官方文档），
# 并确认本机 API 监听地址和端口（通过 -ApiUrl 指定）。
#
# 参数：
#  -ApiUrl <string>        外部集成 API 基地址，如 http://127.0.0.1:3333
#  -TemplateDir <string>   模板工程目录（含 .cmo3 / 贴图等）
#  -OutDir <string>        导出输出目录
#  -EditorPath <string>    可选，Editor 安装路径（用于未运行时启动）
#  -LaunchEditor           可选，若提供 EditorPath 则尝试启动并加载 .cmo3
#  -DeltaFile <string>     可选，几何变形 delta（由业务自定义，示例中透传）

param(
  [Parameter(Mandatory=$true)] [string]$ApiUrl,
  [Parameter(Mandatory=$true)] [string]$TemplateDir,
  [Parameter(Mandatory=$true)] [string]$OutDir,
  [Parameter(Mandatory=$false)] [string]$EditorPath,
  [switch]$LaunchEditor,
  [Parameter(Mandatory=$false)] [string]$DeltaFile
)

$ErrorActionPreference = 'Stop'
Write-Output "[INFO] Cubism External API export"
Write-Output ("ApiUrl      : " + $ApiUrl)
Write-Output ("TemplateDir : " + $TemplateDir)
Write-Output ("OutDir      : " + $OutDir)
if($EditorPath){ Write-Output ("EditorPath  : " + $EditorPath) }
if($DeltaFile){ Write-Output ("DeltaFile   : " + $DeltaFile) }

# 尝试启动 Editor（可选）
if($LaunchEditor -and $EditorPath){
  $editorExe = Join-Path $EditorPath 'Live2D Cubism Editor.exe'
  $cmo3 = Get-ChildItem -Path $TemplateDir -Filter *.cmo3 -File -ErrorAction SilentlyContinue | Select-Object -First 1
  if((Test-Path $editorExe) -and $cmo3){
    $arg = '"' + $cmo3.FullName + '"'
    Start-Process -FilePath $editorExe -ArgumentList $arg | Out-Null
    Write-Output ("[INFO] Launched Editor: " + $editorExe + ' ' + $cmo3.FullName)
    Start-Sleep -Seconds 3
  } else {
    Write-Warning "Editor 可执行文件或 .cmo3 未找到，跳过启动。"
  }
}

# 构造 API 端点（以下路径与负载需依据官方文档实际调整）
$openEndpoint   = ($ApiUrl.TrimEnd('/')) + '/project/open'
$exportEndpoint = ($ApiUrl.TrimEnd('/')) + '/model/export'
$applyEndpoint  = ($ApiUrl.TrimEnd('/')) + '/geometry/apply'

# 1) 打开工程
$cmo3Path = (Get-ChildItem -Path $TemplateDir -Filter *.cmo3 -File -ErrorAction SilentlyContinue | Select-Object -First 1)
if(-not $cmo3Path){
  Write-Error "未在模板目录找到 .cmo3 文件：$TemplateDir"
  exit 1
}
Write-Output ("[INFO] Open project: " + $cmo3Path.FullName)
try {
  $resp = Invoke-RestMethod -Method Post -Uri $openEndpoint -Body (@{ path = $cmo3Path.FullName } | ConvertTo-Json) -ContentType 'application/json'
  Write-Output ("[INFO] Open response: " + ($resp | ConvertTo-Json -Compress))
} catch {
  Write-Warning ("打开工程失败：" + $_.Exception.Message)
}

# 2) 可选：应用几何 delta（具体格式请按官方 API 调整）
if($DeltaFile -and (Test-Path $DeltaFile)){
  Write-Output ("[INFO] Apply geometry delta: " + $DeltaFile)
  try {
    $deltaJson = Get-Content -Raw -Path $DeltaFile -Encoding UTF8
    $resp2 = Invoke-RestMethod -Method Post -Uri $applyEndpoint -Body $deltaJson -ContentType 'application/json'
    Write-Output ("[INFO] Apply response: " + ($resp2 | ConvertTo-Json -Compress))
  } catch {
    Write-Warning ("应用几何 delta 失败：" + $_.Exception.Message)
  }
}

# 3) 导出 .moc3（实际参数按官方 API 填写）
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Write-Output ("[INFO] Export model to: " + $OutDir)
try {
  $payload = @{ outputDir = (Resolve-Path $OutDir).Path } | ConvertTo-Json
  $resp3 = Invoke-RestMethod -Method Post -Uri $exportEndpoint -Body $payload -ContentType 'application/json'
  Write-Output ("[INFO] Export response: " + ($resp3 | ConvertTo-Json -Compress))
} catch {
  Write-Warning ("导出失败：" + $_.Exception.Message)
  exit 1
}

Write-Output "[INFO] 完成"
exit 0


