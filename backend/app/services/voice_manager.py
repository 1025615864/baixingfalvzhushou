"""智能语音模块管理服务"""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .sherpa_asr_service import sherpa_is_ready, sherpa_transcribe

logger = logging.getLogger(__name__)

# OpenAI 异常类型（延迟导入，但需要在 except 块中使用）
APIError = None
RateLimitError = None

try:
    from openai import APIError, RateLimitError
except ImportError:
    pass


class VoiceProvider(str, Enum):
    """语音转写提供商"""
    AUTO = "auto"
    OPENAI = "openai"
    SHERPA = "sherpa"


class VoiceProviderStatus(str, Enum):
    """语音提供商状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


@dataclass
class VoiceProviderHealth:
    """语音提供商健康状态"""
    provider: VoiceProvider
    status: VoiceProviderStatus
    message: str
    last_check: float
    latency_ms: float | None = None


class VoiceManager:
    """智能语音模块管理器"""

    def __init__(self):
        self._health_checks: dict[VoiceProvider, VoiceProviderHealth] = {}
        self._check_interval: float = 300.0  # 5分钟检查一次
        self._check_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """启动健康检查任务"""
        if self._check_task is None or self._check_task.done():
            self._check_task = asyncio.create_task(self._health_check_loop())
            logger.info("语音管理器健康检查任务已启动")

    async def stop(self) -> None:
        """停止健康检查任务"""
        if self._check_task and not self._check_task.done():
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            logger.info("语音管理器健康检查任务已停止")

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while True:
            try:
                await self._check_all_providers()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as health_err:
                logger.exception(f"Voice provider health check loop error: {health_err}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试

    async def _check_all_providers(self) -> None:
        """检查所有语音提供商的健康状态"""
        from ..config import get_settings

        settings = get_settings()

        # 检查Sherpa
        sherpa_health = await self._check_sherpa(settings)
        self._health_checks[VoiceProvider.SHERPA] = sherpa_health

        # 检查OpenAI
        openai_health = await self._check_openai(settings)
        self._health_checks[VoiceProvider.OPENAI] = openai_health

        logger.info(
            "语音提供商健康检查完成: Sherpa=%s, OpenAI=%s",
            sherpa_health.status.value,
            openai_health.status.value,
        )

    async def _check_sherpa(self, settings: Any) -> VoiceProviderHealth:
        """检查Sherpa ASR服务状态"""
        import time

        start_time = time.time()
        try:
            is_ready = sherpa_is_ready(settings)
            latency_ms = (time.time() - start_time) * 1000

            if is_ready:
                return VoiceProviderHealth(
                    provider=VoiceProvider.SHERPA,
                    status=VoiceProviderStatus.AVAILABLE,
                    message="Sherpa ASR服务正常",
                    last_check=time.time(),
                    latency_ms=latency_ms,
                )
            else:
                return VoiceProviderHealth(
                    provider=VoiceProvider.SHERPA,
                    status=VoiceProviderStatus.UNAVAILABLE,
                    message="Sherpa ASR服务未配置或不可用",
                    last_check=time.time(),
                    latency_ms=None,
                )
        except FileNotFoundError as e:
            logger.error(f"Sherpa ASR配置文件不存在: {e}")
            return VoiceProviderHealth(
                provider=VoiceProvider.SHERPA,
                status=VoiceProviderStatus.UNAVAILABLE,
                message=f"配置错误: {str(e)}",
                last_check=time.time(),
                latency_ms=None,
            )
        except PermissionError as e:
            logger.error(f"Sherpa ASR文件权限错误: {e}")
            return VoiceProviderHealth(
                provider=VoiceProvider.SHERPA,
                status=VoiceProviderStatus.UNAVAILABLE,
                message=f"权限错误: {str(e)}",
                last_check=time.time(),
                latency_ms=None,
            )
        except Exception as e:
            logger.exception("检查Sherpa ASR服务失败")
            return VoiceProviderHealth(
                provider=VoiceProvider.SHERPA,
                status=VoiceProviderStatus.UNAVAILABLE,
                message=f"检查失败: {str(e)}",
                last_check=time.time(),
                latency_ms=None,
            )

    async def _check_openai(self, settings: Any) -> VoiceProviderHealth:
        """检查OpenAI语音服务状态"""
        import time

        start_time = time.time()
        try:
            # 检查API密钥是否存在
            api_key = str(
                getattr(
                    settings,
                    "openai_api_key",
                    "") or "").strip()
            if not api_key:
                return VoiceProviderHealth(
                    provider=VoiceProvider.OPENAI,
                    status=VoiceProviderStatus.UNAVAILABLE,
                    message="OpenAI API密钥未配置",
                    last_check=time.time(),
                    latency_ms=None,
                )

            # 这里可以添加实际的API测试调用
            # 为了简化，我们只检查配置
            latency_ms = (time.time() - start_time) * 1000

            return VoiceProviderHealth(
                provider=VoiceProvider.OPENAI,
                status=VoiceProviderStatus.AVAILABLE,
                message="OpenAI语音服务配置正常",
                last_check=time.time(),
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.exception("检查OpenAI语音服务失败")
            return VoiceProviderHealth(
                provider=VoiceProvider.OPENAI,
                status=VoiceProviderStatus.UNAVAILABLE,
                message=f"检查失败: {str(e)}",
                last_check=time.time(),
                latency_ms=None,
            )

    def get_provider_health(
            self, provider: VoiceProvider) -> VoiceProviderHealth | None:
        """获取指定提供商的健康状态"""
        return self._health_checks.get(provider)

    def get_all_health(self) -> dict[VoiceProvider, VoiceProviderHealth]:
        """获取所有提供商的健康状态"""
        return self._health_checks.copy()

    def get_available_providers(self) -> list[VoiceProvider]:
        """获取可用的语音提供商列表"""
        return [
            provider
            for provider, health in self._health_checks.items()
            if health.status == VoiceProviderStatus.AVAILABLE
        ]

    def get_best_provider(
            self,
            preferred: VoiceProvider = VoiceProvider.AUTO) -> VoiceProvider:
        """获取最佳可用的语音提供商"""
        available = self.get_available_providers()

        if not available:
            # 如果没有可用的提供商，返回首选
            return preferred if preferred != VoiceProvider.AUTO else VoiceProvider.OPENAI

        if preferred != VoiceProvider.AUTO and preferred in available:
            return preferred

        # 优先返回Sherpa（本地服务更快）
        if VoiceProvider.SHERPA in available:
            return VoiceProvider.SHERPA

        return available[0]

    async def transcribe_with_fallback(
        self,
        *,
        content: bytes,
        filename: str,
        settings: Any,
        db: AsyncSession,
        segment_index: int | None = None,
        is_final: bool | None = None,
    ) -> tuple[str, VoiceProvider]:
        """使用自动回退机制进行语音转写"""
        from .voice_config_service import get_effective_voice_settings

        # 获取有效的语音设置
        effective_settings, _, _ = await get_effective_voice_settings(db, settings)

        # 确定首选提供商
        provider_str = str(
            getattr(
                effective_settings,
                "voice_transcribe_provider",
                "auto") or "").strip().lower()
        preferred = VoiceProvider(provider_str) if provider_str in {
            p.value for p in VoiceProvider} else VoiceProvider.AUTO

        # 获取最佳提供商
        best_provider = self.get_best_provider(preferred)

        # 尝试使用最佳提供商
        if best_provider == VoiceProvider.SHERPA:
            try:
                text, _, _ = await sherpa_transcribe(
                    content=content,
                    filename=filename,
                    settings=effective_settings,
                    segment_index=segment_index,
                    is_final=is_final,
                )
                return text, VoiceProvider.SHERPA
            except Exception as e:
                logger.warning("Sherpa转写失败，尝试使用OpenAI: %s", str(e))
                # 回退到OpenAI
                if VoiceProvider.OPENAI in self.get_available_providers():
                    text = await self._transcribe_with_openai(
                        content=content,
                        filename=filename,
                        settings=effective_settings,
                    )
                    return text, VoiceProvider.OPENAI
                raise

        # 使用OpenAI
        text = await self._transcribe_with_openai(
            content=content,
            filename=filename,
            settings=effective_settings,
        )
        return text, VoiceProvider.OPENAI

    async def _transcribe_with_openai(
        self,
        content: bytes,
        filename: str,
        settings: Any,
    ) -> str:
        """使用OpenAI进行语音转写"""
        try:
            from openai import AsyncOpenAI, APIError, RateLimitError

            api_key = str(
                getattr(
                    settings,
                    "openai_api_key",
                    "") or "").strip()
            base_url = str(
                getattr(
                    settings,
                    "openai_base_url",
                    "") or "").strip()

            if not api_key:
                raise ValueError("OpenAI API密钥未配置")

            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url if base_url else None)

            # 创建临时文件
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or ".wav") as f:
                f.write(content)
                temp_path = f.name

            try:
                with open(temp_path, "rb") as audio_file:
                    response = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="zh",
                    )
                return response.text
            finally:
                try:
                    os.unlink(temp_path)
                except OSError as unlink_err:
                    logger.warning(f"Failed to delete temp file {temp_path}: {unlink_err}")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"OpenAI connection error: {e}")
            raise RuntimeError("OpenAI语音转写失败: 网络连接错误，请检查网络后重试")
        except Exception as e:
            # 检查是否是 OpenAI 特定的异常
            if RateLimitError and isinstance(e, RateLimitError):
                logger.error(f"OpenAI API rate limit exceeded: {e}")
                raise RuntimeError("OpenAI语音转写失败: API请求过于频繁，请稍后重试")
            if APIError and isinstance(e, APIError):
                logger.error(f"OpenAI API error: {e}")
                raise RuntimeError(f"OpenAI语音转写失败: {getattr(e, 'message', str(e))}")
            logger.exception("OpenAI语音转写失败")
            raise RuntimeError(f"OpenAI语音转写失败: {str(e)}")

    async def validate_voice_config(self, db: AsyncSession) -> dict[str, Any]:
        """验证语音配置"""
        from .voice_config_service import load_voice_config_overrides
        from ..config import get_settings

        settings = get_settings()
        issues: list[str] = []
        warnings: list[str] = []

        # 检查配置键是否存在
        overrides = await load_voice_config_overrides(db)

        # 检查Sherpa配置
        sherpa_enabled = overrides.get("SHERPA_ASR_ENABLED")
        if sherpa_enabled and str(sherpa_enabled).strip().lower() in {
                "1", "true", "yes"}:
            mode = overrides.get("SHERPA_ASR_MODE", "off").strip().lower()

            if mode == "local":
                tokens = overrides.get("SHERPA_ONNX_TOKENS", "").strip()
                wenet = overrides.get(
                    "SHERPA_ONNX_WENET_CTC_MODEL", "").strip()
                whisper_enc = overrides.get(
                    "SHERPA_ONNX_WHISPER_ENCODER", "").strip()
                whisper_dec = overrides.get(
                    "SHERPA_ONNX_WHISPER_DECODER", "").strip()

                if not tokens:
                    issues.append("Sherpa本地模式需要配置SHERPA_ONNX_TOKENS")
                elif not (wenet or (whisper_enc and whisper_dec)):
                    issues.append("Sherpa本地模式需要配置Wenet或Whisper模型文件")
                else:
                    # 检查文件是否存在
                    import os
                    if wenet and not os.path.exists(wenet):
                        issues.append(f"Wenet模型文件不存在: {wenet}")
                    if whisper_enc and not os.path.exists(whisper_enc):
                        issues.append(f"Whisper编码器文件不存在: {whisper_enc}")
                    if whisper_dec and not os.path.exists(whisper_dec):
                        issues.append(f"Whisper解码器文件不存在: {whisper_dec}")

            elif mode == "remote":
                remote_url = overrides.get("SHERPA_ASR_REMOTE_URL", "").strip()
                if not remote_url:
                    issues.append("Sherpa远程模式需要配置SHERPA_ASR_REMOTE_URL")

        # 检查OpenAI配置
        openai_key = overrides.get("OPENAI_API_KEY") or str(
            getattr(settings, "openai_api_key", "") or "").strip()
        if not openai_key:
            warnings.append("未配置OpenAI API密钥，将无法使用OpenAI语音转写")

        # 检查ffmpeg
        try:
            import subprocess
            cp = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=3,
            )
            if cp.returncode != 0:
                warnings.append("ffmpeg未正确安装，音频格式转换可能失败")
        except Exception:
            warnings.append("ffmpeg未安装，音频格式转换将失败")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }


# 全局语音管理器实例
_voice_manager: VoiceManager | None = None


def get_voice_manager() -> VoiceManager:
    """获取全局语音管理器实例"""
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceManager()
    return _voice_manager
