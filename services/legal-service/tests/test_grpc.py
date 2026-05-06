"""gRPC 服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date


class TestGRPCServer:
    """gRPC 服务单元测试"""

    @pytest.mark.asyncio
    async def test_grpc_servicer_get_lawyer(self):
        """测试 gRPC 获取律师"""
        from app.grpc_server import create_grpc_servicer

        mock_session_factory = MagicMock()

        async def mock_session():
            session = AsyncMock()
            mock_result = MagicMock()
            mock_lawyer = MagicMock()
            mock_lawyer.id = 1
            mock_lawyer.name = "张律师"
            mock_lawyer.title = "合伙人"
            mock_lawyer.specialties = ["刑事辩护"]
            mock_lawyer.rating = 4.8
            mock_lawyer.consultation_count = 100
            mock_lawyer.lawfirm_id = 1
            mock_result.scalar_one_or_none.return_value = mock_lawyer
            session.execute = AsyncMock(return_value=mock_result)
            return session

        mock_session_factory.return_value.__aenter__ = AsyncMock(side_effect=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock()

        servicer = create_grpc_servicer(mock_session_factory)

        mock_request = MagicMock()
        mock_request.lawyer_id = "1"

        mock_context = MagicMock()
        mock_context.set_code = MagicMock()
        mock_context.set_details = MagicMock()

        response = await servicer.GetLawyer(mock_request, mock_context)

        assert response is not None
        assert response.name == "张律师"

    @pytest.mark.asyncio
    async def test_grpc_servicer_get_lawyer_not_found(self):
        """测试 gRPC 获取不存在的律师"""
        from app.grpc_server import create_grpc_servicer

        mock_session_factory = MagicMock()

        async def mock_session():
            session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            session.execute = AsyncMock(return_value=mock_result)
            return session

        mock_session_factory.return_value.__aenter__ = AsyncMock(side_effect=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock()

        servicer = create_grpc_servicer(mock_session_factory)

        mock_request = MagicMock()
        mock_request.lawyer_id = "999"

        mock_context = MagicMock()
        mock_context.set_code = MagicMock()
        mock_context.set_details = MagicMock()

        response = await servicer.GetLawyer(mock_request, mock_context)

        mock_context.set_code.assert_called_once()
        mock_context.set_details.assert_called_once()

    @pytest.mark.asyncio
    async def test_grpc_servicer_get_schedule(self):
        """测试 gRPC 获取律师排班"""
        from app.grpc_server import create_grpc_servicer

        mock_session_factory = MagicMock()

        async def mock_session():
            session = AsyncMock()
            mock_result = MagicMock()
            mock_schedule = MagicMock()
            mock_schedule.id = 1
            mock_schedule.date = datetime.now()
            mock_schedule.start_time = "09:00"
            mock_schedule.end_time = "10:00"
            mock_schedule.is_available = True
            mock_result.scalars.return_value.all.return_value = [mock_schedule]
            session.execute = AsyncMock(return_value=mock_result)
            return session

        mock_session_factory.return_value.__aenter__ = AsyncMock(side_effect=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock()

        servicer = create_grpc_servicer(mock_session_factory)

        mock_request = MagicMock()
        mock_request.lawyer_id = "1"
        mock_request.date = ""

        mock_context = MagicMock()
        mock_context.set_code = MagicMock()
        mock_context.set_details = MagicMock()

        response = await servicer.GetLawyerSchedule(mock_request, mock_context)

        assert response is not None
        assert response.lawyer_id == "1"


class TestGRPCServerSync:
    """gRPC 同步包装器测试"""

    def test_sync_legal_service_servicer_get_lawyer(self):
        """测试同步包装器获取律师"""
        from app.grpc_server import SyncLegalServiceServicer

        mock_session_factory = MagicMock()

        async def mock_get_lawyer(request, context):
            from services.common.proto import user_pb2
            return user_pb2.Lawyer(
                lawyer_id="1",
                name="张律师",
            )

        mock_servicer = MagicMock()
        mock_servicer.GetLawyer = mock_get_lawyer

        servicer = SyncLegalServiceServicer.__new__(SyncLegalServiceServicer)
        servicer._session_factory = mock_session_factory
        servicer._servicer = mock_servicer
        servicer._loop = None

        mock_request = MagicMock()
        mock_context = MagicMock()

        result = servicer.GetLawyer(mock_request, mock_context)

        assert result.name == "张律师"
