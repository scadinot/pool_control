"""Service utilities mixin for safe Home Assistant service calls."""

import logging
from typing import Any, Optional

_LOGGER = logging.getLogger(__name__)


class ServiceMixin:
    """Mixin providing safe service call methods."""

    async def _safe_service_call(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any],
        entity_name: Optional[str] = None,
    ) -> bool:
        """
        Appel sécurisé d'un service Home Assistant avec gestion d'erreurs.

        Args:
            domain: Domaine du service (ex: "switch", "input_boolean")
            service: Nom du service (ex: "turn_on", "turn_off")
            service_data: Données du service (ex: {"entity_id": "switch.pool"})
            entity_name: Nom de l'entité pour les logs (optionnel)

        Returns:
            True si le service a été appelé avec succès, False sinon
        """
        try:
            await self.hass.services.async_call(domain, service, service_data)
            return True
        except Exception as e:
            entity_id = service_data.get("entity_id", "unknown")
            entity_label = entity_name or entity_id
            _LOGGER.error(
                "Failed to call service %s.%s for %s: %s",
                domain,
                service,
                entity_label,
                e,
            )
            return False
