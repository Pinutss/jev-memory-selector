"""Erreurs publiques du sélecteur."""


class SelectorError(Exception):
    """Erreur de base du sélecteur."""


class ConfigurationError(SelectorError):
    """Configuration manquante ou invalide."""


class ProviderError(SelectorError):
    """Échec d'un provider distant."""
