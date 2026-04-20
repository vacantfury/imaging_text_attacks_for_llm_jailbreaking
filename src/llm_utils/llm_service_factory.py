"""
Factory for creating LLM service instances.
"""
from typing import Dict, Optional, Type

from .llm_model import LLMModel, Provider
from .base_llm_service import BaseLLMService

# Import concrete service implementations
from .llm_services import OpenAIService, ClaudeService, GoogleService, LocalLMService, NURCClusterService


class LLMServiceFactory:
    """Factory for creating LLM service instances based on model provider."""
    
    # Registry mapping providers to their service implementations
    _PROVIDER_REGISTRY: Dict[Provider, Type[BaseLLMService]] = {
        Provider.OPENAI: OpenAIService,
        Provider.ANTHROPIC: ClaudeService,
        Provider.GOOGLE: GoogleService,
        Provider.LOCAL: LocalLMService,
        Provider.NU_CLUSTER: NURCClusterService,
    }
    
    # Cluster server manager (set by Experiment before running tasks)
    _server_manager: Optional[object] = None
    
    
    @classmethod
    def set_server_manager(cls, manager) -> None:
        """
        Register the ClusterModelServerManager.
        
        Called by Experiment.run_experiment() after starting servers,
        so factory can auto-fetch endpoint URLs for cluster models.
        
        Args:
            manager: ClusterModelServerManager instance with running servers.
        """
        cls._server_manager = manager
    
    @classmethod
    def get_registered_providers(cls) -> list[Provider]:
        """
        Get list of currently registered providers.
        
        Returns:
            List of provider enums that have registered services
        """
        return list(cls._PROVIDER_REGISTRY.keys())
    
    @classmethod
    def is_provider_supported(cls, provider: Provider) -> bool:
        """
        Check if a provider is currently supported.
        
        Args:
            provider: The provider to check
        
        Returns:
            True if provider has a registered service, False otherwise
        """
        return provider in cls._PROVIDER_REGISTRY

    @classmethod
    def register_provider(cls, provider: Provider, service_class: Type[BaseLLMService]) -> None:
        """
        Register a service class for a provider.
        
        This allows dynamic registration of new providers without modifying the factory.
        
        Args:
            provider: The provider enum
            service_class: The service class to handle this provider
        """
        cls._PROVIDER_REGISTRY[provider] = service_class

    @classmethod
    def create(cls, model: LLMModel, **kwargs) -> BaseLLMService:
        """
        Create an LLM service instance for the given model.
        
        For cluster models, automatically fetches the server endpoint
        from the registered server manager.
        
        Args:
            model: The LLM model to create a service for
            **kwargs: Additional arguments passed to the service constructor
                Common kwargs:
                - temperature (float): Sampling temperature
                - max_tokens (int): Maximum tokens to generate
                - api_key (str): API key for API-based services
                - server_url (str): For cluster models, explicit endpoint URL
        
        Returns:
            Instance of the appropriate service implementation
        
        Raises:
            ValueError: If no service is registered for the model's provider
        """
        service_class = cls._PROVIDER_REGISTRY.get(model.provider)
        
        if service_class is None:
            raise ValueError(
                f"No service registered for provider: {model.provider}. "
                f"Available providers: {list(cls._PROVIDER_REGISTRY.keys())}"
            )
        
        # For cluster models: inject server_manager from manager if not explicitly provided
        if model.provider == Provider.NU_CLUSTER and "server_manager" not in kwargs:
            if cls._server_manager is None:
                raise RuntimeError(
                    f"Cannot create service for cluster model {model.model_id}: "
                    f"No ClusterModelServerManager registered. "
                    f"Call LLMServiceFactory.set_server_manager() first."
                )
            kwargs["server_manager"] = cls._server_manager
        
        return service_class(model, **kwargs)