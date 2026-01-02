# 最初版本（Lite MVP）：FastAPI 后端需要哪些功能（越简单越好）

> 目标：用 **1–2 周** 做出一个能上线的最小版本：有 **基础内容**（指南/避坑）、有 **审核**（保证可信）、有 **AI 问答**（基于已审核内容），其余全部后置。

## Lite MVP（最初版本）只做这些功能

### 1) 内容浏览（不需要登录也能看）

- 展示已发布内容（只展示审核通过的）
- 过滤：城市/板块（先做 2 维就够：城市 + 板块）
- MVP 建议先内置少量“官方/人工整理指南”（让平台一上线就可用）
- 多语言：UI 与内容支持中英；默认英文（`en`），可切换中文（`zh`）

板块（`section`）建议先固定为以下枚举（MVP 足够用）：

- 落地第一周
- 找房与入住
- 食物与超市
- 交通出行
- 办事与生活
- 安全与诈骗

### 2) 投稿（可选登录；更推荐先做登录再投稿）

- 用户提交内容：**最初版本建议不做“内容类型（type）”**，统一当作一种帖子（Post）
  - 作者只需要选择 **`section`（板块）**（落地第一周/找房与入住/…），再填 `title` + `content`
- 状态：`draft` → `pending_review`

> 重要说明：它们本质上都可以是同一种“帖子”（同一张 `posts` 表）。
> - `section`（板块）= 发布到哪里（落地第一周/找房与入住/…）
> - `type`（内容类型，后置）= 用什么模板展示、审核强度如何、卡片样式如何（例如 Guide vs ScamCase）

### 3) 人工审核（最关键）

- 审核队列：查看待审内容
- 审核动作：通过/驳回（可选“需要补充信息”）
- 发布后可见：`approved` 才对外展示

### 4) AI 问答（最初版本）

- 只有一个接口：用户输入问题 → AI 返回答案
- **强约束**：答案只允许基于“已发布/已审核内容”检索生成，并且返回引用来源（内容标题/ID）
- 先不做复杂对话、多轮记忆、个性化推荐
- 多语言：用户可用中/英文提问；答案用用户当前语言输出；引用内容优先返回相同语言版本

### 5) AI 审查（最初版本：只做“红线拦截”）

- 投稿时自动检查：
  - 隐私泄露（电话/邮箱/证件号/完整门牌）
  - 明显诈骗/引流（转账诱导、加联系方式、非官方外链等）
- 输出：`allow / needs_review / block` + 命中原因
- 目的：减少垃圾与高危内容进入人工队列

### 5.5)（可选但强建议）帖子 AI 自动翻译（中↔英）

- 投稿后可一键生成另一语言版本（先标记 `ai_draft`）
- 高风险板块（找房与入住/安全与诈骗）建议强制人工复核后再作为默认展示

### 6) （可选）举报

- 一键举报已发布内容（诈骗/不实/隐私/广告）
- 后台查看举报列表即可（不需要复杂闭环）

## Lite MVP 明确不做（全部后置）

- 收藏/有用度/积分体系
- 评论/站内私信
- 志愿者工单与匹配
- 多语言协作翻译（人工协作翻译后置；AI 自动翻译见 5.5）
- 高级搜索（全文/向量混合/重排等）
- 房源交易撮合/转租市场

## Lite MVP 的最小角色与权限

- **public**：浏览 + AI 问答
- **user**：投稿（可后置，MVP 也可先只允许管理员发内容）
- **moderator/admin**：审核与发布、下架

## Lite MVP 数据表（最小集合）

- `users`（可选，若先允许匿名浏览与提问）
- `posts`（status/city/section/title/content/created_at/updated_at）
- `moderation_reviews`（post_id/decision/reason/reviewer_id/created_at）
- `ai_answer_logs`（question/answer/quoted_post_ids/created_at）
- `ai_moderation_results`（post_id/decision/tags/snippets/created_at）
- （可选）`reports`

## Lite MVP API（最小端点）

- 内容：
  - `GET /posts`（公开，只返回 approved；支持 query：`city`、`section`）
  - `GET /posts/{id}`（公开）
  - `POST /posts`（投稿，需登录或仅内部）
- 审核：
  - `GET /moderation/queue`（仅 moderator/admin）
  - `POST /moderation/reviews/{post_id}`（approve/reject）
- AI：
  - `POST /ai/ask`（公开或登录）
- （可选）举报：
  - `POST /reports`

---

## 扩展版（Standard MVP）功能清单（后续再做）

## 角色与权限（MVP 版本）

- **user**：浏览、搜索、AI 问答、投稿、评论/反馈、举报
- **moderator**：审核投稿、处理举报、封禁账号/内容、配置敏感词与外链策略
- **admin**：系统配置、角色管理、数据导出、审计查看

## 功能清单（按模块）

### 1) 账户与鉴权

- 邮箱注册/登录（可先不做学校邮箱验证，后续迭代）
- Token 鉴权（JWT/Session 任选，MVP 推荐 JWT）
- 角色权限（RBAC）
- 基础风控：新用户限流（投稿/评论/外链）

### 2) 内容模块（Posts）

内容类型（MVP 建议 3 类）：

- **Guide**：结构化指南/清单（步骤、链接、注意事项、更新时间）
- **Experience**：经验帖（可匿名展示，模板化字段）
- **ScamCase**：诈骗/避坑案例（话术、核验清单、风险等级）

必备能力：

- CRUD：创建/编辑/发布/下架（发布通常需要审核通过）
- 分类与标签：城市、州、学校、主题（住房/交通/超市/安全/办事）
- 媒体上传（图片）：存储 + EXIF 清理（可后置打码）
- 版本/更新记录（MVP 可简化为 updated_at + 简单 changelog）

### 3) 审核与可信（Moderation + Verification）

审核状态（建议）：

- `pending` 待审
- `needs_info` 需补充（退回作者补字段/证据）
- `approved` 通过（可发布）
- `rejected` 驳回

可信状态（展示给用户）：

- `verified` 已验证
- `partially_verified` 部分验证
- `unverified` 待验证

审核队列能力：

- 列表与筛选（按风险、类型、城市、提交时间）
- 审核备注与证据字段
- 审核审计日志（谁在什么时候做了什么）

### 4) 搜索与发现（Discovery）

- 按城市/学校/主题筛选
- 关键词搜索（MVP 可用 Postgres 全文检索）
- 排序策略（MVP）：
  - 优先展示已审核/已验证
  - 优先新内容（近 12 个月）
  - 结合“有用度”加权

### 5) 反馈闭环（Helpfulness / 收藏 / 举报）

- “有用”反馈（替代点赞）：同一用户对同一内容只能一次
- 收藏（Bookmark）
- 举报（Report）：
  - 类型：诈骗/广告/骚扰/隐私泄露/不实信息/其他
  - 处理状态：待处理/处理中/已处理/驳回

### 6) AI 问答（RAG，MVP）

MVP 约束（强建议写死）：

- 只基于平台“已审核内容”检索，不允许自由编造来源
- 输出必须带“来源引用片段 + 内容标题/ID + 更新时间”
- 高风险话题强制加“核验清单 + 风险提示”

功能点：

- `/ai/ask`：问题输入 → 检索 → 生成 → 返回答案与引用
- 多语言：中文默认（可先支持中英）
- 日志：记录问题、引用内容、模型版本、是否触发高风险提示（便于复盘）

### 7) AI 内容审查（发布前初筛）

目标：减少违法/隐私泄露/广告/诈骗引流进入人工审核队列。

输出建议（MVP）：

- decision：ALLOW / ALLOW_WITH_REDACTION / NEEDS_HUMAN_REVIEW / BLOCK
- tags：风险标签（隐私/诈骗/广告/违法）
- evidence_snippets：命中的片段
- redactions_suggested：建议脱敏内容

集成点：

- 投稿创建时触发：先做 AI 初筛，再进入人工审核队列（高风险优先）
- 作者可见：告诉作者“需要修改什么才能通过审核”

### 8) 安全与反滥用（MVP 必要的底座）

- 频控：按 IP / 用户 ID 限制投稿/评论/问答频率
- 外链策略：默认禁止非白名单外链或强制进入人工复审
- 敏感信息识别：电话/邮箱/地址门牌/证件号/银行卡号（命中即提示脱敏）
- 基础反刷：异常账号（短期大量投稿/同文改写）标记

### 9) 后台管理（Admin）

- 用户管理：封禁、角色修改
- 内容管理：下架/删除、批量处理
- 举报处理：队列与备注
- 风控配置：敏感词/外链白名单/频控阈值（MVP 可先写在配置文件，后续做 UI）

## FastAPI 后端模块划分（建议）

- `auth`：JWT、RBAC
- `users`：用户、角色、封禁
- `content`：posts、tags、media
- `moderation`：审核队列、可信状态、审计
- `feedback`：helpful、bookmarks、reports
- `ai`：ask（RAG）、moderate（审查）
- `admin`：后台接口
- `infra`：配置、日志、限流、任务队列

## 数据库（MVP 最小表集合）

- `users`、`roles`、`user_roles`
- `posts`（含 type/status/visibility/city/state/school/updated_at）
- `post_tags`、`tags`
- `post_media`
- `moderation_reviews`（审核记录、备注、证据、审计字段）
- `helpfulness`、`bookmarks`
- `reports`、`report_actions`
- `ai_answer_logs`、`ai_moderation_results`

## API 端点（示例清单）

- Auth：`POST /auth/register` `POST /auth/login` `GET /auth/me`
- Content：
  - `POST /posts` `GET /posts` `GET /posts/{id}` `PATCH /posts/{id}`
  - `POST /posts/{id}/submit_for_review`
- Moderation（受限）：
  - `GET /moderation/queue` `POST /moderation/reviews/{post_id}`
- Feedback：
  - `POST /posts/{id}/helpful` `POST /posts/{id}/bookmark`
  - `POST /reports`
- AI：
  - `POST /ai/ask`
  - `POST /ai/moderate`（内部用或投稿时自动调用）
- Admin（受限）：
  - `GET /admin/users` `PATCH /admin/users/{id}`
  - `PATCH /admin/posts/{id}/take_down`

## MVP 验收标准（上线前必须达成）

- 住房/诈骗类内容能走通：投稿 → AI 初筛 → 人审 → 发布 → 展示可信状态
- AI 问答能引用来源，并能对高风险问题给出明确风险提示
- 举报能闭环处理（至少能记录处理结果与审核人）
- 频控与外链策略生效（防刷与反引流）


