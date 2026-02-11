import sys


from .constants import (
    CATEGORY_PREFIX
)


class Everything(str):
    """Wildcard type marker."""
    def __ne__(self, __value: object) -> bool:
        return False


def _looks_like_model(x):
    return x is not None and hasattr(x, 'model') and hasattr(x.model, 'apply_model')

def _looks_like_clip(x):
    return x is not None and hasattr(x, 'encode_from_tokens')

def _looks_like_vae(x):
    return x is not None and hasattr(x, 'decode') and hasattr(x, 'encode')

def _looks_like_latent(x):
    return x is not None and isinstance(x, dict) and 'samples' in x

def _looks_like_image(x):
    return x is not None and hasattr(x, 'shape') and len(x.shape) >= 3

def _looks_like_conditioning(x):
    return x is not None and isinstance(x, list) and len(x) > 0 and isinstance(x[0], list)

def _looks_like_clip_vision_output(x):
    return x is not None and hasattr(x, 'image_embeds')


class PipeIn:
    """
    PipeIn (Safe + Logging, Custom Names)
    -------------------------------------
    Aggregates optional workflow parameters into a PIPE dict.
    Uses custom input names as shown in the screenshot.
    Validates input types and logs activity for debugging.
    """

    LOG_TAG = "[PipeIn]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "pipe": (Everything("*"),),

                # MODELS — renamed
                "high_noise": ("MODEL",),
                "high_noise_svi": ("MODEL",),
                "high_noise_light": ("MODEL",),
                "high_noise_light_svi": ("MODEL",),
                "low_noise": ("MODEL",),
                "low_noise_svi": ("MODEL",),
                "low_noise_light": ("MODEL",),
                "low_noise_light_svi": ("MODEL",),

                # CLIP & Vision
                "clip": ("CLIP",),
                "clip_vision_output": ("CLIP_VISION_OUTPUT",),

                # VAE
                "vae": ("VAE",),

                # LATENTS — renamed
                "anchor_samples": ("LATENT",),
                "prev_samples": ("LATENT",),

                # IMAGES — renamed
                "start_image": ("IMAGE",),
                "source_images": ("IMAGE",),
                "last_image": ("IMAGE",),

                # CONDITIONING — renamed
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
            }
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("pipe",)
    FUNCTION = "build_pipe"
    CATEGORY = f"{CATEGORY_PREFIX}/Pipe"
    DESCRIPTION = "Safely merges inputs into a PIPE dict with custom names and validation."

    def _log(self, msg):
        print(f"{self.LOG_TAG} {msg}", file=sys.stderr)

    def build_pipe(
        self,
        pipe=None,
        high_noise=None, high_noise_svi=None, high_noise_light=None, high_noise_light_svi=None,
        low_noise=None, low_noise_svi=None, low_noise_light=None, low_noise_light_svi=None,
        clip=None,
        clip_vision_output=None,
        vae=None,
        anchor_samples=None, prev_samples=None,
        start_image=None, source_images=None, last_image=None,
        positive=None, negative=None,
    ):
        self._log("=== Starting build_pipe ===")

        if pipe is None:
            pipe = {}
            self._log("No input pipe provided — initializing empty pipe.")
        else:
            self._log("Input pipe received.")

        result_pipe = {
            "model": list(pipe.get("model", [None] * 8)),
            "clip": pipe.get("clip", None),
            "clip_vision_output": pipe.get("clip_vision_output", None),
            "vae": pipe.get("vae", None),
            "latent": list(pipe.get("latent", [None] * 2)),
            "image": list(pipe.get("image", [None] * 3)),
            "conditioning": list(pipe.get("conditioning", [None] * 2)),
        }

        # --- Models ---
        input_models = [
            high_noise, high_noise_svi, high_noise_light, high_noise_light_svi,
            low_noise, low_noise_svi, low_noise_light, low_noise_light_svi
        ]
        for i, m in enumerate(input_models):
            if m is not None:
                if _looks_like_model(m):
                    result_pipe["model"][i] = m
                    self._log(f"✅ Accepted model_{i+1} ({['high_noise', 'high_noise_svi', 'high_noise_light', 'high_noise_light_svi', 'low_noise', 'low_noise_svi', 'low_noise_light', 'low_noise_light_svi'][i]})")
                else:
                    self._log(f"⚠️  Ignored invalid model_{i+1} (type: {type(m).__name__})")

        # --- CLIP ---
        if clip is not None:
            if _looks_like_clip(clip):
                result_pipe["clip"] = clip
                self._log("✅ Accepted clip")
            else:
                self._log(f"⚠️  Ignored invalid clip (type: {type(clip).__name__})")

        # --- CLIP Vision ---
        if clip_vision_output is not None:
            if _looks_like_clip_vision_output(clip_vision_output):
                result_pipe["clip_vision_output"] = clip_vision_output
                self._log("✅ Accepted clip_vision_output")
            else:
                self._log(f"⚠️  Ignored invalid clip_vision_output (type: {type(clip_vision_output).__name__})")

        # --- VAE ---
        if vae is not None:
            if _looks_like_vae(vae):
                result_pipe["vae"] = vae
                self._log("✅ Accepted vae")
            else:
                self._log(f"⚠️  Ignored invalid vae (type: {type(vae).__name__})")

        # --- Latents ---
        input_latents = [anchor_samples, prev_samples]
        for i, l in enumerate(input_latents):
            if l is not None:
                if _looks_like_latent(l):
                    result_pipe["latent"][i] = l
                    self._log(f"✅ Accepted latent_{i+1} ({['anchor_samples', 'prev_samples'][i]})")
                else:
                    self._log(f"⚠️  Ignored invalid latent_{i+1} (type: {type(l).__name__})")

        # --- Images ---
        input_images = [start_image, source_images, last_image]
        for i, img in enumerate(input_images):
            if img is not None:
                if _looks_like_image(img):
                    result_pipe["image"][i] = img
                    self._log(f"✅ Accepted image_{i+1} ({['start_image', 'source_images', 'last_image'][i]})")
                else:
                    self._log(f"⚠️  Ignored invalid image_{i+1} (type: {type(img).__name__})")

        # --- Conditioning ---
        input_conditionings = [positive, negative]
        for i, c in enumerate(input_conditionings):
            if c is not None:
                if _looks_like_conditioning(c):
                    result_pipe["conditioning"][i] = c
                    self._log(f"✅ Accepted conditioning_{i+1} ({['positive', 'negative'][i]})")
                else:
                    self._log(f"⚠️  Ignored invalid conditioning_{i+1} (type: {type(c).__name__})")

        self._log("=== build_pipe completed ===")
        return (result_pipe,)


class PipeOut:
    """
    PipeOut (Safe + Logging, Custom Names)
    --------------------------------------
    Extracts individual components from a PIPE dictionary into separate outputs.
    Uses custom output names as shown in the screenshot.
    Validates extracted values before outputting. Logs activity for debugging.
    """

    LOG_TAG = "[PipeOut]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "pipe": (Everything("*"),),
            }
        }

    RETURN_TYPES = (
        Everything("*"),  # pipe passthrough

        # MODELS — renamed
        "MODEL", "MODEL", "MODEL", "MODEL",
        "MODEL", "MODEL", "MODEL", "MODEL",

        # CLIP & Vision
        "CLIP",
        "CLIP_VISION_OUTPUT",

        # VAE
        "VAE",

        # LATENTS — renamed
        "LATENT", "LATENT",

        # IMAGES — renamed
        "IMAGE", "IMAGE", "IMAGE",

        # CONDITIONING — renamed
        "CONDITIONING", "CONDITIONING",
    )

    RETURN_NAMES = (
        "pipe",
        "high_noise", "high_noise_svi", "high_noise_light", "high_noise_light_svi",
        "low_noise", "low_noise_svi", "low_noise_light", "low_noise_light_svi",
        "clip",
        "clip_vision_output",
        "vae",
        "anchor_samples", "prev_samples",
        "start_image", "source_images", "last_image",
        "positive", "negative",
    )

    FUNCTION = "extract_pipe"
    CATEGORY = f"{CATEGORY_PREFIX}/Pipe"
    DESCRIPTION = "Extracts all components from a PIPE with custom names and validation."

    def _log(self, msg):
        print(f"{self.LOG_TAG} {msg}", file=sys.stderr)

    def extract_pipe(self, pipe=None):
        self._log("=== Starting extract_pipe ===")

        if pipe is None:
            pipe = {}
            self._log("No input pipe provided — initializing empty pipe.")
        else:
            self._log("Input pipe received.")

        def safe_get(lst, index, default=None):
            if lst is None:
                return default
            try:
                return lst[index]
            except (IndexError, TypeError):
                return default

        models = pipe.get("model", [])
        latents = pipe.get("latent", [])
        images = pipe.get("image", [])
        conditionings = pipe.get("conditioning", [])

        # --- Validate and extract MODELS ---
        model_names = [
            "high_noise", "high_noise_svi", "high_noise_light", "high_noise_light_svi",
            "low_noise", "low_noise_svi", "low_noise_light", "low_noise_light_svi"
        ]
        model_outputs = []
        for i in range(8):
            m = safe_get(models, i)
            if m is not None:
                if _looks_like_model(m):
                    model_outputs.append(m)
                    self._log(f"✅ Output {model_names[i]}")
                else:
                    model_outputs.append(None)
                    self._log(f"⚠️  Invalid {model_names[i]} (type: {type(m).__name__}) → set to None")
            else:
                model_outputs.append(None)
                self._log(f"ℹ️  {model_names[i]} not found → set to None")

        # --- Validate and extract CLIP ---
        clip_out = pipe.get("clip", None)
        if clip_out is not None:
            if _looks_like_clip(clip_out):
                self._log("✅ Output clip")
            else:
                clip_out = None
                self._log(f"⚠️  Invalid clip (type: {type(clip_out).__name__}) → set to None")

        # --- Validate and extract CLIP Vision ---
        clip_vision_out = pipe.get("clip_vision_output", None)
        if clip_vision_out is not None:
            if _looks_like_clip_vision_output(clip_vision_out):
                self._log("✅ Output clip_vision_output")
            else:
                clip_vision_out = None
                self._log(f"⚠️  Invalid clip_vision_output (type: {type(clip_vision_out).__name__}) → set to None")

        # --- Validate and extract VAE ---
        vae_out = pipe.get("vae", None)
        if vae_out is not None:
            if _looks_like_vae(vae_out):
                self._log("✅ Output vae")
            else:
                vae_out = None
                self._log(f"⚠️  Invalid vae (type: {type(vae_out).__name__}) → set to None")

        # --- Validate and extract LATENTS ---
        latent_names = ["anchor_samples", "prev_samples"]
        latent_outputs = []
        for i in range(2):
            l = safe_get(latents, i)
            if l is not None:
                if _looks_like_latent(l):
                    latent_outputs.append(l)
                    self._log(f"✅ Output {latent_names[i]}")
                else:
                    latent_outputs.append(None)
                    self._log(f"⚠️  Invalid {latent_names[i]} (type: {type(l).__name__}) → set to None")
            else:
                latent_outputs.append(None)
                self._log(f"ℹ️  {latent_names[i]} not found → set to None")

        # --- Validate and extract IMAGES ---
        image_names = ["start_image", "source_images", "last_image"]
        image_outputs = []
        for i in range(3):
            img = safe_get(images, i)
            if img is not None:
                if _looks_like_image(img):
                    image_outputs.append(img)
                    self._log(f"✅ Output {image_names[i]}")
                else:
                    image_outputs.append(None)
                    self._log(f"⚠️  Invalid {image_names[i]} (type: {type(img).__name__}) → set to None")
            else:
                image_outputs.append(None)
                self._log(f"ℹ️  {image_names[i]} not found → set to None")

        # --- Validate and extract CONDITIONING ---
        conditioning_names = ["positive", "negative"]
        conditioning_outputs = []
        for i in range(2):
            c = safe_get(conditionings, i)
            if c is not None:
                if _looks_like_conditioning(c):
                    conditioning_outputs.append(c)
                    self._log(f"✅ Output {conditioning_names[i]}")
                else:
                    conditioning_outputs.append(None)
                    self._log(f"⚠️  Invalid {conditioning_names[i]} (type: {type(c).__name__}) → set to None")
            else:
                conditioning_outputs.append(None)
                self._log(f"ℹ️  {conditioning_names[i]} not found → set to None")

        self._log("=== extract_pipe completed ===")

        return (
            pipe,  # passthrough

            # Models
            *model_outputs,

            # CLIP & Vision
            clip_out,
            clip_vision_out,

            # VAE
            vae_out,

            # Latents
            *latent_outputs,

            # Images
            *image_outputs,

            # Conditioning
            *conditioning_outputs,
        )