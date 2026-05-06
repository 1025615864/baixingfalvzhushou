"""律师缓存模块"""
import json
import logging
from typing import Optional, List
from datetime import timedelta

logger = logging.getLogger(__name__)


class LawyerCache:
    LAWYER_DETAIL_KEY = "lawyer:detail:{lawyer_id}"
    LAWYER_LIST_KEY = "lawyer:list:{specialty}:{page}"
    LAWYER_SEARCH_KEY = "lawyer:search:{hash}"
    LAWYER_SCHEDULE_KEY = "lawyer:schedule:{lawyer_id}:{date}"

    LAWYER_DETAIL_TTL = timedelta(minutes=15)
    LAWYER_LIST_TTL = timedelta(minutes=5)
    LAWYER_SEARCH_TTL = timedelta(minutes=5)
    LAWYER_SCHEDULE_TTL = timedelta(minutes=5)

    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_lawyer_detail(self, lawyer_id: int) -> Optional[dict]:
        if not self.redis:
            return None
        try:
            key = self.LAWYER_DETAIL_KEY.format(lawyer_id=lawyer_id)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to get lawyer detail from cache: {e}")
        return None

    async def set_lawyer_detail(self, lawyer_id: int, lawyer_data: dict) -> bool:
        if not self.redis:
            return False
        try:
            key = self.LAWYER_DETAIL_KEY.format(lawyer_id=lawyer_id)
            await self.redis.setex(key, self.LAWYER_DETAIL_TTL, json.dumps(lawyer_data))
            return True
        except Exception as e:
            logger.warning(f"Failed to set lawyer detail cache: {e}")
            return False

    async def invalidate_lawyer_detail(self, lawyer_id: int) -> bool:
        if not self.redis:
            return False
        try:
            key = self.LAWYER_DETAIL_KEY.format(lawyer_id=lawyer_id)
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Failed to invalidate lawyer detail cache: {e}")
            return False

    async def get_lawyer_list(
        self,
        specialty: Optional[str] = None,
        page: int = 1,
    ) -> Optional[dict]:
        if not self.redis:
            return None
        try:
            key = self.LAWYER_LIST_KEY.format(specialty=specialty or "all", page=page)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to get lawyer list from cache: {e}")
        return None

    async def set_lawyer_list(
        self,
        specialty: Optional[str] = None,
        page: int = 1,
        list_data: dict = None,
    ) -> bool:
        if not self.redis:
            return False
        try:
            key = self.LAWYER_LIST_KEY.format(specialty=specialty or "all", page=page)
            await self.redis.setex(key, self.LAWYER_LIST_TTL, json.dumps(list_data))
            return True
        except Exception as e:
            logger.warning(f"Failed to set lawyer list cache: {e}")
            return False

    async def invalidate_lawyer_list(self) -> bool:
        if not self.redis:
            return False
        try:
            pattern = "lawyer:list:*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    pipe = self.redis.pipeline()
                    for key in keys:
                        pipe.delete(key)
                    await pipe.execute()
                if cursor == 0:
                    break
            return True
        except Exception as e:
            logger.warning(f"Failed to invalidate lawyer list cache: {e}")
            return False


class FirmCache:
    FIRM_DETAIL_KEY = "firm:detail:{firm_id}"
    FIRM_LIST_KEY = "firm:list:{province}:{page}"

    FIRM_DETAIL_TTL = timedelta(minutes=30)
    FIRM_LIST_TTL = timedelta(minutes=10)

    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_firm_detail(self, firm_id: int) -> Optional[dict]:
        if not self.redis:
            return None
        try:
            key = self.FIRM_DETAIL_KEY.format(firm_id=firm_id)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to get firm detail from cache: {e}")
        return None

    async def set_firm_detail(self, firm_id: int, firm_data: dict) -> bool:
        if not self.redis:
            return False
        try:
            key = self.FIRM_DETAIL_KEY.format(firm_id=firm_id)
            await self.redis.setex(key, self.FIRM_DETAIL_TTL, json.dumps(firm_data))
            return True
        except Exception as e:
            logger.warning(f"Failed to set firm detail cache: {e}")
            return False

    async def invalidate_firm_detail(self, firm_id: int) -> bool:
        if not self.redis:
            return False
        try:
            key = self.FIRM_DETAIL_KEY.format(firm_id=firm_id)
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Failed to invalidate firm detail cache: {e}")
            return False

    async def get_firm_list(
        self,
        province: Optional[str] = None,
        page: int = 1,
    ) -> Optional[dict]:
        if not self.redis:
            return None
        try:
            key = self.FIRM_LIST_KEY.format(province=province or "all", page=page)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to get firm list from cache: {e}")
        return None

    async def set_firm_list(
        self,
        province: Optional[str] = None,
        page: int = 1,
        list_data: dict = None,
    ) -> bool:
        if not self.redis:
            return False
        try:
            key = self.FIRM_LIST_KEY.format(province=province or "all", page=page)
            await self.redis.setex(key, self.FIRM_LIST_TTL, json.dumps(list_data))
            return True
        except Exception as e:
            logger.warning(f"Failed to set firm list cache: {e}")
            return False

    async def invalidate_firm_list(self) -> bool:
        if not self.redis:
            return False
        try:
            pattern = "firm:list:*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    pipe = self.redis.pipeline()
                    for key in keys:
                        pipe.delete(key)
                    await pipe.execute()
                if cursor == 0:
                    break
            return True
        except Exception as e:
            logger.warning(f"Failed to invalidate firm list cache: {e}")
            return False