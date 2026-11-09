# AGENTS.md

本文件是本仓库对 Agent 的硬性协作规则，优先级高于技能、计划和任务描述中的通用步骤。

## 1. superpowers plans / specs 的提交

`docs/superpowers/plans/` 和 `docs/superpowers/specs/` 下的文件由人工决定是否进入版本库。

- Agent 可以创建、修改这些文件，并在执行任务时使用它们。
- 需要提交时，先列出文件与提交信息，等待人工明确同意；Agent 不自行 `git add`、`git commit`，也不把它们带入其他提交。
- 计划或技能里的“提交”步骤，不构成对这些文件的提交授权。

## 2. push 审批

执行任何推送前，先报告目标远端、分支、提交范围和可能触发的 CI/Release，等待人工明确同意。

- 覆盖 `git push`、`git push --tags`、`git push --force`、删除远端分支等所有形式。
- 未获同意时，只做本地提交，不推送。
- 人工的明确回复（例如“可以推送”“批准 push”）才算同意；沉默、默认或此前的一般性授权不算。

## 3. yun SDK 与 yunpyopt 版本同步

`yun-sdk-version.txt` 的 **major.minor**（前两位）发生变化时，必须同步升级根目录
`VERSION` 中的包版本，并让 `yunpyopt` 的 major.minor 与 SDK 保持一致。`pyproject.toml`
的 `version` 是派生副本，只由 `python scripts/version.py set/bump` 改写：

- SDK `0.2.x → 0.3.0`：`yunpyopt` 必须升到 `0.3.x`；
- SDK 只变 patch（`0.3.0 → 0.3.1`）不触发强制升级，`yunpyopt` 可按需发 patch；
- 升级时同步更新 `CHANGELOG.md`；README/docs 不写死当前版本，wheel 名与下载 URL
  使用 `<version>`、`<sdk-version>` 占位符。

该规则由 `scripts/version.py check` 校验，CI 的 `quality` job 与 `release.yml` 的
`version` job 都会运行；`tests/test_version_policy.py` 覆盖脚本行为。版本不一致时
CI/Release 直接失败。
