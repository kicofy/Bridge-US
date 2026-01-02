# Developing Plan（Flask 全栈一体，Lite MVP）

> 框架与入口：**Flask**，项目入口文件为 **`app.py`**。  
> 目标：实现 Lite MVP 的前 5 点：**内容浏览（城市+板块）/ 投稿 / 人工审核 / AI 问答 / AI 审查（红线拦截）**。
> 额外约束：**全站中英双语**（至少 `en`/`zh`），**默认英文开发**（代码/接口/字段/文案以英文为主）。

---

## 0. 最小约束（先对齐）

### 多语言（I18n）基本约束

- UI 必须支持 `en`/`zh`，默认 `en`
- 用户可随时切换语言（建议：`/set-lang/<lang>` 或 `?lang=...`）
- 帖子支持双语：
  - `source_lang`：作者投稿语言（en/zh）
  - 可选 `post_translations`：存 AI 翻译版本（`ai_draft` → `human_reviewed`）

### Lite MVP 的板块枚举（`section`）

- 落地第一周
- 找房与入住
- 食物与超市
- 交通出行
- 办事与生活
- 安全与诈骗

### Lite MVP 的最小状态（`status`）

- `draft`：草稿（作者可见）
- `pending_review`：待审核（管理员可见）
- `approved`：已发布（全站可见）
- `rejected`：驳回（作者可见）

---

## 1. 项目结构（建议，保持极简）

> 你要求 `app.py` 作为入口，这里按“能维护但不复杂”的方式拆分。

```
/
  app.py
  requirements.txt
  instance/
    app.db                  # SQLite（最初版本用它）
  templates/
    base.html
    index.html              # 内容列表（城市+板块筛选）
    post_detail.html
    submit.html             # 投稿表单
    admin_login.html
    admin_queue.html        # 审核队列
    ai_chat.html            # AI 问答页面
  static/
    app.css
    app.js                  # 可选：AI 问答前端交互
  services/
    ai.py                   # AI 问答（先用占位/可替换）
    moderation_ai.py        # AI 审查（红线拦截）
    translate_ai.py         # （可选）AI 翻译（中↔英）
  db.py                     # 数据库初始化/连接
  translations/             # Flask-Babel 语言包（后续生成）
```

---

## 2. 开发计划（一步一步）

### Step 1 — 初始化工程（半天）

**目标**：本地可运行 Flask 服务，能看到首页。

- 交付：
  - `requirements.txt`（至少：flask + Flask-Babel）
  - `app.py`（Flask app + 首页路由）
  - `templates/base.html`、`templates/index.html`
- 验收：
  - 运行后访问 `/` 能看到页面
  - 默认语言为英文（`en`），并能切换到中文（`zh`）

---

### Step 2 — SQLite 数据库与 posts 表（半天）

**目标**：有最小数据表，能存储帖子。

- 数据表（最小字段）`posts`：
  - `id`（int）
  - `title`（text）
  - `content`（text）
  - `city`（text，可空）
  - `section`（text，必须是枚举之一）
  - `status`（text：draft/pending_review/approved/rejected）
  - `source_lang`（text：en/zh，默认 en）
  - `created_at`、`updated_at`
- （可选但推荐）数据表 `post_translations`（用于 AI 翻译）：
  - `id`、`post_id`
  - `lang`（en/zh）
  - `title`、`content`
  - `provider`（例如 openai/other）
  - `quality_status`（ai_draft/human_reviewed/rejected）
  - `created_at`、`updated_at`
- 交付：
  - `db.py`：初始化数据库、创建表
  - `app.py`：启动时确保表存在
- 验收：
  - 手动插入一条 `approved` 数据后，首页能显示

---

### Step 3 — 内容浏览（城市 + 板块筛选）（1 天）

**对应 Lite MVP 第 1 点**

**目标**：不登录也能看内容，只显示 `approved`，支持按 `city` 与 `section` 筛选。

- 页面：
  - `GET /`：列表页（query：`city`、`section`）
  - `GET /posts/<id>`：详情页
- 交付：
  - `templates/index.html`：城市输入/下拉、板块下拉、列表展示
  - `templates/post_detail.html`
- 验收：
  - `/` 只出现 approved
  - 切换 `city/section` 过滤生效

---

### Step 4 — 投稿（只要 section + title + content）（1 天）

**对应 Lite MVP 第 2 点**

**目标**：用户提交帖子进入 `pending_review`（不直接发布）。

- 页面/接口：
  - `GET /submit`：投稿表单
  - `POST /submit`：写入 posts，状态 `pending_review`
- 交付：
  - `templates/submit.html`
  - 表单校验：section 必须在枚举内；title/content 非空
- 验收：
  - 投稿成功后不会出现在首页（因为未 approved）

---

### Step 5 — 管理员登录 + 审核队列（1 天）

**对应 Lite MVP 第 3 点**

**目标**：管理员能看待审核内容并 approve/reject。

- 最简管理员方案（最初版本）：
  - 使用一个环境变量 `ADMIN_PASSWORD`（不做复杂用户系统）
  - session 登录
- 页面/接口：
  - `GET /admin/login`、`POST /admin/login`
  - `GET /admin/queue`：只列出 `pending_review`
  - `POST /admin/review/<id>`：approve 或 reject（可带 reason）
- 交付：
  - `templates/admin_login.html`
  - `templates/admin_queue.html`
- 验收：
  - approve 后帖子立刻出现在首页
  - reject 后作者看不到首页，但可以看到“未通过”提示（最初版本可先不做作者查看页）

---

### Step 6 — AI 问答（MVP：只引用已发布内容）（1–2 天）

**对应 Lite MVP 第 4 点**

**目标**：提供一个 AI 问答页面与接口；回答必须“基于已发布内容”的引用。

- 后端接口：
  - `GET /ai`：AI 问答页面
  - `POST /api/ai/ask`：输入 `question` → 返回 `{answer, quotes:[{post_id,title}]}`  
- 最小实现策略（不复杂但可用）：
  - 先做“检索”：从 `approved` 的 posts 里用关键词匹配（最简）找 Top N
  - 生成回答：
    - 第一版可以先用模板化回答（基于 quotes 摘要）
    - 或接入模型（后置配置），但必须同时返回 quotes
  - 多语言：
    - 用户用中文提问 → 中文回答；英文提问 → 英文回答（或按当前 UI 语言）
    - 引用优先返回同语言版本（若存在 `post_translations`）
- 交付：
  - `services/ai.py`
  - `templates/ai_chat.html`
  - `static/app.js`（可选，用 fetch 调接口）
- 验收：
  - 每次回答都返回至少 1 条引用（如果找不到则返回“暂无已审核资料 + 建议投稿/请求人工补充”）

---

### Step 7 — AI 审查（红线拦截）（1 天）

**对应 Lite MVP 第 5 点**

**目标**：投稿时自动扫描隐私/明显诈骗引流，给出 allow/needs_review/block。

- 触发点：
  - `POST /submit` 时，先跑 `services/moderation_ai.py`
- 规则（最初版本先用规则就行）：
  - 隐私：手机号/邮箱/证件号模式命中 → `needs_review`（或 `block`）
  - 明显诈骗：转账/押金/加微信/WhatsApp/Telegram 等引流词 → `needs_review`
  - 非官方外链（http/https）→ `needs_review`
- 行为（简单清晰）：
  - `block`：直接拒绝提交并提示用户删改
  - `needs_review`：允许进入 `pending_review`，并给管理员标红提示
  - `allow`：正常进入 `pending_review`
- 交付：
  - `services/moderation_ai.py`
  - posts 表可增加 `ai_flag`、`ai_reason`（可选；或先不加，写到日志）
- 验收：
  - 提交含手机号/引流词的内容时，系统会提示并标记

---

### Step 8 —（可选）帖子 AI 自动翻译（中↔英）（1 天）

**目标**：对帖子生成另一语言版本，写入 `post_translations`，并标记为 `ai_draft`。

- 触发方式（选一种即可）：
  - 管理员在审核队列里点击“一键生成翻译”
  - 或作者投稿后点击“生成英文/中文版本”
- 约束：
  - 翻译不得添加事实、不得改变数字金额
  - 高风险板块（找房与入住/安全与诈骗）建议必须人工复核后标记 `human_reviewed`
- 验收：
  - 访问帖子详情页时，若用户语言存在翻译版本则优先展示

---

## 3. 最小上线清单（真的要能上线）

- `.env`（或环境变量）
  - `FLASK_SECRET_KEY`
  - `ADMIN_PASSWORD`
- 部署（任选一种，保持简单）
  - gunicorn/uwsgi + Nginx（Linux）
  - 或先用平台托管（后续再规范）
- 基本安全：
  - 管理后台必须登录
  - `POST` 接口加 CSRF（可后置，但建议尽快补）

---

## 4. 后续迭代（明确后置，避免变复杂）

- 用户系统（注册/登录/作者查看自己的投稿状态）
- “有用/收藏/举报”闭环
- 评论
- 真正的向量检索（pgvector）与更强 RAG
- 志愿者工单


