"""火山引擎即梦 CV API 客户端。

提供任务提交、查询、轮询等核心功能。
所有接口均为异步任务模式：先提交任务获取 task_id，再轮询获取结果。
"""

import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from auth import load_credentials, sign_request

HOST = "visual.volcengineapi.com"
BASE_URL = f"https://{HOST}"


def _build_url(action: str) -> tuple[str, dict[str, str]]:
    """构建请求 URL 和 query 参数。"""
    query_params = {"Action": action, "Version": "2022-08-31"}
    qs = "&".join(f"{k}={v}" for k, v in sorted(query_params.items()))
    url = f"{BASE_URL}/?{qs}"
    return url, query_params


def _make_request(action: str, body_dict: dict, ak: str, sk: str) -> dict:
    """发送已签名的请求到火山引擎 CV API。

    Args:
        action: API Action，如 CVSync2AsyncSubmitTask
        body_dict: 请求体字典
        ak: Access Key
        sk: Secret Key

    Returns:
        API 响应字典

    Raises:
        RuntimeError: 请求失败时抛出
    """
    url, query_params = _build_url(action)
    body_bytes = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")

    headers = {
        "host": HOST,
        "content-type": "application/json",
    }

    headers = sign_request("POST", "/", query_params, headers, body_bytes, ak, sk)

    req = urllib.request.Request(url, data=body_bytes, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)

    # 创建不验证 SSL 的上下文（部分环境可能缺少根证书）
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            return json.loads(error_body)
        except json.JSONDecodeError:
            raise RuntimeError(f"HTTP {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络请求失败: {e.reason}")


def submit_task(body_dict: dict, ak: str | None = None, sk: str | None = None) -> str:
    """提交异步生成任务。

    Args:
        body_dict: 请求体，必须包含 req_key 和业务参数
        ak: Access Key（可选，不传则自动加载）
        sk: Secret Key（可选，不传则自动加载）

    Returns:
        task_id 字符串

    Raises:
        RuntimeError: 提交失败时抛出
    """
    if not ak or not sk:
        ak, sk = load_credentials()

    result = _make_request("CVSync2AsyncSubmitTask", body_dict, ak, sk)

    code = result.get("code")
    if code != 10000:
        raise RuntimeError(
            f"提交任务失败: code={code}, "
            f"message={result.get('message')}, "
            f"request_id={result.get('request_id')}"
        )

    task_id = result.get("data", {}).get("task_id")
    if not task_id:
        raise RuntimeError(f"提交任务返回异常: 未获取到 task_id, response={result}")

    return task_id


def query_task(
    req_key: str,
    task_id: str,
    ak: str | None = None,
    sk: str | None = None,
    req_json: str | None = None,
) -> dict:
    """查询任务结果（单次查询）。

    Args:
        req_key: 服务标识
        task_id: 任务 ID
        ak: Access Key
        sk: Secret Key
        req_json: 可选的 JSON 配置字符串（水印等）

    Returns:
        API 完整响应字典
    """
    if not ak or not sk:
        ak, sk = load_credentials()

    body: dict[str, Any] = {"req_key": req_key, "task_id": task_id}
    if req_json:
        body["req_json"] = req_json

    return _make_request("CVSync2AsyncGetResult", body, ak, sk)


def poll_task(
    req_key: str,
    task_id: str,
    ak: str | None = None,
    sk: str | None = None,
    interval: int = 5,
    timeout: int = 600,
    req_json: str | None = None,
) -> dict:
    """轮询任务直到完成。

    Args:
        req_key: 服务标识
        task_id: 任务 ID
        ak: Access Key
        sk: Secret Key
        interval: 轮询间隔（秒），默认 5
        timeout: 最大等待时间（秒），默认 600
        req_json: 可选的 JSON 配置字符串

    Returns:
        成功时返回完整响应字典

    Raises:
        RuntimeError: 任务失败、超时或未找到时抛出
    """
    if not ak or not sk:
        ak, sk = load_credentials()

    start = time.time()
    last_status = None

    while True:
        result = query_task(req_key, task_id, ak, sk, req_json)
        code = result.get("code")
        data = result.get("data") or {}
        status = data.get("status")

        # 成功完成
        if code == 10000 and status == "done":
            return result

        # 任务失败（code=10000 但 status=done 以外的终态，或 code!=10000 且 status=done）
        if status in ("not_found", "expired"):
            raise RuntimeError(
                f"任务{status}: task_id={task_id}, "
                f"request_id={result.get('request_id')}"
            )

        if code != 10000 and status == "done":
            raise RuntimeError(
                f"任务完成但出错: code={code}, "
                f"message={result.get('message')}, "
                f"request_id={result.get('request_id')}"
            )

        # 超时检查
        elapsed = time.time() - start
        if elapsed > timeout:
            raise RuntimeError(
                f"轮询超时({timeout}s): task_id={task_id}, 最后状态={status}"
            )

        # 进度输出
        if status != last_status:
            _print_status(status, elapsed)
            last_status = status
        else:
            _print_status(status, elapsed)

        time.sleep(interval)


def _print_status(status: str | None, elapsed: float) -> None:
    """打印轮询进度。"""
    status_map = {
        "in_queue": "排队中",
        "generating": "生成中",
    }
    display = status_map.get(status or "", status or "unknown")
    print(f"  状态: {display}, 已等待 {elapsed:.0f}s ...", file=sys.stderr)
