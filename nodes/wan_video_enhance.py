import torch
import comfy.model_management as mm
import comfy.utils
import node_helpers
import comfy.latent_formats


from .constants import (
    CATEGORY_PREFIX
)


class WanVideoEnhanceMotionAdvancedKJ:
    """
    WanVideoEnhanceMotionAdvancedKJ
    -------------------------------
    Applies motion amplification with color drift protection to image_embeds.
    Uses PainterI2V algorithm with advanced color correction from PainterI2VAdvanced.

    Input: image_embeds from WanVideoImageToVideoEncode
    Output: modified image_embeds with enhanced motion and color protection
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_embeds": ("WANVIDIMAGE_EMBEDS",),
                "motion_amplitude": ("FLOAT", {
                    "default": 1.1,
                    "min": 1.0,
                    "max": 1.5,
                    "step": 0.01,
                    "tooltip": "Motion amplification factor (>1.0 = more dynamic, 1.0 = disabled)"
                }),
                "color_protect": ("BOOLEAN", {"default": True}),
                "correct_strength": ("FLOAT", {
                    "default": 0.05,
                    "min": 0.0,
                    "max": 0.3,
                    "step": 0.01,
                    "tooltip": "Color drift correction strength"
                }),
            }
        }

    RETURN_TYPES = ("WANVIDIMAGE_EMBEDS",)
    RETURN_NAMES = ("enhanced_image_embeds",)
    FUNCTION = "enhance_motion"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"
    DESCRIPTION = "Amplifies motion in latent space with color drift protection."

    def enhance_motion(self, image_embeds, motion_amplitude=1.15, color_protect=True, correct_strength=0.05):
        # Early exit if no enhancement needed
        if motion_amplitude <= 1.0:
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
            print("⚠️ [WanVideoEnhanceMotionAdvancedKJ] Warning: Need at least 2 frames for motion enhancement")
            return (enhanced,)

        device = mm.get_torch_device()
        y = y.to(device)

        # Store original for color correction
        y_original = y.clone()

        # === Enhanced logging format ===
        print(f"\n🎯 [WanVideoEnhanceMotionAdvancedKJ] Applying motion amplification")
        print(f"  Motion amplitude: {motion_amplitude:.2f}")
        print(f"  Total frames: {y.shape[1]}")
        print(f"  Base frame mean: {y[:, 0:1].mean():.4f}")

        # --- Core PainterI2V algorithm ---
        base_latent = y[:, 0:1]  # [C, 1, H, W]
        other_latent = y[:, 1:]  # [C, T-1, H, W]

        # Broadcast first frame
        base_latent_bc = base_latent.expand(-1, other_latent.shape[1], -1, -1)

        # Calculate difference and amplify (preserve brightness stability)
        diff = other_latent - base_latent_bc
        diff_mean = diff.mean(dim=(0, 2, 3), keepdim=True)
        diff_centered = diff - diff_mean
        scaled_other = base_latent_bc + diff_centered * motion_amplitude + diff_mean

        # Safe clipping (WanVideo latent range is typically [-6, 6])
        scaled_other = torch.clamp(scaled_other, -6.0, 6.0)

        # Reconstruct full sequence
        enhanced_y = torch.cat([base_latent, scaled_other], dim=1)
        # ---

        corrected_channels = 0

        # === COLOR DRIFT PROTECTION (adapted from WanVideoEnhanceMotionAdvanced) ===
        if color_protect and correct_strength > 0:
            post_enhanced = enhanced_y.clone()

            # Calculate mean drift per channel (adapted for 4D format)
            orig_mean = y_original.mean(dim=(1, 2, 3))  # [C]
            enhanced_mean = post_enhanced.mean(dim=(1, 2, 3))  # [C]

            # Calculate relative drift
            mean_drift = torch.abs(enhanced_mean - orig_mean) / (torch.abs(orig_mean) + 1e-6)
            problem_channels = mean_drift > 0.18

            if problem_channels.any():
                drift_amount = enhanced_mean - orig_mean
                correction = drift_amount * problem_channels.float() * correct_strength * 0.03

                # Apply correction to problematic channels
                for c in range(y.shape[0]):  # C channels
                    if correction[c].abs() > 0:
                        post_enhanced[c] = torch.where(
                            post_enhanced[c] > 0,
                            post_enhanced[c] - correction[c],
                            post_enhanced[c]
                        )
                        corrected_channels += 1

            # Brightness protection
            orig_brightness = y_original.mean()
            enhanced_brightness = post_enhanced.mean()
            brightness_corrected = False

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
            if corrected_channels > 0:
                print(f"  🎨 Color correction applied to {corrected_channels} channels")
            if brightness_corrected:
                print(f"  💡 Brightness correction applied (boost={brightness_boost:.3f})")
        # === END COLOR DRIFT PROTECTION ===

        enhanced["image_embeds"] = enhanced_y.cpu()
        print(f"  ⚡ Enhanced frames mean: {enhanced_y[:, 1:].mean():.4f}")
        print("🎯 Motion enhancement with color protection completed\n")

        return (enhanced,)


class WanVideoEnhanceMotionAdvanced:
    """
    WanVideoEnhanceMotionAdvanced
    ----------------------------
    Advanced motion enhancement with color drift protection.
    Outputs both enhanced and original conditioning (dual-sampler ready).

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
                "motion_amplitude": ("FLOAT", {
                    "default": 1.3,
                    "min": 1.0,
                    "max": 2.0,
                    "step": 0.05,
                }),
                "color_protect": ("BOOLEAN", {"default": True}),
                "correct_strength": ("FLOAT", {
                    "default": 0.05,
                    "min": 0.0,
                    "max": 0.3,
                    "step": 0.01,
                }),
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

        # Standard format: [(tensor, dict)]
        if isinstance(first_item, tuple) and len(first_item) >= 2:
            return first_item[1] if isinstance(first_item[1], dict) else None

        # List format: [[tensor, dict]]
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
                    if isinstance(cond_item, list):
                        cloned.append([tensor_part, new_params])
                    else:
                        cloned.append((tensor_part, new_params))
                else:
                    cloned.append(cond_item)
            else:
                cloned.append(cond_item)
        return cloned

    def enhance_motion_advanced(self, positive, negative, latent, vae,
                                motion_amplitude=1.3, color_protect=True, correct_strength=0.05):

        # Extract dimensions from latent
        latent_samples = latent["samples"]
        if latent_samples.dim() != 5:
            print("[WanVideoEnhanceMotionAdvanced] ERROR: Expected 5D latent [B, C, T, H, W]")
            return (positive, negative, positive, negative, latent)

        batch_size, channels, latent_frames, latent_h, latent_w = latent_samples.shape
        UPSAMPLING_FACTOR = 8
        width = latent_w * UPSAMPLING_FACTOR
        height = latent_h * UPSAMPLING_FACTOR
        length = (latent_frames - 1) * 4 + 1

        # Extract params from positive conditioning
        pos_params = self._extract_params_from_conditioning(positive)
        concat_latent_original = None

        if pos_params is not None and "concat_latent_image" in pos_params:
            concat_latent_original = pos_params["concat_latent_image"]
        else:
            print("[WanVideoEnhanceMotionAdvanced] WARNING: No concat_latent_image found, returning originals")
            return (positive, negative, positive, negative, latent)

        print(f"[WanVideoEnhanceMotionAdvanced] Found concat_latent_image with shape: {concat_latent_original.shape}")

        # Create enhanced version
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

            # Apply color protection
            if color_protect and correct_strength > 0:
                post_enhanced = concat_latent_enhanced.clone()

                # Calculate mean drift
                orig_mean = concat_latent_original.mean(dim=(2, 3, 4))  # [B, C]
                enhanced_mean = post_enhanced.mean(dim=(2, 3, 4))  # [B, C]

                mean_drift = torch.abs(enhanced_mean - orig_mean) / (torch.abs(orig_mean) + 1e-6)
                problem_channels = mean_drift > 0.18

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

                # Brightness protection
                orig_brightness = concat_latent_original.mean()
                enhanced_brightness = post_enhanced.mean()

                if enhanced_brightness < orig_brightness * 0.92:
                    brightness_boost = min(orig_brightness / (enhanced_brightness + 1e-6), 1.05)
                    post_enhanced = torch.where(
                        post_enhanced < 0.5,
                        post_enhanced * brightness_boost,
                        post_enhanced
                    )

                concat_latent_enhanced = torch.clamp(post_enhanced, -6.0, 6.0)

        # Get mask from original conditioning
        concat_mask = pos_params.get("concat_mask", None)
        if concat_mask is None:
            # Create default mask
            device = concat_latent_enhanced.device
            concat_mask = torch.ones((1, 1, concat_latent_enhanced.shape[2],
                                      concat_latent_enhanced.shape[3],
                                      concat_latent_enhanced.shape[4]),
                                     device=device, dtype=concat_latent_enhanced.dtype)
            concat_mask[:, :, 0] = 0.0

        # Create enhanced conditioning
        enhanced_positive = []
        enhanced_negative = []
        original_positive = self._clone_conditioning(positive)
        original_negative = self._clone_conditioning(negative)

        for cond_item in positive:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                tensor_part = cond_item[0]
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    new_params = params_part.copy()
                    new_params.update({"concat_latent_image": concat_latent_enhanced, "concat_mask": concat_mask})
                    if isinstance(cond_item, list):
                        enhanced_positive.append([tensor_part, new_params])
                    else:
                        enhanced_positive.append((tensor_part, new_params))
                else:
                    enhanced_positive.append(cond_item)
            else:
                enhanced_positive.append(cond_item)

        for cond_item in negative:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                tensor_part = cond_item[0]
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    new_params = params_part.copy()
                    new_params.update({"concat_latent_image": concat_latent_enhanced, "concat_mask": concat_mask})
                    if isinstance(cond_item, list):
                        enhanced_negative.append([tensor_part, new_params])
                    else:
                        enhanced_negative.append((tensor_part, new_params))
                else:
                    enhanced_negative.append(cond_item)
            else:
                enhanced_negative.append(cond_item)

        print(
            f"✅ [WanVideoEnhanceMotionAdvanced] Applied advanced motion enhancement (amplitude={motion_amplitude:.2f}, color_protect={color_protect})")
        return (enhanced_positive, enhanced_negative, original_positive, original_negative, latent)


class WanVideoEnhanceSVI:
    """
    WanVideoEnhanceSVI
    ------------------
    Advanced SVI motion enhancement with color drift protection.
    Outputs both enhanced (high) and original (low) conditioning for dual-sampler workflow.

    Combines BoyoPainterSVI context preservation with WanVideoEnhanceMotionAdvanced color correction.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "length": ("INT", {"default": 81, "min": 1, "max": 4096, "step": 4}),
                "anchor_samples": ("LATENT",),
                "motion_amplitude": ("FLOAT", {"default": 1.15, "min": 1.0, "max": 2.0, "step": 0.05}),
                "motion_latent_count": ("INT", {"default": 1, "min": 0, "max": 128, "step": 1}),
                "color_protect": ("BOOLEAN", {"default": True}),
                "correct_strength": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 0.3, "step": 0.01}),
            },
            "optional": {
                "prev_samples": ("LATENT",),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "CONDITIONING", "CONDITIONING", "LATENT")
    RETURN_NAMES = ("high_positive", "high_negative", "low_positive", "low_negative", "latent")
    FUNCTION = "enhance_svi"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"

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
                    if isinstance(cond_item, list):
                        cloned.append([tensor_part, new_params])
                    else:
                        cloned.append((tensor_part, new_params))
                else:
                    cloned.append(cond_item)
            else:
                cloned.append(cond_item)
        return cloned

    def enhance_svi(self, positive, negative, length, anchor_samples, motion_amplitude,
                    motion_latent_count, color_protect=True, correct_strength=0.05, prev_samples=None):

        # SVI Context Preservation Logic
        anchor_latent = anchor_samples["samples"].clone()
        B, C, T, H, W = anchor_latent.shape
        empty_latent = torch.zeros([B, 16, ((length - 1) // 4) + 1, H, W],
                                   device=comfy.model_management.intermediate_device())
        total_latents = (length - 1) // 4 + 1
        device = anchor_latent.device
        dtype = anchor_latent.dtype

        # Context concatenation from SVI
        if prev_samples is None or motion_latent_count == 0:
            padding_size = total_latents - anchor_latent.shape[2]
            image_cond_latent = anchor_latent
        else:
            motion_latent = prev_samples["samples"][:, :, -motion_latent_count:].clone()
            padding_size = total_latents - anchor_latent.shape[2] - motion_latent.shape[2]
            image_cond_latent = torch.cat([anchor_latent, motion_latent], dim=2)

        padding = torch.zeros(1, C, padding_size, H, W, dtype=dtype, device=device)
        padding = comfy.latent_formats.Wan21().process_out(padding)
        image_cond_latent = torch.cat([image_cond_latent, padding], dim=2)

        # Store original for low conditioning and color correction
        image_cond_latent_original = image_cond_latent.clone()
        image_cond_latent_enhanced = image_cond_latent.clone()

        # Apply motion enhancement and color correction to enhanced version
        if motion_amplitude > 1.0 and image_cond_latent_enhanced.shape[2] > 1:
            base_latent = image_cond_latent_enhanced[:, :, 0:1]
            subsequent_latent = image_cond_latent_enhanced[:, :, 1:]

            if subsequent_latent.shape[2] > 0:
                diff = subsequent_latent - base_latent
                diff_mean = diff.mean(dim=(1, 3, 4), keepdim=True)
                diff_centered = diff - diff_mean
                scaled_latent = base_latent + diff_centered * motion_amplitude + diff_mean
                scaled_latent = torch.clamp(scaled_latent, -6, 6)
                image_cond_latent_enhanced = torch.cat([base_latent, scaled_latent], dim=2)

                # Color drift protection
                if color_protect and correct_strength > 0:
                    post_enhanced = image_cond_latent_enhanced.clone()

                    orig_mean = image_cond_latent_original.mean(dim=(2, 3, 4))
                    enhanced_mean = post_enhanced.mean(dim=(2, 3, 4))

                    mean_drift = torch.abs(enhanced_mean - orig_mean) / (torch.abs(orig_mean) + 1e-6)
                    problem_channels = mean_drift > 0.18

                    if problem_channels.any():
                        drift_amount = enhanced_mean - orig_mean
                        correction = drift_amount * problem_channels.float() * correct_strength * 0.03

                        for b in range(B):
                            for c in range(C):
                                if correction[b, c].abs() > 0:
                                    post_enhanced[b, c] = torch.where(
                                        post_enhanced[b, c] > 0,
                                        post_enhanced[b, c] - correction[b, c],
                                        post_enhanced[b, c]
                                    )

                    # Brightness protection
                    orig_brightness = image_cond_latent_original.mean()
                    enhanced_brightness = post_enhanced.mean()

                    if enhanced_brightness < orig_brightness * 0.92:
                        brightness_boost = min(orig_brightness / (enhanced_brightness + 1e-6), 1.05)
                        post_enhanced = torch.where(
                            post_enhanced < 0.5,
                            post_enhanced * brightness_boost,
                            post_enhanced
                        )

                    image_cond_latent_enhanced = torch.clamp(post_enhanced, -6, 6)

        # Create conditioning mask
        mask = torch.ones((1, 1, empty_latent.shape[2], H, W), device=device, dtype=dtype)
        mask[:, :, :1] = 0.0

        # Create high conditioning (enhanced)
        high_positive = []
        high_negative = []

        for cond_item in positive:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                tensor_part = cond_item[0]
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    new_params = params_part.copy()
                    new_params.update({"concat_latent_image": image_cond_latent_enhanced, "concat_mask": mask})
                    if isinstance(cond_item, list):
                        high_positive.append([tensor_part, new_params])
                    else:
                        high_positive.append((tensor_part, new_params))
                else:
                    high_positive.append(cond_item)
            else:
                high_positive.append(cond_item)

        for cond_item in negative:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                tensor_part = cond_item[0]
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    new_params = params_part.copy()
                    new_params.update({"concat_latent_image": image_cond_latent_enhanced, "concat_mask": mask})
                    if isinstance(cond_item, list):
                        high_negative.append([tensor_part, new_params])
                    else:
                        high_negative.append((tensor_part, new_params))
                else:
                    high_negative.append(cond_item)
            else:
                high_negative.append(cond_item)

        # Create low conditioning (original)
        low_positive = self._clone_conditioning(positive)
        low_negative = self._clone_conditioning(negative)

        # Update low conditioning with original latent
        for cond_item in low_positive:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    params_part.update({"concat_latent_image": image_cond_latent_original, "concat_mask": mask})

        for cond_item in low_negative:
            if isinstance(cond_item, (list, tuple)) and len(cond_item) >= 2:
                params_part = cond_item[1]
                if isinstance(params_part, dict):
                    params_part.update({"concat_latent_image": image_cond_latent_original, "concat_mask": mask})

        # Reference latent enhancement (applied to both high and low)
        ref_latent = anchor_latent[:, :, 0:1]

        high_positive = node_helpers.conditioning_set_values(high_positive, {"reference_latents": [ref_latent]},
                                                             append=True)
        high_negative = node_helpers.conditioning_set_values(high_negative,
                                                             {"reference_latents": [torch.zeros_like(ref_latent)]},
                                                             append=True)

        low_positive = node_helpers.conditioning_set_values(low_positive, {"reference_latents": [ref_latent]},
                                                            append=True)
        low_negative = node_helpers.conditioning_set_values(low_negative,
                                                            {"reference_latents": [torch.zeros_like(ref_latent)]},
                                                            append=True)

        out_latent = {"samples": empty_latent}

        print(
            f"✅ [WanVideoEnhanceSVI] Applied SVI enhancement (amplitude={motion_amplitude:.2f}, color_protect={color_protect})")
        return (high_positive, high_negative, low_positive, low_negative, out_latent)


class WanVideoSVIProEmbeds_EnhancedMotion:
    """
    WanVideoSVIProEmbeds_EnhancedMotion
    ----------------------------------
    Enhanced SVI embeds with proper temporal mask for motion dynamics.
    Uses full attention mask to enable effective motion amplification.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "anchor_samples": ("LATENT", {"tooltip": "Initial start image encoded"}),
            "num_frames": (
            "INT", {"default": 81, "min": 1, "max": 10000, "step": 4, "tooltip": "Number of frames to encode"}),
            "motion_intensity": ("FLOAT", {
                "default": 1.0,
                "min": 0.5,
                "max": 2.0,
                "step": 0.1,
                "tooltip": "Motion intensity boost (higher = more dynamic)"
            }),
        },
            "optional": {
                "prev_samples": ("LATENT", {"tooltip": "Last latent from previous generation"}),
                "motion_latent_count": ("INT", {"default": 1, "min": 0, "max": 100, "step": 1,
                                                "tooltip": "Number of latents used to continue"}),
            }
        }

    RETURN_TYPES = ("WANVIDIMAGE_EMBEDS",)
    RETURN_NAMES = ("image_embeds",)
    FUNCTION = "add_enhanced"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"

    def add_enhanced(self, anchor_samples, num_frames, motion_intensity=1.0,
                     prev_samples=None, motion_latent_count=1):

        anchor_latent = anchor_samples["samples"][0].clone()

        C, T, H, W = anchor_latent.shape

        total_latents = (num_frames - 1) // 4 + 1
        device = anchor_latent.device
        dtype = anchor_latent.dtype

        # === Create base sequence (same as original) ===
        if prev_samples is None or motion_latent_count == 0:
            padding_size = total_latents - anchor_latent.shape[1]
            padding = torch.zeros(C, padding_size, H, W, dtype=dtype, device=device)
            y = torch.concat([anchor_latent, padding], dim=1)
            is_first_generation = True
        else:
            prev_latent = prev_samples["samples"][0].clone()
            motion_latent = prev_latent[:, -motion_latent_count:]
            padding_size = total_latents - anchor_latent.shape[1] - motion_latent.shape[1]
            padding = torch.zeros(C, padding_size, H, W, dtype=dtype, device=device)
            y = torch.concat([anchor_latent, motion_latent, padding], dim=1)
            is_first_generation = False
        # ============================================

        # === Apply motion intensity (simple difference amplification) ===
        if motion_intensity > 1.0 and y.shape[1] > 1:
            print(f"\n🎯 [WanVideoSVIProEmbeds_EnhancedMotion] Applying motion intensity: {motion_intensity:.1f}")

            if is_first_generation:
                # Amplify difference between anchor and padding frames
                base_frame = y[:, 0:1]
                other_frames = y[:, 1:]
                if other_frames.shape[1] > 0:
                    diff = other_frames - base_frame.expand(-1, other_frames.shape[1], -1, -1)
                    # Simple amplification without centering
                    amplified_other = base_frame.expand(-1, other_frames.shape[1], -1, -1) + diff * motion_intensity
                    y[:, 1:] = amplified_other
                    print(f"  Applied to {other_frames.shape[1]} frames")
            else:
                # Amplify existing motion frames relative to anchor
                motion_start = anchor_latent.shape[1]
                motion_end = motion_start + motion_latent_count
                if motion_end <= y.shape[1]:
                    motion_frames = y[:, motion_start:motion_end]
                    if motion_frames.shape[1] > 0:
                        base_frame = y[:, 0:1]
                        diff = motion_frames - base_frame.expand(-1, motion_frames.shape[1], -1, -1)
                        amplified_motion = base_frame.expand(-1, motion_frames.shape[1], -1,
                                                             -1) + diff * motion_intensity
                        y[:, motion_start:motion_end] = amplified_motion
                        print(f"  Amplified {motion_frames.shape[1]} existing motion frames")
        # ===========================================================

        # === CREATE ENHANCED TEMPORAL MASK (KEY IMPROVEMENT) ===
        # Instead of anchor-only attention, use full attention with motion boost
        msk = self.create_enhanced_temporal_mask(
            num_frames, H, W, device, dtype, motion_intensity
        )
        # =====================================================

        image_embeds = {
            "image_embeds": y,
            "num_frames": num_frames,
            "lat_h": H,
            "lat_w": W,
            "mask": msk
        }

        if motion_intensity > 1.0:
            print("✅ Motion enhancement with full attention mask completed\n")
        else:
            print("✅ SVI embeds created with full attention mask\n")

        return (image_embeds,)

    def create_enhanced_temporal_mask(self, num_frames, lat_h, lat_w, device, dtype, motion_intensity):
        """Create temporal mask with full attention for motion enhancement"""
        # Base mask: allow attention to all frames (not just anchor)
        msk = torch.ones(1, num_frames, lat_h, lat_w, device=device, dtype=dtype)

        # Apply the same reshaping as original SVI
        msk = torch.concat([torch.repeat_interleave(msk[:, 0:1], repeats=4, dim=1), msk[:, 1:]], dim=1)
        msk = msk.view(1, msk.shape[1] // 4, 4, lat_h, lat_w)
        msk = msk.transpose(1, 2)[0]

        # Boost motion attention if needed
        if motion_intensity > 1.0:
            motion_boost = min(motion_intensity, 1.5)  # Safe upper limit
            # Slightly boost non-anchor frames to encourage motion attention
            msk_enhanced = msk.clone()
            if msk_enhanced.shape[0] > 1:
                msk_enhanced[1:] = msk_enhanced[1:] * motion_boost
                msk_enhanced = torch.clamp(msk_enhanced, 0.0, 2.0)
            return msk_enhanced

        return msk