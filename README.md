# Delta Hedging: Replication, Optimal Rebalancing & Volatility Trading

一个 Python 数学金融学习项目：从 GBM 股价路径和自融资复制组合出发，研究离散对冲误差、交易成本和波动率差异。

## 从哪里开始

| 内容 | Notebook | 说明 |
|---|---|---|
| 基础实验 | [Delta_Hedging.ipynb](Delta_Hedging.ipynb) | 无交易成本；比较调仓频率与真实 drift |
| A/B 扩展 | [advanced/Hedging_AB.ipynb](advanced/Hedging_AB.ipynb) | 含交易成本的频率选择、波动率交易和独立验证 |

最新完整结果见 [A/B 实验报告](advanced/实验报告.md)，从零生成数据的代码见 [experiments_ab.py](advanced/experiments_ab.py)。

## A：交易成本下，多久调仓一次？

初始股价和行权价均为 100，期限 1 年，无风险利率 5%，真实 drift 10%。实际与定价波动率均为 20%，每笔股票交易收费 0.1%，包含初始建仓、后续调仓和到期平仓。一年划分为 3650 步，每批 1000 条路径。

在 0.1、0.5、1、2、3、5、10、15、30、60 天的候选间隔中，以含成本复制误差 RMSE 最小为目标，两批路径均选出 **每 2 天调仓**：

| 随机种子 | 1 天 RMSE | 2 天 RMSE | 3 天 RMSE |
|---|---:|---:|---:|
| 42 | 0.8532 | **0.7620** | 0.8040 |
| 43 | 0.8527 | **0.7825** | 0.7938 |

![A：RMSE、交易成本和损益波动](advanced/results/rerun/A_optimal_hedging.png)

## B：对冲后的损益来自哪里？

固定定价波动率为 20%，先关闭交易成本。每 0.1 天调仓时：

| 实际波动率 | 平均对冲损益 |
|---|---:|
| 15% | +1.8251 |
| 20% | −0.0058 |
| 25% | −1.9162 |

实际波动率低于定价波动率时，卖出期权并对冲产生正的平均毛损益；较高时转为负值。结果与 Gamma 加权的方差差有关，完整解释见报告。

加入 0.1% 股票交易成本后，在实际波动率 15%、定价波动率 20% 的情景中，用“样本亏损比例不超过 1%，同时平均净损益最高”的规则选出 **3 天**。固定该策略，以独立种子 44 验证：

| 样本 | 平均净损益 | 标准差 | 亏损比例 | 第 5 百分位 |
|---|---:|---:|---:|---:|
| 筛选：种子 43 | 1.3960 | 0.7758 | 0.3% | 0.3115 |
| 验证：种子 44 | **1.4224** | 0.7532 | **0.2%** | 0.3172 |

![B：交易频率、净收益和亏损概率](advanced/results/rerun/B_volatility_trading.png)

A 与 B 的参数和评价目标不同，选出的频率不能直接互换。

## 数据与复现

最新扩展的数据全部由独立程序从随机股价路径计算，未读取先前手动记录的结果表。

- [61 组完整统计](advanced/results/rerun/fresh_summary.csv)
- [61,000 条逐路径损益记录](advanced/results/rerun/fresh_path_pnl.csv)：同一路径会在不同调仓频率下重复评估，这不是 61,000 条独立股价路径。
- [运行参数、种子和 NumPy 版本](advanced/results/rerun/fresh_metadata.json)
- [逐路径数据核对与文件哈希](advanced/results/audit.json)：已从逐路径记录独立重算六项汇总指标，并核对净损益、毛损益和成本之间的关系。

```bash
cd advanced
python -m pip install -r requirements.txt
python experiments_ab.py
```

程序自动运行全部实验，生成数据和 PNG 图，结果写入 `advanced/results/rerun/`。也可以在 VS Code 或 Jupyter 中运行 A/B Notebook 下方的重跑单元。

基础版本仍可通过 `python delta_hedging_clean.py` 运行。

## 局限

常波动率 GBM、无股息、碎股交易和理想融资均为模型假设，未使用真实市场数据。未来实际波动率在市场中未知。本次选择只针对指定参数、候选网格和有限样本；样本亏损比例低于 1% 不代表真实亏损概率必然低于 1%，也不构成真实市场盈利验证。
