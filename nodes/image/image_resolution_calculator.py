from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class ImageResolutionCalculator:
    @classmethod
    def INPUT_TYPES(cls):
        megapixel_options = [f"{i / 10:.1f}" for i in range(1, 120)]

        return {
            "required": {
                "megapixel": (megapixel_options, {"default": "1.0"}),
                "aspect_ratio": ([
                                     "1:1 (Perfect Square)",
                                     "2:3 (Classic Portrait)", "3:4 (Golden Ratio)", "3:5 (Elegant Vertical)",
                                     "4:5 (Artistic Frame)", "5:7 (Balanced Portrait)", "5:8 (Tall Portrait)",
                                     "7:9 (Modern Portrait)", "9:16 (Slim Vertical)", "9:19 (Tall Slim)",
                                     "9:21 (Ultra Tall)", "9:32 (Skyline)",
                                     "3:2 (Golden Landscape)", "4:3 (Classic Landscape)", "5:3 (Wide Horizon)",
                                     "5:4 (Balanced Frame)", "7:5 (Elegant Landscape)", "8:5 (Cinematic View)",
                                     "9:7 (Artful Horizon)", "16:9 (Panorama)", "19:9 (Cinematic Ultra Wide)",
                                     "21:9 (Epic Ultra Wide)", "32:9 (Extreme Ultra Wide)"
                                 ], {"default": "1:1 (Perfect Square)"}),
                "divisible_by": (["8", "16", "32", "64"], {"default": "8"}),
                "custom_ratio": ("BOOLEAN", {"default": False, "label_on": "Enable", "label_off": "Disable"}),
            },
            "optional": {
                "custom_aspect_ratio": ("STRING", {"default": "1:1"}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ("width", "height", "resolution", "aspect_ratio")
    FUNCTION = "calculate_dimensions"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def calculate_dimensions(self, megapixel, aspect_ratio, divisible_by, custom_ratio, custom_aspect_ratio=None):
        megapixel = float(megapixel)
        round_to = int(divisible_by)

        if custom_ratio and custom_aspect_ratio:
            numeric_ratio = custom_aspect_ratio.strip()
        else:
            numeric_ratio = aspect_ratio.split(' ')[0]

        width_ratio, height_ratio = map(int, numeric_ratio.split(':'))
        total_pixels = megapixel * 1_000_000
        dimension = (total_pixels / (width_ratio * height_ratio)) ** 0.5
        width = int(dimension * width_ratio)
        height = int(dimension * height_ratio)

        width = round(width / round_to) * round_to
        height = round(height / round_to) * round_to
        resolution = f"{width} x {height}"

        log(LogEntry(
            node_class="ImageResolutionCalculator",
            title="Dimensions Calculated",
            details={
                "Width": width,
                "Height": height,
                "Resolution": resolution,
                "Ratio": numeric_ratio
            }
        ))

        return (width, height, resolution, numeric_ratio)