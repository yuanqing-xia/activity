# activity

活动申请资料仓库。

## 目录约定

- `rules/`: 活动规则、申报通知、官方模板。
- `materials/`: 案例素材、证明材料、参考资料。
- `outputs/`: 生成或整理后的申请文档、提交稿。
- `skills/activity-skill/`: 活动申请配套 Codex Skill。
- `.agents/plugins/marketplace.json`: Codex 插件 marketplace 清单。
- `plugins/activity/`: 可分发的 Codex 插件包，内置 `activity-skill`。

## Codex 插件分发

本仓库已整理为 Codex marketplace 源。其他人获得 GitHub 只读权限后，可以添加本仓库并安装插件：

```bash
codex plugin marketplace add yuanqing-xia/activity --ref main
codex plugin add activity@activity
```

插件安装后，使用者可以通过自然语言触发活动申请流程，也可以显式调用：

```text
$activity:activity-skill 帮我分析这个活动规则并列出申报材料清单。
```

## 权限边界

- GitHub 仓库权限只给使用者 `read`，不要授予 `write`、`maintain` 或 `admin`。
- 如需让别人提出修改，建议走 fork 后提交 PR，最终由仓库所有者合并。
- 使用者可以修改自己的本地安装副本，但不会影响本仓库 `main` 分支上的权威版本。

## 真源库约定

在本项目中，用户提到“真源库”或“产品真源库”时，均指远端 GitHub 仓库 `qschouteam/Aicare-Product-Kb`（https://github.com/qschouteam/Aicare-Product-Kb）。每次使用真源库信息时都必须实时查询该仓库；本地缓存、历史摘要、生成材料或旧 clone 只能作为线索，不能作为最终事实来源。

后续每个活动可以按活动名称或日期创建子目录，方便追踪规则、素材和最终版本。
