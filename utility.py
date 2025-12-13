class Everything(str):
    """Wildcard type marker."""

    def __ne__(self, __value: object) -> bool:
        return False


class LogValue:
    """
    LogValue
    ------------------
    Logs the type, value, and an optional checkpoint name to the console based on the log_to_console flag.
    Also outputs the formatted log message as a STRING, which can be used by other nodes (e.g., for saving to a file).
    The console log includes the node tag and force trigger for identification if logging is enabled,
    but the output string contains only the core information.
    Passes the input value through unchanged to the output.
    Uses a force_log_trigger to ensure execution even if primary output is not connected.
    The force_log_trigger is marked with forceInput=True, so any change to it (e.g., from a connected node)
    will cause this node to execute.

    Inputs:
        input_value (Any) - Any value to be logged and passed through
        checkpoint_name (STRING) - Optional name for the checkpoint/log point (default: "LogPoint")
        force_log_trigger (INT) - Optional trigger to force execution (default: 0, connect any changing value)
        log_to_console (BOOLEAN) - Flag to enable or disable console logging (default: True)

    Outputs:
        output_value (Any) - The same value as input_value
        log_string (STRING) - The clean log message as a string (without block start/end markers, node tags, or force trigger info)

    Logs:
        Console messages are printed based on the log_to_console flag.
        They include [LogValue] tags and force trigger info for identification when enabled.
        The output log_string is always clean without markers, tags, or force trigger info.
    """

    LOG_TAG = "[LogValue]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_value": (Everything("*"),),
                "force_log_trigger": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFF, "forceInput": True}),
                "log_to_console": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "checkpoint_name": ("STRING", {"default": "LogPoint", "multiline": False}),
            }
        }

    RETURN_TYPES = (Everything("*"), "STRING")
    RETURN_NAMES = ("output_value", "log_string")
    FUNCTION = "log_and_pass"
    CATEGORY = "Stalkervr/Utils"

    def log_and_pass(self, input_value, force_log_trigger, log_to_console, checkpoint_name="LogPoint"):
        """
        Logs the checkpoint name, type, and value to console based on log_to_console flag.
        Returns the input value and a clean log message string regardless of the flag.
        The force_log_trigger parameter ensures this function runs when its value changes.
        """
        value_type = type(input_value).__name__

        core_log_info = f"""Checkpoint: {checkpoint_name}
Type: {value_type}
Value: {input_value}"""

        if log_to_console:
            console_formatted_block = f"""
{self.LOG_TAG} ==================== LOG START ====================
{self.LOG_TAG} {core_log_info.replace(chr(10), chr(10) + self.LOG_TAG + " ")}
{self.LOG_TAG} Force Trigger: {force_log_trigger} (Used to ensure execution)
{self.LOG_TAG} ==================== LOG END ======================
"""
            print(console_formatted_block)

        clean_output_string = f"\n{core_log_info}\n"

        return (input_value, clean_output_string)
