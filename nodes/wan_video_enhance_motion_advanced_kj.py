import torch
from .constants import CATEGORY_PREFIX
from .logger import LogEntry, log


try:
    import comfy.model_management as mm
except ImportError:
    mm = None

class WanVideoEnhanceMotionAdvancedKJ:
    """
    WanVideoEnhanceMotionAdvancedKJ
    -------------------------------
    Applies motion amplification with color drift protection to image_embeds.
    Uses PainterI2V algorithm with advanced color correction.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_embeds": ("WANVIDIMAGE_EMBEDS",),
                "motion_amplitude": ("FLOAT", {"default": 1.1, "min": 1.0, "max": 1.5, "step": 0.01, "tooltip": "Motion amplification factor (>1.0 = more dynamic, 1.0 = disabled)"}),
                "color_protect": ("BOOLEAN", {"default": True}),
                "correct_strength": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 0.3, "step": 0.01, "tooltip": "Color drift correction strength"}),
            }
        }

    RETURN_TYPES = ("WANVIDIMAGE_EMBEDS",)
    RETURN_NAMES = ("enhanced_image_embeds",)
    FUNCTION = "enhance_motion"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"

    def enhance_motion(self, image_embeds, motion_amplitude=1.15, color_protect=True, correct_strength=0.05):
        # Early exit if no enhancement needed
        if motion_amplitude <= 1.0:
            log(LogEntry(
                node_class="WanVideoEnhanceMotionAdvancedKJ",
                title="Motion enhancement skipped",
                details={"Reason": "motion_amplitude <= 1.0"},
                footer="Passthrough original embeds"
            ))
            return (image_embeds,)

        # Make a deep copy to avoid modifying original
        enhanced = {}
        for k, v in image_embeds.items():
            if isinstance(v, torch.Tensor):
                enhanced[k] = v.clone()
            else:
                enhanced[k] = v

        y = enhanced["image_embeds"]

        # Ensure we have at least 2 frames
        if y.dim() != 4 or y.shape[1] < 2:
            log(LogEntry(
                node_class="WanVideoEnhanceMotionAdvancedKJ",
                title="Insufficient frames",
                details={"Frames": y.shape[1] if y.dim() == 4 else "N/A", "Required": "≥2"},
                footer="Passthrough without enhancement"
            ))
            return (enhanced,)

        device = mm.get_torch_device() if mm else y.device
        y = y.to(device)

        # Store original for color correction
        y_original = y.clone()

        # Log processing start
        log(LogEntry(
            node_class="WanVideoEnhanceMotionAdvancedKJ",
            title="Applying motion amplification",
            details={
                "Motion amplitude": f"{motion_amplitude:.2f}",
                "Total frames": y.shape[1],
                "Base frame mean": f"{y[:, 0:1].mean():.4f}"
            }
        ))

        # --- Core PainterI2V algorithm ---
        base_latent = y[:, 0:1]
        other_latent = y[:, 1:]
        base_latent_bc = base_latent.expand(-1, other_latent.shape[1], -1, -1)

        diff = other_latent - base_latent_bc
        diff_mean = diff.mean(dim=(0, 2, 3), keepdim=True)
        diff_centered = diff - diff_mean
        scaled_other = base_latent_bc + diff_centered * motion_amplitude + diff_mean
        scaled_other = torch.clamp(scaled_other, -6.0, 6.0)

        enhanced_y = torch.cat([base_latent, scaled_other], dim=1)
        # ---

        corrected_channels = 0
        brightness_corrected = False
        brightness_boost = None

        # === COLOR DRIFT PROTECTION ===
        if color_protect and correct_strength > 0:
            post_enhanced = enhanced_y.clone()

            orig_mean = y_original.mean(dim=(1, 2, 3))
            enhanced_mean = post_enhanced.mean(dim=(1, 2, 3))
            mean_drift = torch.abs(enhanced_mean - orig_mean) / (torch.abs(orig_mean) + 1e-6)
            problem_channels = mean_drift > 0.18

            if problem_channels.any():
                drift_amount = enhanced_mean - orig_mean
                correction = drift_amount * problem_channels.float() * correct_strength * 0.03

                for c in range(y.shape[0]):
                    if correction[c].abs() > 0:
                        post_enhanced[c] = torch.where(
                            post_enhanced[c] > 0,
                            post_enhanced[c] - correction[c],
                            post_enhanced[c]
                        )
                        corrected_channels += 1

            orig_brightness = y_original.mean()
            enhanced_brightness = post_enhanced.mean()

            if enhanced_brightness < orig_brightness * 0.92:
                brightness_boost = min(orig_brightness / (enhanced_brightness + 1e-6), 1.05)
                post_enhanced = torch.where(
                    post_enhanced < 0.5,
                    post_enhanced * brightness_boost,
                    post_enhanced
                )
                brightness_corrected = True

            enhanced_y = torch.clamp(post_enhanced, -6.0, 6.0)

        # Log color correction results
        if corrected_channels > 0 or brightness_corrected:
            log(LogEntry(
                node_class="WanVideoEnhanceMotionAdvancedKJ",
                title="Color protection applied",
                details={
                    "Channels corrected": corrected_channels,
                    "Brightness boost": f"{brightness_boost:.3f}" if brightness_corrected else "N/A"
                }
            ))

        enhanced["image_embeds"] = enhanced_y.cpu()

        log(LogEntry(
            node_class="WanVideoEnhanceMotionAdvancedKJ",
            title="Motion enhancement completed",
            details={
                "Enhanced frames mean": f"{enhanced_y[:, 1:].mean():.4f}",
                "Output device": str(enhanced["image_embeds"].device)
            },
            footer="Ready for WanVideoImageToVideoEncode"
        ))

        return (enhanced,)