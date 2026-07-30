#!/usr/bin/env python3
"""火山引擎即梦 3.0 视频生成 CLI 工具。

单任务模式：
  python video.py t2v "提示词" [选项]
  python video.py i2v-first "提示词" --image-url URL [选项]
  python video.py i2v-first-tail "提示词" --first-image-url URL --last-image-url URL [选项]
  python video.py i2v-camera "提示词" --image-url URL --template-id ID --camera-strength LEVEL [选项]

批量模式（严格串行，并发=1）：
  python video.py --batch tasks.json [--output DIR] [--json]
"""

import argparse
import base64
import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api import poll_task, submit_task
from auth import load_credentials

# 批量模式下，两个任务之间的等待间隔（秒）
BATCH_TASK_INTERVAL = 2

CAMERA_TEMPLATES = [
    "hitchcock_dolly_in",
    "hitchcock_dolly_out",
    "robo_arm",
    "dynamic_orbit",
    "central_orbit",
    "crane_push",
    "quick_pull_back",
    "counterclockwise_swivel",
    "clockwise_swivel",
    "handheld",
    "rapid_push_pull",
]

CAMERA_STRENGTHS = {"weak", "medium", "strong"}
FRAME_COUNTS = {121, 241}
ASPECT_RATIOS = {"16:9", "4:3", "1:1", "3:4", "9:16", "21:9"}

MODE_REQ_KEY = {
    "t2v": "jimeng_t2v_v30",
    "i2v-first": "jimeng_i2v_first_v30",
    "i2v-first-tail": "jimeng_i2v_first_tail_v30",
    "i2v-camera": "jimeng_i2v_recamera_v30",
}


def download_file(url: str, output_path: str) -> None:
    """从 URL 下载文件到本地。"""
    req = urllib.request.Request(url)
    ctx = ssl.create_default_context()
    with (
        urllib.request.urlopen(req, timeout=300, context=ctx) as resp,
        open(output_path, "wb") as f,
    ):
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            f.write(chunk)


def read_image_as_base64(file_path: str) -> str:
    """读取本地图片文件并返回 base64 编码字符串。"""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"图片文件不存在: {file_path}")
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _resolve_images_from_task(task: dict, mode: str) -> dict:
    """从任务字典解析图片输入，返回 body 字段片段。"""
    if mode in ("i2v-first", "i2v-camera"):
        if task.get("image_url"):
            return {"image_urls": [task["image_url"]]}
        if task.get("image_file"):
            return {"binary_data_base64": [read_image_as_base64(task["image_file"])]}
        raise ValueError(f"模式 {mode} 需要 image_url 或 image_file")

    if mode == "i2v-first-tail":
        if task.get("first_image_url") and task.get("last_image_url"):
            return {"image_urls": [task["first_image_url"], task["last_image_url"]]}
        if task.get("first_image_file") and task.get("last_image_file"):
            return {
                "binary_data_base64": [
                    read_image_as_base64(task["first_image_file"]),
                    read_image_as_base64(task["last_image_file"]),
                ]
            }
        raise ValueError("模式 i2v-first-tail 需要 first_image_url/last_image_url 或对应的 file 字段")

    return {}


def _resolve_images_from_args(args: argparse.Namespace, mode: str) -> dict:
    """从 CLI 参数解析图片输入，返回 body 字段片段。"""
    if mode in ("i2v-first", "i2v-camera"):
        if args.image_url:
            return {"image_urls": [args.image_url]}
        if args.image_file:
            return {"binary_data_base64": [read_image_as_base64(args.image_file)]}
        print(f"错误: 模式 {mode} 需要通过 --image-url 或 --image-file 提供图片", file=sys.stderr)
        sys.exit(1)

    if mode == "i2v-first-tail":
        if args.first_image_url and args.last_image_url:
            return {"image_urls": [args.first_image_url, args.last_image_url]}
        if args.first_image_file and args.last_image_file:
            return {
                "binary_data_base64": [
                    read_image_as_base64(args.first_image_file),
                    read_image_as_base64(args.last_image_file),
                ]
            }
        print(
            "错误: 首尾帧模式需要 --first-image-url/--last-image-url "
            "或 --first-image-file/--last-image-file",
            file=sys.stderr,
        )
        sys.exit(1)

    return {}


def build_body(task: dict) -> dict:
    """从任务字典构建 API 请求体。"""
    mode = task["mode"]
    req_key = MODE_REQ_KEY.get(mode)
    if not req_key:
        raise ValueError(f"无效的视频模式: {mode}")

    body = {
        "req_key": req_key,
        "prompt": task["prompt"],
    }

    # 图片输入
    body.update(_resolve_images_from_task(task, mode))

    # 运镜参数
    if mode == "i2v-camera":
        template_id = task.get("template_id")
        if not template_id:
            raise ValueError("运镜模式需要 template_id")
        if template_id not in CAMERA_TEMPLATES:
            raise ValueError(f"无效的运镜模板 '{template_id}'")
        body["template_id"] = template_id

        strength = task.get("camera_strength")
        if not strength:
            raise ValueError("运镜模式需要 camera_strength")
        if strength not in CAMERA_STRENGTHS:
            raise ValueError(f"无效的运镜强度 '{strength}'")
        body["camera_strength"] = strength

    # 通用可选参数
    aspect_ratio = task.get("aspect_ratio")
    if mode == "t2v" and aspect_ratio:
        if aspect_ratio not in ASPECT_RATIOS:
            raise ValueError(f"无效的视频宽高比 '{aspect_ratio}'")
        body["aspect_ratio"] = aspect_ratio
    if task.get("seed") is not None:
        body["seed"] = task["seed"]
    frames = task.get("frames")
    if frames is not None:
        if frames not in FRAME_COUNTS:
            raise ValueError(f"无效的视频帧数 '{frames}'")
        body["frames"] = frames

    return body


def generate_one(task: dict, output_dir: Path, ak: str, sk: str, label: str = "") -> dict:
    """执行单个视频生成任务（提交 → 轮询 → 下载）。

    Returns:
        {"task_id": str, "file": str, "video_url": str} 或 {"task_id": str, "error": str}
    """
    prefix = f"[{label}] " if label else ""
    mode = task["mode"]

    try:
        body = build_body(task)
    except ValueError as e:
        print(f"{prefix}参数错误: {e}", file=sys.stderr)
        return {"task_id": None, "error": str(e)}

    req_key = body["req_key"]

    print(f"{prefix}正在提交视频生成任务 (模式: {mode})...", file=sys.stderr)
    try:
        task_id = submit_task(body, ak, sk)
    except RuntimeError as e:
        print(f"{prefix}提交失败: {e}", file=sys.stderr)
        return {"task_id": None, "error": str(e)}

    print(f"{prefix}任务已提交, task_id: {task_id}", file=sys.stderr)

    print(f"{prefix}正在等待生成结果 (视频生成可能需要较长时间)...", file=sys.stderr)
    try:
        result = poll_task(req_key, task_id, ak, sk, interval=10, timeout=600)
    except RuntimeError as e:
        print(f"{prefix}轮询失败: {e}", file=sys.stderr)
        return {"task_id": task_id, "error": str(e)}

    data = result.get("data", {})
    video_url = data.get("video_url")

    if not video_url:
        print(f"{prefix}警告: 未获取到视频 URL", file=sys.stderr)
        return {"task_id": task_id, "error": "未获取到视频 URL", "data": data}

    # 保存视频
    output_path = str(output_dir / f"video_{task_id}.mp4")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"{prefix}正在下载视频: {output_path}", file=sys.stderr)
    download_file(video_url, output_path)
    print(f"{prefix}视频生成完成: {output_path}", file=sys.stderr)

    return {"task_id": task_id, "file": output_path, "video_url": video_url}


# ──────────────────────────────────────────────
# 单任务模式
# ──────────────────────────────────────────────


def run_single(args: argparse.Namespace) -> None:
    """单任务模式入口。"""
    ak, sk = load_credentials()
    mode = args.mode

    body = {
        "req_key": MODE_REQ_KEY[mode],
        "prompt": args.prompt,
    }

    # 图片输入
    body.update(_resolve_images_from_args(args, mode))

    # 运镜参数
    if mode == "i2v-camera":
        if not args.template_id:
            print("错误: 运镜模式需要通过 --template-id 指定运镜模板", file=sys.stderr)
            sys.exit(1)
        if args.template_id not in CAMERA_TEMPLATES:
            print(
                f"错误: 无效的运镜模板 '{args.template_id}'，可选值:\n  "
                + "\n  ".join(CAMERA_TEMPLATES),
                file=sys.stderr,
            )
            sys.exit(1)
        body["template_id"] = args.template_id

        if not args.camera_strength:
            print("错误: 运镜模式需要通过 --camera-strength 指定强度", file=sys.stderr)
            sys.exit(1)
        body["camera_strength"] = args.camera_strength

    # 通用可选参数
    if mode == "t2v" and args.aspect_ratio:
        body["aspect_ratio"] = args.aspect_ratio
    if args.seed is not None:
        body["seed"] = args.seed
    if args.frames:
        body["frames"] = args.frames

    req_key = body["req_key"]

    print(f"正在提交视频生成任务 (模式: {mode})...", file=sys.stderr)
    task_id = submit_task(body, ak, sk)
    print(f"任务已提交, task_id: {task_id}", file=sys.stderr)

    print("正在等待生成结果 (视频生成可能需要较长时间)...", file=sys.stderr)
    result = poll_task(req_key, task_id, ak, sk, interval=10, timeout=600)
    data = result.get("data", {})

    video_url = data.get("video_url")
    if not video_url:
        print("警告: 未获取到视频 URL", file=sys.stderr)
        print(f"返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}", file=sys.stderr)
        return

    output_path = args.output or f"video_{task_id}.mp4"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"正在下载视频: {output_path}", file=sys.stderr)
    download_file(video_url, output_path)
    print(f"\n视频生成完成: {output_path}", file=sys.stderr)

    if args.json:
        output = {"task_id": task_id, "file": output_path, "video_url": video_url}
        print(json.dumps(output, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────────
# 批量模式（严格串行，并发=1）
# ──────────────────────────────────────────────


def run_batch(args: argparse.Namespace) -> None:
    """批量模式入口。逐个处理任务，绝不并行。"""
    ak, sk = load_credentials()

    batch_path = Path(args.batch)
    if not batch_path.exists():
        raise RuntimeError(f"批量任务文件不存在: {args.batch}")

    tasks = json.loads(batch_path.read_text(encoding="utf-8"))
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise RuntimeError("批量任务文件格式错误: 需要一个非空的 JSON 数组")

    total = len(tasks)
    output_dir = Path(args.output) if args.output else Path(".")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"批量模式: 共 {total} 个任务，严格串行执行 (并发=1)", file=sys.stderr)
    print(f"输出目录: {output_dir}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    results = []
    success_count = 0
    fail_count = 0

    for i, task in enumerate(tasks):
        if not isinstance(task, dict) or "prompt" not in task or "mode" not in task:
            print(f"[{i + 1}/{total}] 跳过: 缺少 prompt 或 mode 字段", file=sys.stderr)
            results.append({"index": i, "error": "缺少 prompt 或 mode 字段"})
            fail_count += 1
            continue

        result = generate_one(task, output_dir, ak, sk, label=f"{i + 1}/{total}")
        result["index"] = i
        results.append(result)

        if result.get("error"):
            fail_count += 1
        else:
            success_count += 1

        # 非最后一个任务，等待一小段时间再继续
        if i < total - 1:
            time.sleep(BATCH_TASK_INTERVAL)

    # 汇总
    print("=" * 50, file=sys.stderr)
    print(f"批量完成: 成功 {success_count}, 失败 {fail_count}, 共 {total}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="火山引擎即梦 3.0 视频生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 单任务位置参数（批量模式下可选）
    parser.add_argument(
        "mode",
        nargs="?",
        choices=list(MODE_REQ_KEY),
        help="视频生成模式 (单任务模式)",
    )
    parser.add_argument("prompt", nargs="?", help="生成视频的提示词 (单任务模式)")

    # 单图输入（首帧 / 运镜）
    parser.add_argument("--image-url", metavar="URL", help="输入图片 URL (首帧/运镜模式)")
    parser.add_argument("--image-file", metavar="PATH", help="输入图片本地文件 (首帧/运镜模式)")

    # 双图输入（首尾帧）
    parser.add_argument("--first-image-url", metavar="URL", help="首帧图片 URL (首尾帧模式)")
    parser.add_argument("--last-image-url", metavar="URL", help="尾帧图片 URL (首尾帧模式)")
    parser.add_argument("--first-image-file", metavar="PATH", help="首帧图片本地文件 (首尾帧模式)")
    parser.add_argument("--last-image-file", metavar="PATH", help="尾帧图片本地文件 (首尾帧模式)")

    # 运镜参数
    parser.add_argument("--template-id", metavar="ID", help="运镜模板 ID (运镜模式)")
    parser.add_argument(
        "--camera-strength",
        choices=sorted(CAMERA_STRENGTHS),
        help="运镜强度 (运镜模式)",
    )

    # 通用选项
    parser.add_argument(
        "--frames",
        type=int,
        choices=sorted(FRAME_COUNTS),
        help="帧数: 121(5s) 或 241(10s)",
    )
    parser.add_argument(
        "--aspect-ratio",
        choices=sorted(ASPECT_RATIOS),
        help="视频宽高比 (仅文生视频)",
    )
    parser.add_argument("--seed", type=int, help="随机种子 (-1 为随机)")

    # 批量模式
    parser.add_argument("--batch", metavar="FILE", help="批量任务 JSON 文件路径 (严格串行执行)")

    # 通用输出
    parser.add_argument("--output", "-o", metavar="PATH", help="输出路径 (单任务为文件路径, 批量为目录)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果到 stdout")

    args = parser.parse_args()

    # 互斥校验
    if args.batch and (args.mode or args.prompt):
        parser.error("--batch 不能与 mode/prompt 同时指定")
    if not args.batch and (not args.mode or not args.prompt):
        parser.error("请指定 mode 和 prompt（单任务模式）或 --batch（批量模式）")

    try:
        if args.batch:
            run_batch(args)
        else:
            run_single(args)
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        sys.exit(130)
    except RuntimeError as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
