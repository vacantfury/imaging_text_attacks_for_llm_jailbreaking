"""
Unified factory for defenses (NoDefense + SAGE + SemanticSmooth + ECSO + ...).

Use as:
    from src.defense import create_defense
    defense = create_defense("no_defense")          # pure attack baseline
    defense = create_defense("sage")
    defense = create_defense("ecso", judge_model="gpt-5-nano")
"""
from src.utils.logger import get_logger
from .base import Defense

logger = get_logger(__name__)


# Registry populated by submodule imports + @register_defense decorator.
DEFENSES: dict[str, type[Defense]] = {}


def register_defense(cls: type[Defense]) -> type[Defense]:
    """Class decorator: register Defense subclass under its type_name."""
    name = cls.type_name
    if not name:
        raise ValueError(
            f"{cls.__name__} must declare a non-empty type_name to register.")
    if name in DEFENSES and DEFENSES[name] is not cls:
        raise ValueError(
            f"Defense {name!r} already registered to {DEFENSES[name].__name__}; "
            f"cannot re-register {cls.__name__}.")
    DEFENSES[name] = cls
    return cls


def create_defense(name: str, **kwargs) -> Defense:
    """Create a Defense instance by canonical type_name."""
    if name not in DEFENSES:
        raise ValueError(
            f"Unknown defense {name!r}. Available: {sorted(DEFENSES)}")
    try:
        return DEFENSES[name](**kwargs)
    except Exception:
        logger.exception(f"Error constructing defense {name!r}")
        raise


def list_defenses() -> list[str]:
    return sorted(DEFENSES.keys())


# Backward-compat alias for older imports.
create_defender = create_defense


# Import submodules so their @register_defense decorators fire.
# Order doesn't matter; each class registers under its own type_name.
from . import no_defense  # noqa: E402,F401
from . import sage  # noqa: E402,F401
from . import semantic_smooth  # noqa: E402,F401
from . import ecso  # noqa: E402,F401
# Paper C defenses (import after sage/ecso — they reuse those primitives).
from . import modality_complete  # noqa: E402,F401
from . import joint_verify  # noqa: E402,F401
