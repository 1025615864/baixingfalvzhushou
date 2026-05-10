from __future__ import annotations


class _ModuleIntegration:
    @staticmethod
    def get_integration_service():
        raise NotImplementedError


module_integration = _ModuleIntegration()

__all__ = ["module_integration"]
