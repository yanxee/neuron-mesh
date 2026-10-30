## What changed / 变更内容

Describe the user-visible or protocol-level change.

说明用户可见或协议级变更。

## Why / 原因

Explain the problem, evidence and tradeoffs.

说明问题、证据和权衡。

## Verification / 验证

- [ ] `ruff check .`
- [ ] `pytest`
- [ ] `python scripts/e2e_check.py` when routing, memory or lifecycle behavior changes / 路由、记忆或生命周期变更时执行
- [ ] Added or updated tests / 已增加或更新测试
- [ ] Updated English and Chinese paired documentation or explicitly marked it unnecessary / 已更新中英文成对文档，或明确说明无需更新

## Safety and compatibility / 安全与兼容

- [ ] No credentials, private memory, model weights or user data are included / 未包含凭证、私有记忆、模型权重或用户数据
- [ ] API/version behavior is backward compatible or migration is documented / API/版本行为向后兼容，或已记录迁移
- [ ] Performance/research claims include hardware, versions and failure boundaries / 性能/研究主张包含硬件、版本和失败边界

Closes / 关闭 #

