from ...common.constants import CATEGORY_PREFIX
from ...common.types import Everything

class SwitchAny:
    """
    SwitchAny
    ---------
    Conditional switch with lazy evaluation.
    Evaluates only the branch selected by the boolean condition.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "condition": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "on_true": (Everything("*"), {"lazy": True}),
                "on_false": (Everything("*"), {"lazy": True}),
            }
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("passthrough",)
    FUNCTION = "execute"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def check_lazy_status(self, condition=False, on_true=None, on_false=None):
        """Directs ComfyUI to evaluate only the active branch."""
        return ["on_true"] if condition else ["on_false"]

    def execute(self, condition=False, on_true=None, on_false=None):
        """Returns the value from the selected branch."""
        return (on_true,) if condition else (on_false,)