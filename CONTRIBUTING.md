# 贡献指南

## 先开 Issue 的情况

- 章节增删、节顺序调整、图表编号变更；
- 公式口径或符号体系的改动；
- 大段重写（超过一节）。

## 改稿规则

1. **只改根目录的章节 Markdown**，不要改 `build/` 里的 DOCX/PDF。
2. **文件名前缀不是章号**：`01-` 是序章，`02-` 是第 1 章，`18-` 是第 17 章（完整对照见 README 目录表）。
3. 一次 PR 只做一类事：一个 PR 改一章的错字，或一个 PR 修一类公式，不混在一起。
4. 保持既有结构：`# 第 N 章`、`## 一、…`、章末小结/自检/习题；公式编号 `F章-序` 不跳号。
5. 新增图片放 `figures/`，正文用 `![图 N-M 说明](figures/fig-N-M.png)`；能改生成脚本就不要只换 PNG。
6. 数字、公式、习题答案的改动要在 PR 说明里给出复算依据。

## 提交前自检

```bash
python tools/style_check.py --strict
python tools/structure_check.py
python tools/density_check.py --strict
```

不要提交 `build/`、`work/`、`*.docx`、`*.pdf` 或本机路径。

## 勘误 Issue

请使用仓库的“勘误”模板，写清：版本号、章节/页码、原文、问题、建议改法、依据（手册/标准/计算过程）。
