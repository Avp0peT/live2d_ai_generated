# 占位：在 Cubism Editor 中应用 geometry_delta.json 的脚本示例
# 实际实现需依赖 Editor 的外部集成 API。

param(
  [Parameter(Mandatory=$true)] [string]$ProjectDir,
  [Parameter(Mandatory=$true)] [string]$DeltaFile
)

Write-Host "[INFO] Apply geometry delta to project (stub)"
Write-Host "ProjectDir: $ProjectDir"
Write-Host "DeltaFile : $DeltaFile"
Write-Host "[WARN] 该脚本为占位示例，未实际修改工程。"
exit 0


