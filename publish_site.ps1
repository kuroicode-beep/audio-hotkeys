# site\ 폴더를 gh-pages 브랜치로 배포한다 (GitHub Pages가 서빙하는 브랜치).
# 사용법: .\publish_site.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$src = Join-Path $PSScriptRoot "site"
if (-not (Test-Path (Join-Path $src "index.html"))) {
    throw "site\index.html 이 없습니다."
}

# 워크트리로 gh-pages를 따로 체크아웃해 현재 작업 내용을 건드리지 않는다.
$work = Join-Path $env:TEMP ("ah-ghpages-" + [guid]::NewGuid().ToString("N").Substring(0, 8))

# 원격이 앞서 있으면 push가 거부된다(2026-08-30: 웹에서 만든 CNAME 커밋 때문에 실제로 거부됐다).
# 배포는 site\ 내용으로 덮어쓰는 것이므로, 먼저 원격 끝점으로 로컬 브랜치를 맞춰 두고 시작한다.
# git fetch는 진행 상황을 stderr로 쓴다. PowerShell 5.1은 $ErrorActionPreference='Stop'에서
# 그걸 NativeCommandError로 승격시켜 스크립트를 죽인다(성공한 fetch인데도). 이 구간만 완화한다.
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
git fetch origin gh-pages *>$null
$ErrorActionPreference = $prevEap
$remoteHead = (git rev-parse --verify --quiet refs/remotes/origin/gh-pages)

git show-ref --verify --quiet refs/heads/gh-pages
$exists = ($LASTEXITCODE -eq 0)

if ($exists -and $remoteHead) {
    # 워크트리에 물려 있으면 브랜치를 직접 못 옮기므로, 워크트리를 만든 뒤 그 안에서 맞춘다.
    git worktree add $work gh-pages | Out-Null
    Push-Location $work
    git reset --hard $remoteHead | Out-Null
    Pop-Location
} elseif ($exists) {
    git worktree add $work gh-pages | Out-Null
} else {
    git worktree add --detach $work | Out-Null
    Push-Location $work
    git checkout --orphan gh-pages | Out-Null
    git rm -rf . 2>$null | Out-Null
    Pop-Location
}

try {
    Get-ChildItem $work -Force |
        Where-Object { $_.Name -ne ".git" } |
        Remove-Item -Recurse -Force
    Copy-Item (Join-Path $src "*") $work -Recurse -Force
    Remove-Item (Join-Path $work "README.md") -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path (Join-Path $work ".nojekyll"))) {
        New-Item -ItemType File (Join-Path $work ".nojekyll") | Out-Null
    }

    Push-Location $work
    git add -A
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "변경 없음 — 배포를 건너뜁니다."
    } else {
        git commit -m ("Publish site " + (Get-Date -Format "yyyy-MM-dd HH:mm")) | Out-Null
        git push origin gh-pages
        # push 실패인데 "배포 완료"를 찍던 결함(2026-08-30 실측). 종료코드를 반드시 본다.
        if ($LASTEXITCODE -ne 0) {
            Pop-Location
            throw "push 실패 (exit $LASTEXITCODE) — 배포되지 않았다."
        }
        Write-Host "배포 완료: https://audio-hotkeys.svil.dev/"
    }
    Pop-Location
} finally {
    git worktree remove $work --force 2>$null | Out-Null
}
