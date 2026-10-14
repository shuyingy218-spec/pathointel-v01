---
name: pathointel-product-research
description: Research pathology reagent and matching automation products from public sources, keep field-level evidence, compare them with a configurable company baseline, and prepare a source-linked product brief. Use for PathoIntel product lines or a similar medical product competitor dossier.
---

# PathoIntel Product Research

Build a reusable product dossier for one named product line and one comparison baseline. For this project, the default baseline is 达科为 and the first line is EBER/CISH; ask only when a different line or baseline is essential and cannot be inferred.

## Research and record

1. Search public manufacturer product pages, catalogues, instructions for use, and official regulator records. Treat search titles and snippets only as leads. Open the original page before writing a product fact.
2. Record the **exact reagent or instrument product and model**. For each fact, capture one field from: 目标试剂、配套自动化设备、组成、技术特点、产品布局、价格与口径、注册备案情况. Keep the original URL, page/region/version note, retrieval date, and evidence status.
3. Keep manufacturer claims distinct from independently verified regulatory facts. A manufacturer's equipment page does not prove a specific reagent SKU is compatible. For price, retain currency, unit, region, date, and quote/list/transaction basis. For registration, retain the jurisdiction, registrant, certificate number, and status; use the regulator's record where possible.
4. If a field lacks support, write **未公开／待人工核验**. Never infer product absence from one page, turn a snippet into a verified fact, or score performance from marketing text or unquantified images.
5. Compare the baseline and one rival within the same product line, geography, model version, and use case. Show evidence side by side and identify gaps; make any judgment separately with its supporting sources.

## Deliverables and acceptance

- Product evidence cards: one row per vendor and exact product, with field-level facts and clickable sources.
- An exportable UTF-8 evidence CSV with columns 产品线、厂商、产品名称、信息项目、内容、来源URL、来源说明、获取日期、证据状态.
- A baseline-versus-rival brief with all seven fields, original links, explicit missing fields, and a short section for human analysis and next verification.
- A working loop in PathoIntel: search → open original source → save reviewed fact → see the card and comparison update → export → re-import the CSV in a new session.

When working on the public PathoIntel site, keep the source data and the skill in the same repository, validate CSV round trips and one complete browser workflow, and verify the deployed page before calling it delivered. The public site stores session data only; remind users to download a backup. Do not publish internal documents, patient data, or unapproved excerpts.

This workflow adapts the comparison structure in [Anthropic's competitive-brief](https://github.com/anthropics/knowledge-work-plugins/blob/main/product-management/skills/competitive-brief/SKILL.md) and the evidence traceability principles in [K-Dense's market-research-reports](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/market-research-reports/SKILL.md). Those source skills are guidance, not web-search or regulatory databases.
