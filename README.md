# Stocks Tools

一个用于股票数据获取、筛选与可视化的小工具集合，包含简单的凯利公式模拟、基金报告下载、VCP 条件筛选与施洛斯策略示例。

## 环境要求
- Python >= 3.9
- 建议使用虚拟环境（venv/conda）

## 安装
```bash
pip install -r "requirements.txt"
```

## 主要脚本
- src/kelly.py：凯利公式计算与收益曲线模拟。
- src/fund_downloader.py：根据基金代码批量下载 PDF 报告（东方财富接口）。
- src/vcp.py：简单的 VCP 条件筛选示例（含均线等基础条件）。
- src/walter_schloss.py：沃尔特·施洛斯低估值选股策略示例（按基本财务条件筛选）。

> 注：若你的仓库中脚本名称为大写/小写不同，请以实际文件名为准。

## 使用示例
- 运行凯利公式模拟：
```bash
python src/kelly.py
```

- 下载基金 PDF（示例包含多个基金代码）：
```bash
python src/fund_downloader.py
```

- 施洛斯策略筛选：
```bash
python src/walter_schloss.py
```

- 简单 VCP 条件筛选：
```bash
python src/vcp.py
```

## 代码规范与格式化
- 运行 Ruff 静态检查并自动修复：
```bash
pip install ruff
ruff check "." --fix
```
- 本项目提供 `pyproject.toml` 与 `ruff.toml`，已配置基础规则（行宽 100、isort 排序等）。

## 常见问题
- 未安装依赖：请先执行 `pip install -r requirements.txt`。
- `mpl_finance` 已较旧，推荐迁移到 `mplfinance`；若使用旧接口会看到提示或导入警告。
- `akshare` 接口依赖网络环境，若数据为空或报错，可稍后重试。

## 免责声明
本仓库示例仅用于学习与研究，任何内容不构成投资建议。投资有风险，入市需谨慎。
