"""火山引擎 API 认证模块 - V4 HMAC-SHA256 签名。

凭证加载优先级（与火山引擎官方 SDK 一致）：
1. 环境变量 VOLC_ACCESSKEY / VOLC_SECRETKEY
2. ~/.volc/config 文件（JSON 格式）
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


def load_credentials() -> tuple[str, str]:
    """加载火山引擎 AK/SK 凭证。

    Returns:
        (access_key, secret_key) 元组

    Raises:
        RuntimeError: 未找到有效凭证时抛出
    """
    # 1. 环境变量（优先）
    ak = os.environ.get("VOLC_ACCESSKEY")
    sk = os.environ.get("VOLC_SECRETKEY")

    if ak and sk:
        return ak, sk

    # 2. ~/.volc/config（JSON 格式）
    config_path = Path.home() / ".volc" / "config"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            ak = data.get("ak") or data.get("access_key")
            sk = data.get("sk") or data.get("secret_key")
            if ak and sk:
                return ak, sk
        except (json.JSONDecodeError, IOError):
            pass

    raise RuntimeError(
        "未找到火山引擎凭证。请通过以下方式之一配置：\n"
        "  1. 设置环境变量 VOLC_ACCESSKEY 和 VOLC_SECRETKEY\n"
        '  2. 在 ~/.volc/config 中写入 JSON: {"ak": "...", "sk": "..."}'
    )


# ──────────────────────────────────────────────
# V4 HMAC-SHA256 签名
# ──────────────────────────────────────────────

REGION = "cn-north-1"
SERVICE = "cv"


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sign_request(
    method: str,
    path: str,
    query_params: dict[str, str],
    headers: dict[str, str],
    body_bytes: bytes,
    ak: str,
    sk: str,
    region: str = REGION,
    service: str = SERVICE,
) -> dict[str, str]:
    """对请求进行 V4 HMAC-SHA256 签名。

    Returns:
        包含签名的请求头字典
    """
    now = datetime.now(timezone.utc)
    date_stamp = now.strftime("%Y%m%d")
    x_date = now.strftime("%Y%m%dT%H%M%SZ")

    # 设置必要的请求头
    headers = dict(headers)
    headers["x-date"] = x_date

    # 计算 payload hash
    payload_hash = _sha256_hex(body_bytes)
    headers["x-content-sha256"] = payload_hash

    # 需要签名的请求头（小写排序）
    signed_header_keys = sorted(
        k.lower()
        for k in headers
        if k.lower() in ("host", "x-date", "content-type", "x-content-sha256")
    )
    signed_headers_str = ";".join(signed_header_keys)

    # 构建 canonical headers
    header_map = {k.lower(): v.strip() for k, v in headers.items()}
    canonical_headers = "".join(f"{k}:{header_map[k]}\n" for k in signed_header_keys)

    # 构建 canonical query string（按参数名排序）
    if query_params:
        sorted_params = sorted(query_params.items())
        canonical_qs = "&".join(
            f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted_params
        )
    else:
        canonical_qs = ""

    # 构建 canonical request
    canonical_request = "\n".join([
        method,
        path,
        canonical_qs,
        canonical_headers,
        signed_headers_str,
        payload_hash,
    ])

    # 构建 credential scope
    credential_scope = f"{date_stamp}/{region}/{service}/request"

    # 构建 string to sign
    hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = "\n".join([
        "HMAC-SHA256",
        x_date,
        credential_scope,
        hashed_canonical,
    ])

    # 派生签名密钥
    k_date = _hmac_sha256(sk.encode("utf-8"), date_stamp)
    k_region = _hmac_sha256(k_date, region)
    k_service = _hmac_sha256(k_region, service)
    k_signing = _hmac_sha256(k_service, "request")

    # 计算签名
    signature = hmac.new(
        k_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # 构建 Authorization 头
    headers["authorization"] = (
        f"HMAC-SHA256 Credential={ak}/{credential_scope}, "
        f"SignedHeaders={signed_headers_str}, "
        f"Signature={signature}"
    )

    return headers
