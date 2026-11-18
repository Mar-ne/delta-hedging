# A/B：从零模拟并生成图表

本文件夹包含真实运行产生的完整数据与图。全部结果由随机 GBM 路径计算，不读取旧终端记录。

- [Hedging_AB.ipynb](Hedging_AB.ipynb)：已更新的结果表、两张图、解释及可选重跑代码。
- [实验报告.md](实验报告.md)：中文报告，覆盖全部 61 组计算和独立验证。
- [experiments_ab.py](experiments_ab.py)：独立程序，从随机数生成数据并画图。
- [results/rerun/fresh_summary.csv](results/rerun/fresh_summary.csv)：61 组完整精度统计。
- [results/rerun/fresh_path_pnl.csv](results/rerun/fresh_path_pnl.csv)：61,000 条逐路径净损益、毛损益与费用。
- [results/rerun/fresh_metadata.json](results/rerun/fresh_metadata.json)：运行参数、种子和库版本。
- [results/audit.json](results/audit.json)：从逐路径记录独立重算汇总的核对结果与文件哈希。

## 重跑

```bash
python -m pip install -r requirements.txt
python experiments_ab.py
```

运行会更新本文件夹内的同名结果。原始历史记录不属于本包。A 仍以 2 天得到最小候选 RMSE；B 按样本亏损约束选出 3 天，验证平均净收益 1.4224、样本亏损比例 0.2%。
