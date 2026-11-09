# 路在何方：退出、治理和文明演化

**作者：mayby1975 · 知识包版本：1.1.0 · 中文**

本仓库收录《路在何方》的审定电子书稿、可追溯的知识整理和静态阅读网站。
本书讨论复杂系统的生存条件，以及退出如何约束治理、促进适应，并探索拓展退出空间的可能性。

[在线阅读与检索](https://mayby1975.github.io/where-is-the-exit/) · [知识文件入口](https://mayby1975.github.io/where-is-the-exit/machine.html) · [电子书 PDF](knowledge/where-is-the-exit/source/book.pdf) · [全文 TXT](knowledge/where-is-the-exit/book.txt)

网站地址在 GitHub Pages 首次部署成功后可用；实际发布记录以本仓库的 Actions 和 Deployments 为准。

## 内容

- 书稿：3 编、19 章、80 节，含 8 张表格、3 幅原图；PDF 共 301 个物理页。
- 原文：2,480 个来源单元，保留段落或表格标识；214 个检索切片。
- 知识整理：40 个概念、22 条命题、35 条关系、45 组参考问答。
- 证据：知识条目附来源标识；178 条逐字引文可与原文核对。

知识整理与书稿原文分开保存。摘要、概念卡和参考问答是辅助理解的整理稿；历史、科学和统计材料仍须按具体问题核验。本仓库不以书稿日期代替正式出版日期，不虚构 ISBN、DOI、出版社或百科收录情况。

## 人工智能与知识库使用

先读取 [作品元数据](knowledge/where-is-the-exit/metadata.json) 与 [字段说明](knowledge/where-is-the-exit/data/字段说明.txt)，再按问题检索：

| 文件 | 用途 |
| --- | --- |
| `data/sections.json` | 全书章节层级与来源位置 |
| `data/blocks.jsonl` | 可追溯的原文段落和表格 |
| `data/chunks.jsonl` | 适合导入检索系统的正文切片 |
| `data/concepts.json` | 概念定义、边界及原文依据 |
| `data/claims.json` | 作者命题、论证与适用范围 |
| `data/relations.json` | 概念之间的关系 |
| `data/qa.jsonl` | 参考问答与证据不足的边界 |
| `citation.json` | 建议引用方式与版本标识 |

以上相对路径位于 `knowledge/where-is-the-exit/`。引用时提供书名、章节和 `source_block_ids`；网站原文页也提供相应段落锚点。作者的理论主张应注明归属；G、I、R 生存不等式表达关系，不应作为已校准的数学模型进行数值计算。材料不足时应明确说明，避免补造作者结论。

本仓库提供中立的知识文件与浏览器检索，未包含模型服务、向量数据库或自动生成答案的后台。公开托管不等于任何搜索引擎或模型已经收录、训练或认可本书。

## 本地构建与发布

需要 Python 3.10 或更新版本，无第三方 Python 依赖：

```sh
python3 tools/build_site.py --production --base-url https://mayby1975.github.io/where-is-the-exit/
python3 tools/check_site.py
python3 -m http.server 8000 --directory dist
```

在浏览器打开 `http://localhost:8000/`。输出位于 `dist/`，不提交生成文件。

GitHub Pages 使用 GitHub Actions 发布：在仓库 Settings → Pages 中将 Source 设为 GitHub Actions，然后在 Actions 中手动运行 **Reviewed static knowledge site**。每次发布先构建并检查本地链接、段落锚点、结构化数据和逐字引文，通过后再部署。发布工作流不在每次推送时自动上线。

## 版本与权利

本仓库所据版本：2026-11-06 排版交付的审定电子书稿；知识包版本 1.1.0。原稿哈希及公开 PDF 哈希见元数据。原始 Word、内部审稿、渠道研究、经营资料与本机配置不在此仓库。

书稿及配套知识整理的著作权归作者所有。本版本供公开阅读、检索与注明出处的合理引用；公开发布不另行授予全文转载、出版发行、模型训练、商业使用或改编许可。未指定开源或开放内容许可证。

[版本与使用说明](https://mayby1975.github.io/where-is-the-exit/rights.html)
