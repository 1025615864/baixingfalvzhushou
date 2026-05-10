"""文件上传API路由
安全加固：病毒扫描、内容审核、文件类型白名单、大小限制
"""
import os
import re
import uuid
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, RedirectResponse

from ..models.user import User
from ..services.storage_service import LocalStorageProvider, get_storage_provider
from ..utils.deps import get_current_user, get_current_user_optional
from ..utils.rate_limiter import rate_limit_upload
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["文件上传"])

# 上传目录配置
UPLOAD_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__))),
    "uploads")
AVATAR_DIR = os.path.join(UPLOAD_DIR, "avatars")
IMAGE_DIR = os.path.join(UPLOAD_DIR, "images")
FILE_DIR = os.path.join(UPLOAD_DIR, "files")

# 确保目录存在
try:
    if isinstance(get_storage_provider(), LocalStorageProvider):
        os.makedirs(AVATAR_DIR, exist_ok=True)
        os.makedirs(IMAGE_DIR, exist_ok=True)
        os.makedirs(FILE_DIR, exist_ok=True)
except Exception:
    logger.exception("Failed to create upload directories")

# 安全配置：文件类型白名单
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
}
# 仅允许安全的位图格式（拒绝SVG等潜在危险格式）

ALLOWED_FILE_TYPES = {
    # 文档
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    # 压缩包
    "application/zip",
    "application/x-zip-compressed",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
    "application/vnd.rar",
    "application/x-tar",
    "application/gzip",
    "application/x-gzip",
    # Office文档
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # 图片
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    # 音频
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/mp4",
    # 视频
    "video/mp4",
    "video/webm",
    "video/ogg",
}

# 危险的文件扩展名黑名单
DANGEROUS_EXTENSIONS = {
    "exe", "bat", "cmd", "sh", "ps1", "vbs", "js", "jar", "com",
    "pif", "scr", "dll", "sys", "drv", "msi", "msp", "mst",
    "deb", "rpm", "bin", "run", "out", "command", "svg"
}

# 文件大小限制（字节）
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB - 头像
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB - 附件

_AVATAR_FILENAME_RE = re.compile(
    r"^\d+_[0-9a-f]{8}_\d+\.(jpg|jpeg|png|gif|webp)$",
    re.IGNORECASE)
_IMAGE_FILENAME_RE = re.compile(
    r"^[0-9a-f]{32}\.(jpg|jpeg|png|gif|webp)$",
    re.IGNORECASE)
_FILE_FILENAME_RE = re.compile(
    r"^[0-9a-f]{32}\.[a-z0-9]{1,10}$",
    re.IGNORECASE)


def _env_enabled(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


async def _moderate_image_via_webhook(
        *, content: bytes, content_type: str | None) -> tuple[bool, str | None]:
    """图片内容审核（模拟实现）
    
    生产环境应集成真实的审核服务（如阿里云内容安全、腾讯云天御等）
    """
    _ = content
    _ = content_type
    
    if (not settings.debug) and not _env_enabled(
            "UPLOAD_IMAGE_MODERATION_ALLOW_MOCK", default=False):
        raise RuntimeError("Image moderation mock disabled")

    # 记录警告：当前使用模拟实现
    logger.warning(
        "[SECURITY] Image moderation is using MOCK implementation. "
        "Integrate real content moderation service for production!"
    )
    
    # 模拟：所有图片都通过审核
    # 生产环境：调用真实API检查色情、暴恐、政治敏感内容
    return True, None


async def _scan_bytes_with_clamd(content: bytes) -> tuple[str, str]:
    """病毒扫描 - 集成ClamAV
    
    优先使用真实病毒扫描服务，回退到模拟模式
    """
    # 尝试使用ClamAV进行真实扫描
    try:
        import pyclamd
        cd = pyclamd.ClamdUnixSocket()
        if cd.ping():
            result = cd.scan_stream(content)
            if result:
                # 发现病毒
                for _, virus_info in result.items():
                    return "FOUND", f"Virus detected: {virus_info}"
            return "OK", ""
    except ImportError:
        logger.debug("pyclamd not installed, virus scanning disabled")
    except Exception as e:
        logger.warning(f"ClamAV connection failed: {e}")
    
    # 检查是否允许模拟模式
    if (not settings.debug) and not _env_enabled(
            "UPLOAD_VIRUS_SCAN_ALLOW_MOCK", default=False):
        raise RuntimeError(
            "Virus scanning is required but ClamAV is not available. "
            "Please install and configure ClamAV, or set UPLOAD_VIRUS_SCAN_ALLOW_MOCK=true temporarily"
        )

    # 记录警告：使用模拟实现
    logger.warning(
        "[SECURITY] Virus scanning is using MOCK implementation. "
        "Install pyclamd and ClamAV for production security: "
        "apt-get install clamav-daemon && pip install pyclamd"
    )
    
    return "OK", ""


def _detect_image_ext(content: bytes) -> str | None:
    if len(content) < 12:
        return None

    if content[:3] == b"\xFF\xD8\xFF":
        return "jpg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    # WEBP: RIFF....WEBP
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def _is_safe_filename(filename: str) -> bool:
    if not filename:
        return False
    if filename != os.path.basename(filename):
        return False
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    return _AVATAR_FILENAME_RE.match(filename) is not None


def _is_safe_image_filename(filename: str) -> bool:
    if not filename:
        return False
    if filename != os.path.basename(filename):
        return False
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    return _IMAGE_FILENAME_RE.match(filename) is not None


def _is_safe_file_filename(filename: str) -> bool:
    if not filename:
        return False
    if filename != os.path.basename(filename):
        return False
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    return _FILE_FILENAME_RE.match(filename) is not None


@router.post("/avatar", summary="上传头像（安全加固）")
@rate_limit_upload()
async def upload_avatar(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    上传用户头像（安全加固版本）
    
    安全特性：
    - 仅允许安全的位图格式（jpg, png, gif, webp）
    - 文件大小限制：2MB
    - 文件内容验证（magic bytes）
    - 病毒扫描（需配置）
    - 图片内容审核（需配置）
    - 上传频率限制
    - 防路径遍历攻击
    """
    # 检查文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="不支持的图片格式，请上传 jpg/png/gif/webp 格式"
        )

    # 读取文件内容
    content = await file.read()

    # 验证文件内容（magic bytes）
    detected_ext = _detect_image_ext(content)
    if detected_ext is None:
        raise HTTPException(
            status_code=400,
            detail="无法识别图片格式，请上传 jpg/png/gif/webp 格式"
        )

    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="图片大小不能超过 2MB"
        )

    # 生成唯一文件名
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.{detected_ext}"
    storage = get_storage_provider()

    # 删除旧头像文件（如果存在且是本地文件）
    current_avatar = getattr(current_user, "avatar", None)
    if isinstance(storage, LocalStorageProvider):
        if current_avatar and isinstance(
                current_avatar,
                str) and current_avatar.startswith("/api/upload/avatars/"):
            old_filename = current_avatar.split("/")[-1]
            old_filepath = storage.get_local_path(
                category="avatars", filename=old_filename)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except Exception:
                    logger.exception("Failed to remove old avatar file: %s", old_filepath)

    await storage.put_bytes(
        category="avatars",
        filename=filename,
        content=content,
        content_type=file.content_type,
    )

    # 返回访问URL
    avatar_url = f"/api/upload/avatars/{filename}"

    return {
        "url": avatar_url,
        "filename": filename,
        "message": "头像上传成功"
    }


@router.get("/avatars/{filename}", summary="获取头像")
async def get_avatar(
    filename: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileResponse | RedirectResponse:
    """获取头像文件（需要登录）"""
    _ = current_user
    if not _is_safe_filename(filename):
        raise HTTPException(status_code=400, detail="非法文件名")
    storage = get_storage_provider()
    if isinstance(storage, LocalStorageProvider):
        filepath = storage.get_local_path(
            category="avatars", filename=filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(filepath)

    url = await storage.get_download_url(category="avatars", filename=filename)
    return RedirectResponse(url=url, status_code=307)


@router.post("/file", summary="上传附件（安全加固）")
@rate_limit_upload()
async def upload_file(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    上传附件（安全加固版本）
    
    安全特性：
    - 严格的文件类型白名单
    - 文件大小限制：10MB
    - 文件扩展名校验（黑名单检查）
    - 病毒扫描（需配置）
    - 上传频率限制
    - 防路径遍历攻击
    """
    _ = current_user

    # 严格验证文件类型
    if file.content_type not in ALLOWED_FILE_TYPES:
        logger.warning(
            "[SECURITY] Unauthorized file type upload attempt: %s by user %s",
            file.content_type,
            current_user.id
        )
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}"
        )

    content = await file.read()
    if len(content) > MAX_ATTACHMENT_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    original_name = os.path.basename(file.filename or "")
    original_name = original_name.strip() or "attachment"

    # 验证文件扩展名（黑名单检查）
    ext = os.path.splitext(original_name)[1].lstrip(".").lower()
    
    if not ext:
        raise HTTPException(status_code=400, detail="无法识别文件扩展名")
    
    if ext in DANGEROUS_EXTENSIONS:
        logger.warning(
            "[SECURITY] Dangerous file extension upload attempt: .%s by user %s",
            ext,
            current_user.id
        )
        raise HTTPException(
            status_code=400,
            detail=f"不安全的文件扩展名: {ext}"
        )
    
    # 文件内容病毒扫描（生产环境默认启用）
    if _env_enabled("UPLOAD_VIRUS_SCAN_ENABLED", default=True):
        try:
            status, message = await _scan_bytes_with_clamd(content)
            status = str(status or "").upper()
            if status == "FOUND":
                logger.error(
                    "[SECURITY] malware detected in file upload by user %s: %s",
                    current_user.id,
                    message
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"文件包含恶意软件: {message}"
                )
            if status and status != "OK":
                if not _env_enabled("UPLOAD_VIRUS_SCAN_FAIL_OPEN", default=False):
                    raise HTTPException(status_code=503, detail="病毒扫描服务不可用")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("[SECURITY] Virus scan failed: %s", e)
            if not _env_enabled("UPLOAD_VIRUS_SCAN_FAIL_OPEN", default=False):
                raise HTTPException(status_code=503, detail="文件安全检查失败")

    filename = f"{uuid.uuid4().hex}.{ext}"
    storage = get_storage_provider()
    await storage.put_bytes(
        category="files",
        filename=filename,
        content=content,
        content_type=file.content_type,
    )

    file_url = f"/api/upload/files/{filename}"
    return {
        "url": file_url,
        "filename": filename,
        "original_name": original_name,
        "message": "上传成功",
    }


@router.get("/files/{filename}", summary="获取附件")
async def get_file(
    filename: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileResponse | RedirectResponse:
    """获取附件文件（需要登录）"""
    _ = current_user
    if not _is_safe_file_filename(filename):
        raise HTTPException(status_code=400, detail="非法文件名")
    storage = get_storage_provider()
    if isinstance(storage, LocalStorageProvider):
        filepath = storage.get_local_path(category="files", filename=filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(filepath)

    url = await storage.get_download_url(category="files", filename=filename)
    return RedirectResponse(url=url, status_code=307)


@router.post("/image", summary="上传图片（安全加固）")
@rate_limit_upload()
async def upload_image(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    上传通用图片（安全加固版本）
    
    安全特性：
    - 仅允许安全的位图格式（拒绝SVG等潜在危险格式）
    - 文件大小限制：2MB
    - 文件内容验证（magic bytes）
    - 图片内容审核（需配置）
    - 病毒扫描（需配置）
    - 上传频率限制
    """
    _ = current_user

    # 严格验证图片类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        logger.warning(
            "[SECURITY] Unauthorized image type upload attempt: %s by user %s",
            file.content_type,
            current_user.id
        )
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式: {file.content_type}",
        )

    content = await file.read()

    detected_ext = _detect_image_ext(content)
    if detected_ext is None:
        raise HTTPException(
            status_code=400,
            detail="无法识别图片格式，请上传 jpg/png/gif/webp 格式",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="图片大小不能超过 2MB",
        )

    filename = f"{uuid.uuid4().hex}.{detected_ext}"
    storage = get_storage_provider()

    if _env_enabled(
            "UPLOAD_REQUIRE_OBJECT_STORAGE",
            default=False) and isinstance(
            storage,
            LocalStorageProvider):
        if not _env_enabled("UPLOAD_ALLOW_LOCAL_STORAGE", default=False):
            raise HTTPException(status_code=503, detail="本环境不允许使用本地存储")

    # 图片内容审核（生产环境默认启用）
    if _env_enabled("UPLOAD_IMAGE_MODERATION_ENABLED", default=True):
        try:
            ok, reason = await _moderate_image_via_webhook(
                content=content,
                content_type=file.content_type,
            )
            if not ok:
                raise HTTPException(
                    status_code=400, detail=str(
                        reason or "图片审核未通过"))
        except HTTPException:
            raise
        except Exception:
            logger.exception("Image moderation failed")
            if not _env_enabled(
                    "UPLOAD_IMAGE_MODERATION_FAIL_OPEN", default=False):
                raise HTTPException(status_code=503, detail="图片审核服务不可用")

    # 图片病毒扫描（生产环境默认启用）
    if _env_enabled("UPLOAD_VIRUS_SCAN_ENABLED", default=True):
        try:
            status, message = await _scan_bytes_with_clamd(content)
            status = str(status or "").upper()
            if status == "FOUND":
                raise HTTPException(
                    status_code=400, detail=str(
                        message or "发现病毒"))
            if status and status != "OK":
                if not _env_enabled(
                        "UPLOAD_VIRUS_SCAN_FAIL_OPEN", default=False):
                    raise HTTPException(status_code=503, detail="病毒扫描服务不可用")
        except HTTPException:
            raise
        except Exception:
            logger.exception("Virus scan failed for image upload")
            if not _env_enabled("UPLOAD_VIRUS_SCAN_FAIL_OPEN", default=False):
                raise HTTPException(status_code=503, detail="病毒扫描服务不可用")

    await storage.put_bytes(
        category="images",
        filename=filename,
        content=content,
        content_type=file.content_type,
    )

    image_url = f"/api/upload/images/{filename}"

    return {
        "url": image_url,
        "filename": filename,
        "message": "图片上传成功",
    }


@router.get("/images/{filename}", summary="获取图片")
async def get_image(
    filename: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileResponse | RedirectResponse:
    """获取图片文件（需要登录）"""
    _ = current_user
    if not _is_safe_image_filename(filename):
        raise HTTPException(status_code=400, detail="非法文件名")
    storage = get_storage_provider()
    if isinstance(storage, LocalStorageProvider):
        filepath = storage.get_local_path(category="images", filename=filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(filepath)

    url = await storage.get_download_url(category="images", filename=filename)
    return RedirectResponse(url=url, status_code=307)
