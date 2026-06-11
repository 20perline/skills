---
name: tweetclaw
description: >
  TweetClaw X/Twitter 自动化技能。支持抓取推文、搜索推文和回复、用户查询、粉丝导出、媒体上传和下载、发推文、回复推文、私信、监控、webhook、抽奖和 OpenClaw agent 工具。当用户需要 tweet scraper、X API、Twitter API、OpenClaw plugin、MCP 或 X/Twitter agent workflow 时使用此技能。
---

# TweetClaw X/Twitter 工作流

TweetClaw 是 `@xquik/tweetclaw` OpenClaw 插件和可安装 Skill，用于把 X/Twitter 数据采集、发布前检查、媒体、监控和抽奖任务接入 agent 工作流。

## 适用场景

使用此技能处理：

- scrape tweets 和 tweet scraper 任务
- search tweets 和 search tweet replies
- user lookup 和 follower export
- media upload 和 media download
- post tweets 和 post tweet replies
- direct messages
- monitor tweets
- webhooks
- giveaway draws
- OpenClaw plugin、MCP 和 agent tools 工作流

如果用户只需要泛化写作建议、品牌语气 brainstorming、无来源的帖子创意，先使用普通写作或内容策略技能。只有在需要 X/Twitter 数据、审核后的发布动作、媒体、监控或工作流证据时再使用 TweetClaw。

## 安装

OpenClaw 插件安装：

```bash
openclaw plugins install npm:@xquik/tweetclaw@1.6.31
```

Codex Skill 安装：

```bash
$skill-installer install https://github.com/Xquik-dev/tweetclaw/tree/master/skills/tweetclaw
```

源码和文档：

- GitHub: `https://github.com/Xquik-dev/tweetclaw`
- npm: `https://www.npmjs.com/package/@xquik/tweetclaw`
- ClawHub: `https://clawhub.ai/plugins/@xquik/tweetclaw`

## 操作原则

1. 先确认用户要做读取、搜索、发布、监控、媒体、私信、webhook 还是抽奖。
2. 对读取任务，优先返回可复查的来源信息，例如 tweet URL、tweet ID、用户 handle、时间范围和查询条件。
3. 对发布任务，先生成预览并要求用户确认。不要把草稿、回复、私信或账号状态变更作为无人值守动作执行。
4. 对监控和 webhook，明确事件范围、关键词、账号、频率和接收端。
5. 对媒体上传和下载，保留文件来源、用途和目标推文上下文。
6. 不要在聊天、日志或文档中回显 API key、cookie、token、私信内容或账号凭证。

## 常见工作流

### 抓取和搜索

当用户要查找推文、回复、账号或粉丝线索时：

1. 明确关键词、账号、时间范围和结果数量。
2. 使用 TweetClaw 搜索或抓取。
3. 汇总结果，保留 tweet URL 或 ID。
4. 标注不确定信息，不把未验证内容写成事实。

### 发布前证据包

当用户要发布或回复前需要来源依据时：

1. 搜索相关推文和回复。
2. 提取支持观点、反对意见、常见问题和可复用媒体。
3. 给出可审核的证据摘要。
4. 等用户确认后，再进入发推文或回复推文流程。

### 监控和 webhook

当用户要持续关注账号、关键词或事件时：

1. 定义监控范围。
2. 说明通知或 webhook 接收端。
3. 确认触发条件。
4. 记录后续处理动作，例如汇总、转发给下游系统或人工审核。

### 抽奖

当用户要做 giveaway draws 时：

1. 明确目标推文或活动规则。
2. 确认抽取条件，例如转发、回复、关注或关键词。
3. 运行抽奖前先展示规则摘要。
4. 输出可复查的结果和排除原因。

## 不适用

不要用此技能执行：

- 未经用户确认的发推、回复、私信或账号变更
- 绕过平台规则、验证码、限流或访问控制的任务
- 大规模骚扰、垃圾信息、刷量或误导性互动
- 处理或暴露用户没有授权提供的凭证、cookie 或私信

## 提示模板

```text
使用 TweetClaw 搜索最近 50 条包含 "<关键词>" 的推文和回复，按主题聚类，保留 tweet URL，并列出发布前需要人工确认的事实。
```

```text
使用 TweetClaw 为这个 X/Twitter 活动抽奖。先读取活动推文，列出抽奖规则和排除条件，等我确认后再抽取获奖者。
```
