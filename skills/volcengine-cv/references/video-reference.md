# 即梦视频生成 API 参考文档

## 1. 接口介绍

即梦视频3.0是即梦同源的视频生成能力，专业级视频生成引擎，释放无限创意。准确遵循复杂指令，视觉表达流畅一致，支持最高1080P高清渲染，更可驾驭多元艺术风格，在视频生成质量出色的基础上，是**生成效果与速度兼备的高性价比之选**。

### 支持的视频生成模式

1. **文生视频**（Text-to-Video）：输入文本提示词，生成视频
2. **图生视频 - 首帧**（Image-to-Video - First Frame）：输入首帧图片和提示词，生成视频
3. **图生视频 - 首尾帧**（Image-to-Video - First & Last Frame）：输入首尾帧和提示词，精准控制视频内容
4. **图生视频 - 运镜**（Image-to-Video - Camera Movement）：输入图片和运镜参数，生成具有专业运镜效果的视频

---

## 2. 核心能力

### 2.1 指令准确遵循

- 指令遵循能力增强，准确解析用户输入的复杂指令
- 涵盖人物表情、动作、衣着控制，以及多主体交互动作设计等场景
- 能够理解细微的动作描述和表情变化需求

### 2.2 专业级运镜控制

支持多样化运镜选择，包括：
- 希区柯克拉运镜
- 动感环绕运镜
- 机械臂运镜
- 中心环绕
- 起重机运镜
- 超级拉远
- 逆时针回旋
- 顺时针回旋
- 手持运镜
- 快速推拉

### 2.3 首尾帧掌控叙事节奏

- 仅需输入首帧和尾帧画面，即可精准控制视频生成内容
- 实现起点与终点画面间的自然流畅衔接
- 精准控制视频的叙事节奏和视觉变化

### 2.4 画面风格和主体统一

- 生成内容的画面风格与核心主体保持高度统一
- 确保视觉表达的连贯性
- IP 形象保持稳定，无跳变、偏色等情况

### 2.5 画质分辨率提升

- 场景渲染效果优异
- 能细腻呈现自然光影与写实场景细节
- 支持生成最高 1080P 的高清视频（720P/1080P 可选）

---

## 3. 应用场景

| 场景 | 说明 |
|------|------|
| **电商广告** | 产品展示、运动展示等商业广告视频 |
| **影视创作** | 电影片段、剧情演绎等创意视频 |
| **动态壁纸** | 实时变化的艺术化视频背景 |
| **角色生成** | AI 虚拟人物、角色动画等 |

---

## 4. 提示词建议

### 提示词结构

**基础结构：**主体 / 背景 / 镜头 + 动作

**多个镜头连贯叙事：**镜头1 + 主体 + 动作1 + 镜头2 + 主体 + 动作2 ...

**多个连续动作：**
- 时序性的多个连续动作：主体1 + 运动1 + 运动2
- 多主体的不同动作：主体1 + 运动1 + 主体2 + 运动2 ...

### 运镜词典

**镜头移动：**
- 切换：镜头切换
- 平移：镜头向上/下/左/右移动
- 推轨：镜头拉近/拉远
- 环形跟踪：镜头环绕、航拍、广角、镜头360度旋转
- 跟随：镜头跟随
- 固定：固定镜头、镜头静止不动
- 聚焦：镜头特写
- 手持：镜头晃动 / 抖动、手持拍摄、动态不稳定

**程度副词：**可以通过程度副词突出主体动作频率与强度，或者特征，如"快速"、"大幅度"、"高频率"、"剧烈"、"缓缓"

### 示例提示词

```
一位背对着观众站立的女性，手中的折扇收起，侧过身，画面变亮，镜头缓缓推至人物近景，女人抬起一只手扶住屏幕，缓缓地走出了镜头

一个木质老年木偶坐在街头长凳上缓慢弹奏吉他，他看向手中的吉他，动作僵硬但有节奏感，手指抬起时带有轻微卡顿感。街头安静，偶尔有风吹动他破旧的衣角，整段氛围温暖而略显孤寂

年轻的女孩大笑起来，然后突然睁大眼睛露出震惊的表情，接着严肃的皱眉，嘴周又突然想起什么开始变得痛苦，最后抱住头痛哭
```

---

## 5. API 接入指南

### 5.1 请求信息（通用）

| 项目 | 内容 |
|------|------|
| **接口地址** | https://visual.volcengineapi.com |
| **请求方式** | POST |
| **Content-Type** | application/json |
| **Region** | cn-north-1（固定值） |
| **Service** | cv（固定值） |

### 5.2 API 端点信息

所有视频生成请求均为异步，通过以下两个接口完成：
- **提交任务**：CVSync2AsyncSubmitTask
- **查询结果**：CVSync2AsyncGetResult

---

## 6. 文生视频（Text-to-Video）

### 6.1 提交任务

#### Query 参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| Action | string | 是 | 接口名，取值：**CVSync2AsyncSubmitTask** |
| Version | string | 是 | 版本号，取值：**2022-08-31** |

#### Body 参数

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| req_key | string | 是 | 服务标识，取固定值：**jimeng_t2v_v30** |
| prompt | string | 是 | 用于生成视频的提示词，中英文均可输入。建议 400 字以内，不超过 800 字 |
| seed | int | 否 | 随机种子，默认 -1（随机）。相同种子且参数一致会生成相同视频，默认值：-1 |
| frames | int | 否 | 生成的总帧数（帧数 = 24 × n + 1）。可选取值：[121, 241]，对应 5s、10s，默认值：121 |
| aspect_ratio | string | 否 | 生成视频的长宽比。可选取值：["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"]，默认值："16:9" |

#### 请求示例

```json
{
    "req_key": "jimeng_t2v_v30",
    "prompt": "千军万马",
    "seed": -1,
    "frames": 121,
    "aspect_ratio": "16:9"
}
```

#### 返回参数

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务 ID，用于查询结果 |

#### 返回示例

```json
{
    "code": 10000,
    "data": {
        "task_id": "7392616336519610409"
    },
    "message": "Success",
    "request_id": "20240720103939AF0029465CF6A74E51EC",
    "time_elapsed": "104.852309ms"
}
```

---

## 7. 图生视频 - 首帧（Image-to-Video - First Frame）

### 7.1 提交任务

#### Body 参数

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| req_key | string | 是 | 服务标识，取固定值：**jimeng_i2v_first_v30** |
| binary_data_base64 | array of string | 是（二选一） | 图片文件 base64 编码，仅支持输入 1 张图片，仅支持 JPEG、PNG 格式<br/>**注意：**<br/>• 图片文件大小：最大 4.7MB<br/>• 图片分辨率：最大 4096×4096，最短边不低于 320<br/>• 图片长边与短边比例在 3 以内 |
| image_urls | array of string | 是（二选一） | 图片文件 URL，仅支持输入 1 张图片<br/>**注意：**<br/>• 图片长边与短边比例在 3 以内 |
| prompt | string | 是 | 用于生成视频的提示词，建议 400 字以内，不超过 800 字 |
| seed | int | 否 | 随机种子，默认值：-1 |
| frames | int | 否 | 生成的总帧数（帧数 = 24 × n + 1）。可选取值：[121, 241]，默认值：121 |

#### 请求示例

```json
{
    "req_key": "jimeng_i2v_first_v30",
    "image_urls": [
        "https://xxx"
    ],
    "prompt": "千军万马",
    "seed": -1,
    "frames": 121
}
```

---

## 8. 图生视频 - 首尾帧（Image-to-Video - First & Last Frame）

### 8.1 提交任务

#### Body 参数

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| req_key | string | 是 | 服务标识，取固定值：**jimeng_i2v_first_tail_v30** |
| binary_data_base64 | array of string | 是（二选一） | 图片文件 base64 编码，请输入 2 张图片（首帧和尾帧），仅支持 JPEG、PNG 格式<br/>**注意：**<br/>• 图片文件大小：最大 4.7MB<br/>• 图片分辨率：最大 4096×4096，最短边不低于 320<br/>• 图片长边与短边比例在 3 以内<br/>• 尾帧图片需与首帧图片比例相同 |
| image_urls | array of string | 是（二选一） | 图片文件 URL，请输入 2 张图片（首帧和尾帧）<br/>**注意：**<br/>• 图片长边与短边比例在 3 以内<br/>• 尾帧图片需与首帧图片比例相同 |
| prompt | string | 是 | 用于生成视频的提示词，建议 400 字以内，不超过 800 字 |
| seed | int | 否 | 随机种子，默认值：-1 |
| frames | int | 否 | 生成的总帧数。可选取值：[121, 241]，默认值：121 |

#### 请求示例

```json
{
    "req_key": "jimeng_i2v_first_tail_v30",
    "image_urls": [
        "https://xxx",
        "https://xxx"
    ],
    "prompt": "主体拿出银色雪花魔法棒，对着自己头顶挥舞出现很多银光细闪，变身冰雪女王，蓝色的公主裙和银色王冠闪闪发光",
    "seed": -1,
    "frames": 121
}
```

---

## 9. 图生视频 - 运镜（Image-to-Video - Camera Movement）

### 9.1 支持的运镜模板

| 模板 ID | 运镜类型 |
|----------|---------|
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

### 9.2 提交任务

#### Body 参数

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| req_key | string | 是 | 服务标识，取固定值：**jimeng_i2v_recamera_v30** |
| binary_data_base64 | array of string | 是（二选一） | 图片文件 base64 编码，仅支持输入 1 张图片，仅支持 JPEG、PNG 格式<br/>**注意：**<br/>• 图片文件大小：最大 4.7MB<br/>• 图片分辨率：最大 4096×4096，最短边不低于 320<br/>• 图片长边与短边比例在 3 以内 |
| image_urls | array of string | 是（二选一） | 图片文件 URL，仅支持输入 1 张图片<br/>**注意：**<br/>• 图片长边与短边比例在 3 以内 |
| prompt | string | 是 | 用于生成视频的提示词，建议 400 字以内，不超过 800 字 |
| template_id | string | 是 | 运镜模板 ID，见上表 |
| camera_strength | string | 是 | 运镜强度。可选取值：["weak", "medium", "strong"] |
| seed | int | 否 | 随机种子，默认值：-1 |
| frames | int | 否 | 生成的总帧数。可选取值：[121, 241]，默认值：121 |

#### 请求示例

```json
{
    "req_key": "jimeng_i2v_recamera_v30",
    "image_urls": [
        "https://xxx"
    ],
    "prompt": "千军万马",
    "template_id": "hitchcock_dolly_out",
    "camera_strength": "medium",
    "seed": -1,
    "frames": 121
}
```

---

## 10. 查询任务

### 10.1 请求

#### Query 参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| Action | string | 是 | 接口名，固定值：**CVSync2AsyncGetResult** |
| Version | string | 是 | 版本号，固定值：**2022-08-31** |

#### Body 参数

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| req_key | string | 是 | 服务标识，对应相应的生成方式 req_key |
| task_id | string | 是 | 任务 ID，由提交任务接口返回 |
| req_json | JSON string | 否 | json 序列化后的配置字符串，支持隐式标识配置 |

#### 请求示例

```json
{
    "req_key": "jimeng_t2v_v30",
    "task_id": "7491596536074305586",
    "req_json": "{\"aigc_meta\": {\"content_producer\": \"001191440300192203821610000\", \"producer_id\": \"producer_id_test123\", \"content_propagator\": \"001191440300192203821610000\", \"propagate_id\": \"propagate_id_test123\"}}"
}
```

### 10.2 返回参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 任务执行状态：in_queue / generating / done / not_found / expired |
| video_url | string | 生成的视频 URL（有效期为 1 小时） |
| aigc_meta_tagged | bool | 隐式标识是否打标成功 |

#### 返回示例

```json
{
    "code": 10000,
    "data": {
        "aigc_meta_tagged": true,
        "status": "done",
        "video_url": "https://xxxx"
    },
    "message": "Success",
    "request_id": "20250805144938F6E5264E9D24EB0C4E0A",
    "time_elapsed": "508.312154ms"
}
```

---

## 11. 错误码

### 通用错误码

请参考 [公共返回字段及错误码](https://www.volcengine.com/docs/6444/69728)

### 业务错误码

| HTTP Code | 错误码 | 错误消息 | 描述 | 是否需要重试 |
|-----------|--------|--------|------|-----------|
| 200 | 10000 | 无 | 请求成功 | 不需要 |
| 400 | 50411 | Pre Img Risk Not Pass | 输入图片前审核未通过 | 不需要 |
| 400 | 50511 | Post Img Risk Not Pass | 输出图片后审核未通过 | 可重试 |
| 400 | 50412 | Text Risk Not Pass | 输入文本前审核未通过 | 不需要 |
| 400 | 50512 | Post Text Risk Not Pass | 输出文本后审核未通过 | 不需要 |
| 400 | 50413 | Post Text Risk Not Pass | 输入文本含敏感词、版权词等审核不通过 | 不需要 |
| 400 | 50516 | Post Video Risk Not Pass | 输出视频后审核未通过 | 可重试 |
| 400 | 50517 | Post Audio Risk Not Pass | 输出音频后审核未通过 | 可重试 |
| 400 | 50518 | Pre Img Risk Not Pass: Copyright | 输入版权图前审核未通过 | 不需要 |
| 400 | 50519 | Post Img Risk Not Pass: Copyright | 输出版权图后审核未通过 | 可重试 |
| 400 | 50520 | Risk Internal Error | 审核服务异常 | 不需要 |
| 400 | 50521 | Antidirt Internal Error | 版权词服务异常 | 不需要 |
| 400 | 50522 | Image Copyright Internal Error | 版权图服务异常 | 不需要 |
| 429 | 50429 | Request Has Reached API Limit, Please Try Later | QPS 超限 | 可重试 |
| 429 | 50430 | Request Has Reached API Concurrent Limit, Please Try Later | 并发超限 | 可重试 |
| 500 | 50500 | Internal Error | 内部错误 | 可重试 |
| 500 | 50501 | Internal RPC Error | 内部算法错误 | 可重试 |

---

## 12. 常见问题

### 数据链接相关

**Q: 返回的视频链接有效期是多久？**

A: 视频链接有效期为 1 小时，超过 1 小时后需要重新生成。

**Q: 返回的资源地址的域名有哪些？**

A: 资源地址的域名包括：
- v3-vvecloud.yangyi08.com
- v6-vvecloud.yangyi08.com
- v9-vvecloud.yangyi08.com
- v26-vvecloud.yangyi08.com

### 任务相关

**Q: 提交任务接口返回的 taskID 有效期是多久？**

A: taskID 的有效期为 24 小时，超过 24 小时后无法获取结果。

**Q: 任务超过 12 小时会怎样？**

A: 超过 12 小时后，无法获取视频融合异步接口中的任务结果。

**Q: 如何取消异步调用接口？**

A: 调用 CVCancelTask 接口，注意当前不支持取消 generating 状态的任务。

请求示例：
```json
{
    "req_key": "接口服务req_key",
    "task_id": "<任务task_id>"
}
```

### 控制 QPS 和并发

**Q: 如何稳定持续地保持指定 QPS 去请求接口？**

A: 使用令牌桶（Token Bucket）算法控制 QPS。建议 QPS 比接口限制略小，因为网络延迟可能导致实际请求大于目标 QPS。

**Q: 如何稳定持续地保持指定并发去请求接口？**

A: 使用线程池 + Future 实现并发管理。根据公式：所需线程数 = QPS × 平均响应时间(秒) × 冗余率 计算所需线程数。

### 获取凭证

**Q: 如何获取调用 API 必需的 AK/SK？**

A:
- 已上架控制台的 API，可直接在[火山引擎控制台](https://console.volcengine.com/iam/keymanage/)获取
- 未上架控制台的能力需要联系商务申请授权

---

## 13. SDK 接入

请参考 [SDK 使用说明](https://www.volcengine.com/docs/6444/1340578)

## 14. HTTP 请求示例

请参考 [HTTP 请求示例](https://www.volcengine.com/docs/6444/1390583)

---

## 相关链接

- [服务开通](https://console.volcengine.com/ai/ability/detail/10)
- [火山引擎官网](https://www.volcengine.com/)
