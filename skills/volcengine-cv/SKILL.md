---
name: volcengine-cv
description: >
  火山引擎即梦 (Jimeng) 图像和视频生成技能。支持即梦4.0图像生成（文生图、图生图、多图编辑）和即梦3.0视频生成（文生视频、图生视频-首帧、图生视频-首尾帧、图生视频-运镜）。当用户需要使用火山引擎、即梦、Jimeng、volcengine 生成图像或视频时，使用此技能。也适用于用户提到 AI 生图、AI 视频生成、文生图、文生视频、图生视频等场景，尤其是在项目中已有火山引擎相关配置或代码时。
---

# 火山引擎即梦图像/视频生成

通过火山引擎即梦 API 生成图像和视频。支持纯 Python 脚本调用，无需额外依赖。

## 凭证配置

凭证加载优先级（与火山引擎官方 SDK 一致）：

1. **环境变量**：`VOLC_ACCESSKEY` + `VOLC_SECRETKEY`
2. **配置文件**：`~/.volc/config`（JSON 格式）

配置文件示例（`~/.volc/config`）：
```json
{"ak": "AKLTxxxxxxxxxxxx", "sk": "xxxxxxxxxxxxxxxx"}
```

## 脚本位置

所有脚本位于 `scripts/` 目录下：
- `image.py` — 图像生成 CLI
- `video.py` — 视频生成 CLI
- `auth.py` — 凭证加载 + V4 HMAC-SHA256 签名
- `api.py` — API 客户端（任务提交、查询、轮询）

**仅依赖 Python 标准库，无需 pip install 任何包。**

## 并发限制（重要）

当前平台方限制**最大并发为 1**。这意味着：

- **绝对不要并行调用多次脚本**。如果需要生成多张图片或多个视频，必须使用 `--batch` 批量模式，它会严格串行执行每个任务。
- 不要同时运行 `image.py` 和 `video.py`，同一时刻只能有一个脚本在运行。
- 批量模式内部会自动在任务之间等待间隔，避免请求过于密集。

---

## 图像生成（即梦4.0）

### 单任务模式

```bash
python <skill-path>/scripts/image.py "提示词" [选项]
```

### 批量模式

```bash
python <skill-path>/scripts/image.py --batch tasks.json [--output DIR] [--json]
```

### 参数

| 参数 | 说明 |
|------|------|
| `prompt` (位置参数) | 生成图像的提示词，中英文均可，建议不超过 800 字 |
| `--image-urls URL ...` | 输入图片 URL 列表（0-10 张，用于图生图/编辑） |
| `--image-files PATH ...` | 输入图片本地文件路径列表（0-10 张） |
| `--size SIZE` | 生成图片面积，默认 4194304（即 2K）。范围 [1024×1024, 4096×4096] |
| `--width W` | 生成图片宽度（需同时指定 `--height`） |
| `--height H` | 生成图片高度（需同时指定 `--width`） |
| `--scale FLOAT` | 文本影响程度 0~1，默认 0.5（越大文本影响越强） |
| `--force-single` | 强制只生成 1 张图片 |
| `--batch FILE` | 批量任务 JSON 文件（与 prompt 互斥，严格串行执行） |
| `--output DIR` | 输出目录，默认当前目录 |
| `--json` | 将结果以 JSON 格式输出到 stdout |

### 批量任务 JSON 格式

```json
[
  {"prompt": "一只橘猫坐在窗台上"},
  {"prompt": "把背景换成海边", "image_urls": ["https://example.com/photo.jpg"]},
  {"prompt": "未来城市", "width": 4096, "height": 4096}
]
```

每个任务对象支持的字段：`prompt`(必填)、`image_urls`、`image_files`、`size`、`width`、`height`、`scale`、`force_single`。

### 示例

```bash
# 单张图片
python scripts/image.py "一只橘猫坐在窗台上，阳光照射，暖色调"

# 带参考图的编辑
python scripts/image.py "把背景换成海边" --image-urls "https://example.com/photo.jpg"

# 指定 4K 分辨率
python scripts/image.py "未来城市全景" --width 4096 --height 4096 --output ./4k_output

# 批量生成（严格串行）
python scripts/image.py --batch tasks.json --output ./batch_output --json
```

### 重要提示

- **建议生成 2K 以上的图片**，过小分辨率容易出现人脸效果不佳、文字异常等问题
- 输入图片建议控制在 6 张以内，过多会降低参考效果
- 输出图片 URL 有效期为 **24 小时**
- 更多参数细节参阅 `references/image-reference.md`

---

## 视频生成（即梦3.0）

### 支持的模式

| 模式 | req_key | 说明 |
|------|---------|------|
| `t2v` | jimeng_t2v_v30 | 文生视频 |
| `i2v-first` | jimeng_i2v_first_v30 | 图生视频 - 首帧 |
| `i2v-first-tail` | jimeng_i2v_first_tail_v30 | 图生视频 - 首尾帧 |
| `i2v-camera` | jimeng_i2v_recamera_v30 | 图生视频 - 运镜 |

### 单任务模式

```bash
python <skill-path>/scripts/video.py <模式> "提示词" [选项]
```

### 批量模式

```bash
python <skill-path>/scripts/video.py --batch tasks.json [--output DIR] [--json]
```

### 通用视频参数

| 参数 | 说明 |
|------|------|
| `mode` (位置参数) | 模式：t2v / i2v-first / i2v-first-tail / i2v-camera |
| `prompt` (位置参数) | 提示词，建议 400 字以内 |
| `--frames 121\|241` | 帧数：121(5秒) 或 241(10秒)，默认 121 |
| `--seed INT` | 随机种子，-1 为随机 |
| `--batch FILE` | 批量任务 JSON 文件（与 mode/prompt 互斥，严格串行执行） |
| `--output PATH` | 输出路径（单任务为文件路径，批量为目录） |
| `--json` | JSON 输出 |

### 模式专属参数

**t2v（文生视频）**：
- `--aspect-ratio`：宽高比（16:9 / 4:3 / 1:1 / 3:4 / 9:16 / 21:9），默认 16:9

**i2v-first（首帧）**：
- `--image-url URL` 或 `--image-file PATH`：1 张图片

**i2v-first-tail（首尾帧）**：
- `--first-image-url` + `--last-image-url`（或对应的 `--*-file` 版本）：2 张图片
- 尾帧图片需与首帧比例相同

**i2v-camera（运镜）**：
- `--image-url URL` 或 `--image-file PATH`：1 张图片
- `--template-id ID`：运镜模板（必选）
- `--camera-strength weak|medium|strong`：运镜强度（必选）

运镜模板 ID：

| ID | 效果 |
|----|------|
| hitchcock_dolly_in | 希区柯克推进 |
| hitchcock_dolly_out | 希区柯克拉远 |
| robo_arm | 机械臂 |
| dynamic_orbit | 动感环绕 |
| central_orbit | 中心环绕 |
| crane_push | 起重机 |
| quick_pull_back | 超级拉远 |
| counterclockwise_swivel | 逆时针回旋 |
| clockwise_swivel | 顺时针回旋 |
| handheld | 手持运镜 |
| rapid_push_pull | 快速推拉 |

### 批量任务 JSON 格式

```json
[
  {"mode": "t2v", "prompt": "千军万马", "aspect_ratio": "16:9"},
  {"mode": "i2v-first", "prompt": "人物转身", "image_url": "https://xxx/photo.jpg"},
  {"mode": "i2v-camera", "prompt": "城市夜景", "image_url": "https://xxx/city.jpg", "template_id": "dynamic_orbit", "camera_strength": "strong"}
]
```

每个任务对象必须包含 `mode` 和 `prompt`，其他字段根据模式选填：`image_url`、`image_file`、`first_image_url`、`last_image_url`、`first_image_file`、`last_image_file`、`template_id`、`camera_strength`、`aspect_ratio`、`frames`、`seed`。

### 示例

```bash
# 文生视频（10秒）
python scripts/video.py t2v "千军万马奔腾，黄沙漫天" --frames 241 --aspect-ratio 16:9

# 图生视频 - 首帧
python scripts/video.py i2v-first "人物缓缓转身微笑" --image-url "https://xxx/photo.jpg"

# 图生视频 - 首尾帧
python scripts/video.py i2v-first-tail "魔法变身特效" \
  --first-image-url "https://xxx/start.jpg" \
  --last-image-url "https://xxx/end.jpg"

# 图生视频 - 运镜
python scripts/video.py i2v-camera "城市夜景" \
  --image-file ./city.jpg \
  --template-id dynamic_orbit \
  --camera-strength strong

# 批量生成（严格串行）
python scripts/video.py --batch tasks.json --output ./batch_output --json
```

### 重要提示

- 视频生成需要较长时间（通常 1-5 分钟），脚本会自动轮询直到完成
- 输出视频 URL 有效期为 **1 小时**
- 图片输入要求：JPEG/PNG，最大 4.7MB，最大分辨率 4096×4096，最短边不低于 320
- 更多参数细节参阅 `references/video-reference.md`

---

## 详细 API 参考

如需了解完整的 API 参数、错误码、返回格式等细节，请阅读：

- **图像生成 API**：`references/image-reference.md`
- **视频生成 API**：`references/video-reference.md`
