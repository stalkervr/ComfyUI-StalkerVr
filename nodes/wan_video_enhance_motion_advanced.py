import torch
from .constants import CATEGORY_PREFIX
from .logger import LogEntry, log

class WanVideoEnhanceMotionAdvanced:
    """
    WanVideoEnhanceMotionAdvanced
    ----------------------------
    Advanced motion enhancement with color drift protection for CONDITIONING/LATENT.
    Outputs both enhanced and original conditioning for dual-sampler workflows.
    Based on PainterI2VAdvanced logic with color correction.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "latent": ("LATENT",),
                "vae": ("VAE",),
                "motion_amplitude": ("FLOAT", {"default": 1.3, "min": 1.0, "max": 2.0, "step": 0.05}),
                "color_protect": ("BOOLEAN", {"default": True}),
                "correct_strength": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 0.3, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "CONDITIONING", "CONDITIONING", "LATENT")
    RETURN_NAMES = ("high_positive", "high_negative", "low_positive", "low_negative", "latent")
    FUNCTION = "enhance_motion_advanced"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"

    def _extract_params_from_conditioning(self, conditioning):
        """Extract parameters from both tuple and list formats."""
        if not isinstance(conditioning, list) or len(conditioning) == 0:
            return None
        first_item = conditioning[0]
        if isinstance(first_item, tuple) and len(first_item) >= 2:
            return first_item[1] if isinstance(first_item[1], dict) else None
        elif isinstance(first_item, list) and len(first_item) >= 2:
            return first_item[1] if isinstance(first_item[1], dict) else None
        return None

    def _clone_conditioning(self, conditioning):
        """Create a deep copy of conditioning preserving format."""
        cloned = []
        for cond_item in conditioning:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                tensor_part = cond_item[0]
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    new_params = {}
                    for k, v in params_part.items():
                        if isinstance(v, torch.Tensor):
                            new_params[k] = v.clone()
                        elif isinstance(v, list):
                            new_params[k] = [item.clone() if isinstance(item, torch.Tensor) else item for item in v]
                        else:
                            new_params[k] = v
                    cloned.append([tensor_part, new_params] if isinstance(cond_item, list) else (tensor_part, new_params))
                else:
                    cloned.append(cond_item)
            else:
                cloned.append(cond_item)
        return cloned

    def enhance_motion_advanced(self, positive, negative, latent, vae,
                                motion_amplitude=1.3, color_protect=True, correct_strength=0.05):

        latent_samples = latent["samples"]
        if latent_samples.dim() != 5:
            log(LogEntry(
                node_class="WanVideoEnhanceMotionAdvanced",
                title="Invalid latent dimensions",
                details={"Expected": "5D [B, C, T, H, W]", "Got": f"{latent_samples.dim()}D"},
                footer="Returning original conditioning"
            ))
            return (positive, negative, positive, negative, latent)

        batch_size, channels, latent_frames, latent_h, latent_w = latent_samples.shape
        UPSAMPLING_FACTOR = 8

        pos_params = self._extract_params_from_conditioning(positive)
        concat_latent_original = pos_params.get("concat_latent_image") if pos_params else None

        if concat_latent_original is None:
            log(LogEntry(
                node_class="WanVideoEnhanceMotionAdvanced",
                title="Missing concat_latent_image",
                details={"Status": "Parameter not found in conditioning"},
                footer="Returning original conditioning"
            ))
            return (positive, negative, positive, negative, latent)

        log(LogEntry(
            node_class="WanVideoEnhanceMotionAdvanced",
            title="Starting motion enhancement",
            details={
                "Input shape": str(concat_latent_original.shape),
                "Motion amplitude": f"{motion_amplitude:.2f}",
                "Color protect": color_protect
            }
        ))

        concat_latent_enhanced = concat_latent_original.clone()

        # Apply motion amplification
        if motion_amplitude > 1.0 and concat_latent_enhanced.shape[2] > 1:
            base_latent = concat_latent_enhanced[:, :, 0:1]
            gray_latent = concat_latent_enhanced[:, :, 1:]

            diff = gray_latent - base_latent
            diff_mean = diff.mean(dim=(1, 3, 4), keepdim=True)
            diff_centered = diff - diff_mean
            scaled_latent = base_latent + diff_centered * motion_amplitude + diff_mean
            scaled_latent = torch.clamp(scaled_latent, -6.0, 6.0)
            concat_latent_enhanced = torch.cat([base_latent, scaled_latent], dim=2)

            # Color protection
            if color_protect and correct_strength > 0:
                post_enhanced = concat_latent_enhanced.clone()
                orig_mean = concat_latent_original.mean(dim=(2, 3, 4))
                enhanced_mean = post_enhanced.mean(dim=(2, 3, 4))
                mean_drift = torch.abs(enhanced_mean - orig_mean) / (torch.abs(orig_mean) + 1e-6)
                problem_channels = mean_drift > 0.18

                corrected_channels = 0
                if problem_channels.any():
                    drift_amount = enhanced_mean - orig_mean
                    correction = drift_amount * problem_channels.float() * correct_strength * 0.03
                    for b in range(batch_size):
                        for c in range(channels):
                            if correction[b, c].abs() > 0:
                                post_enhanced[b, c] = torch.where(
                                    post_enhanced[b, c] > 0,
                                    post_enhanced[b, c] - correction[b, c],
                                    post_enhanced[b, c]
                                )
                                corrected_channels += 1

                orig_brightness = concat_latent_original.mean()
                enhanced_brightness = post_enhanced.mean()
                brightness_corrected = False
                brightness_boost = None

                if enhanced_brightness < orig_brightness * 0.92:
                    brightness_boost = min(orig_brightness / (enhanced_brightness + 1e-6), 1.05)
                    post_enhanced = torch.where(
                        post_enhanced < 0.5,
                        post_enhanced * brightness_boost,
                        post_enhanced
                    )
                    brightness_corrected = True

                concat_latent_enhanced = torch.clamp(post_enhanced, -6.0, 6.0)

                if corrected_channels > 0 or brightness_corrected:
                    log(LogEntry(
                        node_class="WanVideoEnhanceMotionAdvanced",
                        title="Color protection applied",
                        details={
                            "Channels corrected": corrected_channels,
                            "Brightness boost": f"{brightness_boost:.3f}" if brightness_corrected else "N/A"
                        }
                    ))

        # Get or create mask
        concat_mask = pos_params.get("concat_mask") if pos_params else None
        if concat_mask is None:
            device = concat_latent_enhanced.device
            concat_mask = torch.ones(
                (1, 1, concat_latent_enhanced.shape[2], concat_latent_enhanced.shape[3], concat_latent_enhanced.shape[4]),
                device=device, dtype=concat_latent_enhanced.dtype
            )
            concat_mask[:, :, 0] = 0.0

        # Build enhanced conditioning
        enhanced_positive = self._build_enhanced_conditioning(positive, concat_latent_enhanced, concat_mask)
        enhanced_negative = self._build_enhanced_conditioning(negative, concat_latent_enhanced, concat_mask)
        original_positive = self._clone_conditioning(positive)
        original_negative = self._clone_conditioning(negative)

        log(LogEntry(
            node_class="WanVideoEnhanceMotionAdvanced",
            title="Motion enhancement completed",
            details={
                "Output shape": str(concat_latent_enhanced.shape),
                "Enhanced positive items": len(enhanced_positive),
                "Enhanced negative items": len(enhanced_negative)
            },
            footer="Ready for dual-sampler workflow"
        ))

        return (enhanced_positive, enhanced_negative, original_positive, original_negative, latent)

    def _build_enhanced_conditioning(self, conditioning, concat_latent, concat_mask):
        """Helper to inject enhanced latents into conditioning."""
        result = []
        for cond_item in conditioning:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                tensor_part = cond_item[0]
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    new_params = params_part.copy()
                    new_params.update({"concat_latent_image": concat_latent, "concat_mask": concat_mask})
                    result.append([tensor_part, new_params] if isinstance(cond_item, list) else (tensor_part, new_params))
                else:
                    result.append(cond_item)
            else:
                result.append(cond_item)
        return result