# 为 NeuronMesh 做贡献

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md)

NeuronMesh 是一个早期研究项目。欢迎小型、可测试且文档清晰的贡献。你不需要实现完整愿景或运行大型模型才能提供帮助。

如果你是第一次参与，请先阅读[贡献者入口指南](https://yanxee.github.io/neuron-mesh/join.zh-CN.html)，根据你想投入的时间和专业能力选择路径。

## 选择贡献方式

| 你可以提供 | 适合的首次贡献 |
| --- | --- |
| 一台电脑或浏览器 | 运行 [10 分钟演示](docs/DEMO.zh-CN.md)，发布兼容性报告 |
| Python 与测试经验 | 认领具有明确验收标准的 `good first issue` |
| 分布式系统经验 | 评审传输设计、NAT 矩阵或故障恢复语义 |
| LLM Serving 经验 | 增加 llama.cpp/vLLM 适配器或阶段执行一致性测试 |
| 研究能力 | 提出包含基线、指标和失败边界的可复现假设 |
| 安全与隐私能力 | 评审命名空间授权、密钥生命周期、记忆投毒或滥用控制 |
| 文档与设计能力 | 改进入门体验、图表、翻译或实验报告 |
| WebXR/OpenXR 经验 | 定义不绑定单一引擎的适配器契约 |

开放式问题应发布到 [GitHub Discussions](https://github.com/yanxee/neuron-mesh/discussions)。当存在另一个人可以验证的具体变更、测试或实验时，请使用 Issue。

## 首次贡献流程

1. 选择一个开放 Issue；如果会修改 API、存储格式或信任边界，先开一个简短的设计 Issue。
2. 说明你计划产生的成果和准备验证的边界。如有必要，维护者会确认范围。
3. Fork 仓库，在主题分支上进行聚焦修改。
4. 运行下方验证命令，并在 Pull Request 中附上输出或 CI 链接。
5. 在 Pull Request 中说明用户可见行为、失败模式以及仍未解决的限制。

维护者响应为尽力而为。新 Issue 和 Pull Request 通常会在三个工作日内完成初步分类；超过后可礼貌催促。

## 开发环境

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
python scripts/e2e_check.py
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\e2e_check.py
```

以下检查全部通过后，Pull Request 才进入评审：

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\e2e_check.py
```

## Pull Request

- 除非显式进行版本升级，保持 OpenAI 兼容接口和内部 API 向后兼容。
- 为路由、记忆持久性、权限和故障恢复增加测试。
- 保持变更可评审；拆分无关重构、协议变更和格式化改动。
- 不要在仓库中放入原始凭证、用户记忆或模型权重。
- 继续区分已实现能力和路线图项目。
- 性能数据必须包含硬件、模型、输入/输出长度和网络条件。
- 配置、存储格式或 API 变更必须提供简短迁移说明。
- 披露实质性 AI 辅助，并对提交的每一行负责。

## 研究主张

关于记忆持久性、故障恢复、去中心化或模型质量的主张，必须包含可复现测试和明确的失败边界。

影响架构的变更还必须说明权威状态所有者、生命周期/幂等行为、兼容与迁移路径、分区/故障行为、安全边界及回滚路径。请先阅读 [系统架构](ARCHITECTURE.zh-CN.md)和[架构变更清单](docs/architecture/README.zh-CN.md#变更检查清单)。

实验和基准使用以下证据模板：

```text
问题：
当前行为和基线：
假设：
硬件 / 操作系统 / 软件版本：
工作负载和随机种子：
指标和验收阈值：
观测结果：
失败模式和有效性威胁：
产物或复现命令：
```

只要测试可复现，负面结果同样有价值。不要在不公开工作负载的情况下只展示经过挑选的标题数字。

## 文档、翻译和兼容性报告

小型非代码贡献同样重要。兼容性报告应包含操作系统、CPU 架构、Python 版本、是否使用 Docker、准确命令、预期输出以及完整的非敏感错误信息。翻译必须保持研究主张、限制和安全警告与源文档等价。

双语文档必须同时更新成对文件。英文文件使用 `name.md`，中文文件使用 `name.zh-CN.md`；中文研究报告的英文版本放在 `docs/research/`。CI 会检查语言切换链接和必需文件是否存在。

## 评审与认可

评审聚焦正确性、可复现性、安全边界和可维护性。贡献者在对某一领域展现可靠判断后，可能被邀请评审该子系统。代码、测试、基准、协议分析、文档、翻译和可复现部署报告都会在发布说明中署名；贡献者可以选择退出公开署名。

决策流程和贡献者阶梯见[治理规则](GOVERNANCE.zh-CN.md)。
