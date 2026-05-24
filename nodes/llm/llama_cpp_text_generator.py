import gc
import os
import re
import tempfile
import time

import numpy as np
import torch

from PIL import Image
from llama_cpp import Llama
import folder_paths

from llama_cpp.llama_chat_format import (
    Llava15ChatHandler,
    Llava16ChatHandler,
    MiniCPMv26ChatHandler,
    Qwen3VLChatHandler,
    Qwen35ChatHandler,
)

from ...config.config_manager import ConfigManager
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import (
    LogEntry,
    log_end,
    log_start
)

# установка - сборка кастомной библиотеки
# CMAKE_ARGS="-DGGML_CUDA=on" pip install git+https://github.com/TAO71-AI/llama-cpp-python-JamePeng.git --force-reinstall --no-cache-dir


class LlamaCppTextGenerator:

    last_seed = 0

    @staticmethod
    def get_gguf_models():
        models = folder_paths.get_filename_list("LLM")

        return [
            model for model in models
            if model.lower().endswith(".gguf")
        ]

    @staticmethod
    def get_system_prompt_dir():

        extension_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", ".."))

        path = ConfigManager().get("llm.system_prompts_path",
            "data/llm_system_instruction"
        )

        prompt_dir = os.path.join(extension_root, path)
        os.makedirs( prompt_dir, exist_ok=True)

        return prompt_dir

    @classmethod
    def get_system_prompt_files(cls):
        prompt_dir = cls.get_system_prompt_dir()

        if not os.path.exists(prompt_dir):
            os.makedirs(prompt_dir, exist_ok=True)

        allowed_extensions = (".txt", ".json", ".md", ".yaml", ".yml")
        files = []

        for root, _, filenames in os.walk(prompt_dir):
            for file_name in filenames:
                if not file_name.lower().endswith(allowed_extensions):
                    continue

                full_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(full_path, prompt_dir)
                relative_path = relative_path.replace("\\", "/")
                files.append(relative_path)

        files.sort()
        return ["none"] + files

    @classmethod
    def load_system_prompt(cls, selected_file):
        if not selected_file or selected_file == "none":
            return None

        prompt_dir = cls.get_system_prompt_dir()
        full_path = os.path.join(prompt_dir, selected_file)

        if not os.path.exists(full_path):
            raise Exception(f"System prompt file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as file:
            return file.read().strip()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": (cls.get_gguf_models(), {}),
                "mmproj_path": (cls.get_gguf_models(), {}),
                "handler_type": (["auto", "qwen35", "qwen3vl", "llava15", "llava16", "minicpmv26"], {"default": "auto"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True}),
                "system_prompt_file": (cls.get_system_prompt_files(), {}),
                "system_prompt": ("STRING", {"multiline": True, "default": "You are a vision-language AI assistant."}),
                "user_prompt": ("STRING", {"multiline": True, "default": "Describe this image."}),
                "max_tokens": ("INT", {"default": 256, "min": 32, "max": 4096}),
                "temperature": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 2.0}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0}),
                "repeat_penalty": ("FLOAT", {"default": 1.1, "min": 1.0, "max": 2.0}),
                "gpu_layers": ("INT", {"default": 35, "min": 0, "max": 80}),
                "context_length": ("INT", {"default": 4096, "min": 512, "max": 32768}),
                "enable_thinking": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "run"
    CATEGORY = f"{CATEGORY_PREFIX}/LLM"

    def resolve_seed(self, seed):
        if isinstance(seed, (tuple, list)):
            seed = seed[0]
        return seed

    def detect_handler(self, model_path):
        name = os.path.basename(model_path).lower()

        if "qwen3.5" in name or "qwen35" in name:
            return "qwen35"

        if "qwen3-vl" in name or "qwen3vl" in name:
            return "qwen3vl"

        if "minicpm" in name:
            return "minicpmv26"

        if "llava-v1.6" in name or "llava16" in name:
            return "llava16"

        return "llava15"

    def tensor_to_pil(self, image):
        if image is None:
            return None

        img = image[0].cpu().numpy()
        if len(img.shape) == 4:
            img = img[0]

        if img.shape[0] in (1, 3, 4):
            img = np.transpose(img, (1, 2, 0))

        img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
        if img.shape[-1] == 4:
            img = img[:, :, :3]

        pil = Image.fromarray(img).convert("RGB")

        max_size = 1024
        if pil.width > max_size or pil.height > max_size:
            pil.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        return pil

    def clean_response(self, text):
        if not text:
            return ""

        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"</?think>", "", text)
        text = text.replace("```", "")

        return text.strip()

    def extract_response(self, output):
        try:
            msg = output["choices"][0]["message"]
            if msg.get("content"):
                return msg["content"]
            if msg.get("reasoning_content"):
                return msg["reasoning_content"]
            return str(output)
        except Exception:
            return str(output)

    def create_handler(self, handler_type, mmproj_path, enable_thinking):
        if handler_type == "qwen35":
            return Qwen35ChatHandler(clip_model_path=mmproj_path, enable_thinking=enable_thinking, verbose=False)

        if handler_type == "qwen3vl":
            return Qwen3VLChatHandler(clip_model_path=mmproj_path, verbose=False)

        if handler_type == "llava16":
            return Llava16ChatHandler(clip_model_path=mmproj_path)

        if handler_type == "llava15":
            return Llava15ChatHandler(clip_model_path=mmproj_path)

        if handler_type == "minicpmv26":
            return MiniCPMv26ChatHandler(clip_model_path=mmproj_path)

        raise Exception(f"Unsupported handler: {handler_type}")

    def build_messages(self, handler_type, system_prompt, user_prompt, image_path):
        if image_path is None:
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

        if handler_type in ["qwen35", "qwen3vl"]:
            return [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_path}},
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ]

        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_path}},
                ],
            },
        ]

    def run(
        self,
        model_path,
        mmproj_path,
        handler_type,
        system_prompt_file,
        seed,
        system_prompt,
        user_prompt,
        max_tokens,
        temperature,
        top_p,
        repeat_penalty,
        gpu_layers,
        context_length,
        enable_thinking,
        image=None,
    ):
        llm = None
        temp_file_path = None

        try:
            log_start(LogEntry(
                node_class="LlamaCppTextGenerator",
                title="START",
                details={
                    "model": model_path,
                    "mmproj": mmproj_path,
                    "handler": handler_type,
                    "system_prompt_file": system_prompt_file
                },
            ))

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            if handler_type == "auto":
                handler_type = self.detect_handler(model_path)

            seed = self.resolve_seed(seed)

            if system_prompt_file != "none":
                loaded_prompt = self.load_system_prompt(system_prompt_file)
                if loaded_prompt:
                    system_prompt = loaded_prompt

            pil = self.tensor_to_pil(image)
            image_path = None
            if pil:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp_file_path = tmp.name
                tmp.close()
                pil.save(temp_file_path, format="JPEG", quality=95)
                image_path = f"file://{temp_file_path}"

            model_full_path = folder_paths.get_full_path("LLM", model_path)
            mmproj_full_path = folder_paths.get_full_path("LLM", mmproj_path)

            handler = self.create_handler(handler_type, mmproj_full_path, enable_thinking)

            llm = Llama(
                model_path=model_full_path,
                chat_handler=handler,
                n_ctx=context_length,
                n_gpu_layers=gpu_layers,
                seed=seed,
                verbose=False,
            )

            messages = self.build_messages(handler_type, system_prompt, user_prompt, image_path)

            generation_start = time.perf_counter()
            output = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
                seed=seed,
            )
            generation_time = time.perf_counter() - generation_start

            raw = self.extract_response(output)
            result = self.clean_response(raw)

            usage = output.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            tokens_per_sec = 0
            if generation_time > 0:
                tokens_per_sec = round(completion_tokens / generation_time, 2)

            log_end(LogEntry(
                node_class="LlamaCppTextGenerator",
                title="DONE",
                details={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "out_tokens": len(result),
                    "tokens_per_sec": tokens_per_sec,
                    "time_sec": round(generation_time, 2),
                },
            ))

            return (result,)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return (f"ERROR: {str(e)}",)

        finally:
            if llm:
                del llm
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
