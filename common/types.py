class Everything(str):
    """
    Wildcard type marker for ComfyUI.
    Allows a socket to accept any data type by bypassing strict type checks.
    """
    def __ne__(self, __value: object) -> bool:
        return False