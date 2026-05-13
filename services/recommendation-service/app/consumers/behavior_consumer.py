import logging
from typing import Dict, Any

try:
    from services.common.events.consumer import KafkaConsumerManager
except ImportError:
    KafkaConsumerManager = None
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class BehaviorConsumer:
    def __init__(self):
        settings = get_settings()
        self._manager = KafkaConsumerManager() if KafkaConsumerManager else None
        self._group_id = settings.kafka_consumer_group
        self._db_session_factory = None

    def set_session_factory(self, session_factory):
        self._db_session_factory = session_factory

    async def start(self):
        settings = get_settings()
        if not settings.kafka_enabled or self._manager is None:
            logger.warning("Kafka not enabled or KafkaConsumerManager unavailable, behavior consumer not started")
            return

        self._manager.register_handler(
            "baixing.user.events", "user.view", self._handle_user_view
        )
        self._manager.register_handler(
            "baixing.user.events", "user.search", self._handle_user_search
        )
        self._manager.register_handler(
            "baixing.user.events", "user.like", self._handle_user_like
        )

        await self._manager.start(
            topics=["baixing.user.events"],
            group_id=self._group_id,
        )
        logger.info("Behavior consumer started")

    async def stop(self):
        await self._manager.stop()
        logger.info("Behavior consumer stopped")

    async def _handle_user_view(self, event_data: Dict[str, Any]):
        user_id = event_data.get("user_id")
        payload = event_data.get("payload", {})
        item_type = payload.get("item_type", "unknown")
        item_id = payload.get("item_id")

        if not user_id or not item_id:
            return

        features = {
            f"viewed_{item_type}": True,
            f"last_view_{item_type}": payload.get("timestamp"),
        }

        await self._update_user_features(user_id, features)
        logger.info(f"Processed user.view: user={user_id}, {item_type}={item_id}")

    async def _handle_user_search(self, event_data: Dict[str, Any]):
        user_id = event_data.get("user_id")
        payload = event_data.get("payload", {})
        query = payload.get("query", "")
        category = payload.get("category", "")

        if not user_id:
            return

        features = {
            "last_search_query": query,
            "last_search_category": category,
        }

        if category:
            features[f"searched_{category}"] = True

        await self._update_user_features(user_id, features)
        logger.info(f"Processed user.search: user={user_id}, query={query}")

    async def _handle_user_like(self, event_data: Dict[str, Any]):
        user_id = event_data.get("user_id")
        payload = event_data.get("payload", {})
        item_type = payload.get("item_type", "unknown")
        item_id = payload.get("item_id")

        if not user_id or not item_id:
            return

        features = {
            f"liked_{item_type}": True,
            f"last_like_{item_type}": payload.get("timestamp"),
        }

        await self._update_user_features(user_id, features)
        logger.info(f"Processed user.like: user={user_id}, {item_type}={item_id}")

    async def _update_user_features(self, user_id: int, features: Dict[str, Any]):
        if not self._db_session_factory:
            logger.warning("No DB session factory, skipping feature update")
            return

        try:
            from app.services.recommendation_service import recommendation_service

            async with self._db_session_factory() as session:
                async with session.begin():
                    await recommendation_service.update_user_features(
                        session, user_id, features
                    )
        except Exception as e:
            logger.error(f"Failed to update user features for user {user_id}: {e}")


behavior_consumer = BehaviorConsumer()
