import os
import sys
import json
import tempfile
import subprocess
import shutil
import time

import numpy as np
import folder_paths
from PIL import Image

from ...config.config_manager import ConfigManager
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log, log_start, log_end


class LlamaCppTextGenerator:

    # ==================== ПУТИ МОДЕЛЕЙ (ИЗ КОНФИГУРАЦИИ) ====================
    @classmethod
    def get_models_dirs(cls):
        raw = ConfigManager().get("llm.models_path", "models/LLM")

        # Обратная совместимость: строка -> список
        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, list):
            raw = ["models/LLM"]

        comfyui_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
        )

        dirs = []
        for path in raw:
            if not isinstance(path, str) or not path.strip():
                continue
            path = path.strip()
            if os.path.isabs(path):
                models_dir = os.path.abspath(path)
            else:
                models_dir = os.path.abspath(os.path.join(comfyui_root, path))
                try:
                    os.makedirs(models_dir, exist_ok=True)
                except (PermissionError, OSError) as e:
                    print(f"[ComfyUI-StalkerVr] ⚠️ Cannot create models dir {models_dir}: {e}")
            if models_dir not in dirs:
                dirs.append(models_dir)

        return dirs

    @classmethod
    def get_model_full_path(cls, rel_path):
        """
        Разрешает относительный путь в абсолютный.
        Проходит каталоги по порядку и возвращает первый существующий файл.
        """
        for models_dir in cls.get_models_dirs():
            full = os.path.join(models_dir, rel_path)
            if os.path.exists(full):
                return full
        # Fallback: первый каталог из списка
        dirs = cls.get_models_dirs()
        return os.path.join(dirs[0], rel_path) if dirs else rel_path

    @classmethod
    def get_all_gguf_files(cls):
        """
        Рекурсивно сканирует ВСЕ каталоги моделей.
        Возвращает относительные пути всех .gguf (без дубликатов).
        """
        files = []
        for models_dir in cls.get_models_dirs():
            if not os.path.isdir(models_dir):
                continue
            for root, _, filenames in os.walk(models_dir):
                for fn in filenames:
                    if fn.lower().endswith(".gguf"):
                        rel = os.path.relpath(os.path.join(root, fn), models_dir)
                        rel = rel.replace("\\", "/")
                        if rel not in files:
                            files.append(rel)
        files.sort()
        return files

    @classmethod
    def get_gguf_models(cls):
        """Список для выпадающего меню: ТОЛЬКО основные модели (mmproj исключены)."""
        return [
            m for m in cls.get_all_gguf_files()
            if "mmproj" not in os.path.basename(m).lower()
        ]

    @classmethod
    def find_mmproj(cls, model_path):
        """Ищет mmproj в той же папке, что и основная модель."""
        full_model_path = cls.get_model_full_path(model_path)
        model_dir = os.path.dirname(full_model_path)
        model_name = os.path.basename(full_model_path).lower()

        if not os.path.isdir(model_dir):
            return None

        candidates = []
        for fn in os.listdir(model_dir):
            if not fn.lower().endswith(".gguf"):
                continue
            fn_lower = fn.lower()
            if fn_lower == model_name:
                continue
            if "mmproj" in fn_lower:
                candidates.append((0, fn))
            elif "vision" in fn_lower or "clip" in fn_lower:
                candidates.append((1, fn))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        best_file = candidates[0][1]

        # Определяем базовый каталог, в котором реально лежит основная модель
        base_dir = model_dir
        for d in cls.get_models_dirs():
            if model_dir == d or model_dir.startswith(d + os.sep):
                base_dir = d
                break

        rel_path = os.path.relpath(os.path.join(model_dir, best_file), base_dir)
        return rel_path.replace("\\", "/")
    # ==================== ПУТИ МОДЕЛЕЙ (ИЗ КОНФИГУРАЦИИ) ====================

    # ==================== СИСТЕМНЫЕ ПРОМПТЫ (ИЗ КОНФИГУРАЦИИ) ===============

    @classmethod
    def get_system_prompt_dirs(cls):
        raw = ConfigManager().get("llm.system_prompts_path", "data/llm/system_instruction")

        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, list):
            raw = ["data/llm/system_instruction"]

        extension_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        dirs = []
        for path in raw:
            if not isinstance(path, str) or not path.strip():
                continue
            path = path.strip()
            if os.path.isabs(path):
                prompt_dir = path
            else:
                prompt_dir = os.path.join(extension_root, path)
                try:
                    os.makedirs(prompt_dir, exist_ok=True)
                except (PermissionError, OSError) as e:
                    print(f"[ComfyUI-StalkerVr] ⚠️ Cannot create system prompt dir {prompt_dir}: {e}")
            if prompt_dir not in dirs:
                dirs.append(prompt_dir)

        return dirs

    @classmethod
    def get_system_prompt_full_path(cls, rel_path):
        """
        Разрешает относительный путь в абсолютный.
        Проходит каталоги по порядку и возвращает первый существующий файл.
        """
        for prompt_dir in cls.get_system_prompt_dirs():
            full = os.path.join(prompt_dir, rel_path)
            if os.path.exists(full):
                return full
        # Fallback: первый каталог из списка
        dirs = cls.get_system_prompt_dirs()
        return os.path.join(dirs[0], rel_path) if dirs else rel_path

    @classmethod
    def get_system_prompt_files(cls):
        """
        Рекурсивно сканирует ВСЕ каталоги системных промптов.
        Возвращает относительные пути всех файлов (без дубликатов).
        Приоритет: первый каталог в списке.
        """
        allowed_extensions = (".txt", ".json", ".md", ".yaml", ".yml")
        files = []
        for prompt_dir in cls.get_system_prompt_dirs():
            if not os.path.isdir(prompt_dir):
                continue
            for root, _, filenames in os.walk(prompt_dir):
                for file_name in filenames:
                    if file_name.lower().endswith(allowed_extensions):
                        rel_path = os.path.relpath(os.path.join(root, file_name), prompt_dir)
                        rel_path = rel_path.replace("\\", "/")
                        if rel_path not in files:
                            files.append(rel_path)
        files.sort()
        return ["none"] + files

    @classmethod
    def load_system_prompt(cls, selected_file):
        if not selected_file or selected_file == "none":
            return None
        full_path = cls.get_system_prompt_full_path(selected_file)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        return None

    # ==================== СИСТЕМНЫЕ ПРОМПТЫ (ИЗ КОНФИГУРАЦИИ) ====================

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": (cls.get_gguf_models(), {
                    "tooltip": "Main model. The mmproj (vision) file is auto-detected from the same folder."}),
                "enable_thinking": ("BOOLEAN", {"default": False}),
                "handler_type": (["auto", "qwen35", "qwen3vl", "gemma4", "llava15", "llava16", "minicpmv26"], {"default": "auto"}),
                "max_tokens": ("INT", {"default": 8192, "min": 32, "max": 16384, "step": 32}),
                "context_length": ("INT", {"default": 32768, "min": 512, "max": 65536, "step": 32,
                                           "tooltip": "Lower this if you experience crashes with partial GPU layers."}),
                "gpu_layers": ("INT", {"default": -1, "min": -1, "max": 200,
                                       "tooltip": "-1 = All GPU, 0 = CPU. Partial values may cause CUDA errors with Gemma SWA cache."}),
                "kv_cache_type": (["f16", "q8_0", "q4_0"], {"default": "q8_0",
                                                            "tooltip": "Quantize KV cache to save VRAM. 'q8_0' is highly recommended for Gemma to prevent CUDA crashes."}),
                "flash_attn": ("BOOLEAN", {"default": True,
                                           "tooltip": "Enable Flash Attention. Changes memory layout and often bypasses SWA cache bugs."}),
                "temperature": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 2.0, "step": 0.01}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "top_k": ("INT", {"default": 40, "min": 0, "max": 200}),
                "min_p": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "repeat_penalty": ("FLOAT", {"default": 1.1, "min": 1.0, "max": 2.0, "step": 0.01}),
                "present_penalty": ("FLOAT", {"default": 0.0, "min": -2.0, "max": 2.0, "step": 0.01}),
                "frequency_penalty": ("FLOAT", {"default": 0.0, "min": -2.0, "max": 2.0, "step": 0.01}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True}),
                "system_prompt_file": (cls.get_system_prompt_files(), {}),
                "system_prompt": ("STRING", {"multiline": True,
                                             "default": ""}),
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("response", "metadata")
    FUNCTION = "run"
    CATEGORY = f"{CATEGORY_PREFIX}/LLM"

    @staticmethod
    def _build_metadata(instructions, request, response):
        data = {
            "instructions": instructions or "",
            "request": request or "",
            "response": response or "",
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

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
        if pil.width > 1024 or pil.height > 1024:
            pil.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        return pil

    def detect_handler(self, model_path):
        name = os.path.basename(model_path).lower()
        if "qwen3.5" in name or "qwen35" in name: return "qwen35"
        if "qwen3-vl" in name or "qwen3vl" in name: return "qwen3vl"
        if "minicpm" in name: return "minicpmv26"
        if "llava-v1.6" in name or "llava16" in name: return "llava16"
        if "gemma4" in name or "gemma-4" in name: return "gemma4"
        return "llava15"

    def run(self, model_path, handler_type, system_prompt_file, seed,
            system_prompt, user_prompt, max_tokens, temperature, top_p, top_k, min_p,
            repeat_penalty, present_penalty, frequency_penalty, gpu_layers, context_length,
            kv_cache_type, flash_attn, enable_thinking, image=None):

        temp_dir = None
        start_time = time.perf_counter()
        original_user_prompt = user_prompt

        try:
            # АВТОПОИСК MMPROJ в папке основной модели
            mmproj_path = self.find_mmproj(model_path)

            # Определяем реальный хендлер ДО логирования
            selected_handler = handler_type
            if handler_type == "auto":
                handler_type = self.detect_handler(model_path)

            log_start(LogEntry(
                node_class="LlamaCppTextGenerator",
                title="START",
                details={
                    "model": model_path,
                    "mmproj": mmproj_path if mmproj_path else "NOT FOUND (text-only mode)",
                    "handler": selected_handler,
                    "used_handler": handler_type,
                    "system_prompt_file": system_prompt_file,
                    "gpu_layers": gpu_layers,
                    "kv_cache": kv_cache_type,
                    "flash_attn": flash_attn
                }
            ))

            if system_prompt_file != "none":
                loaded = self.load_system_prompt(system_prompt_file)
                if loaded:
                    system_prompt = loaded

            image_path = None
            pil = self.tensor_to_pil(image)

            temp_dir = tempfile.mkdtemp()
            payload_path = os.path.join(temp_dir, "payload.json")
            output_path = os.path.join(temp_dir, "output.json")
            img_temp_path = os.path.join(temp_dir, "input.jpg")

            if pil:
                pil.save(img_temp_path, format="JPEG", quality=95)
                image_path = f"file://{img_temp_path}"

            # Если есть изображение, но mmproj не найден - предупреждаем
            if image_path and not mmproj_path:
                log(LogEntry(
                    node_class="LlamaCppTextGenerator",
                    title="Warning",
                    details={"Reason": "Image provided but no mmproj found in model folder. Image will be ignored."}
                ))
                image_path = None

            if image_path is None:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            elif handler_type in ["qwen35", "qwen3vl"]:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_path}},
                                                 {"type": "text", "text": user_prompt}]},
                ]
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [{"type": "text", "text": user_prompt},
                                                 {"type": "image_url", "image_url": {"url": image_path}}]},
                ]

            payload = {
                "output_file": output_path,
                "model_full_path": self.get_model_full_path(model_path),
                "mmproj_full_path": self.get_model_full_path(mmproj_path) if mmproj_path else None,
                "handler_type": handler_type,
                "enable_thinking": enable_thinking,
                "context_length": context_length,
                "gpu_layers": gpu_layers,
                "kv_cache_type": kv_cache_type,
                "flash_attn": flash_attn,
                "seed": int(seed[0] if isinstance(seed, (list, tuple)) else seed),
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "min_p": min_p,
                "repeat_penalty": repeat_penalty,
                "present_penalty": present_penalty,
                "frequency_penalty": frequency_penalty,
            }

            with open(payload_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False)

            worker_script = os.path.join(os.path.dirname(__file__), "llama_cpp_worker.py")
            python_executable = sys.executable

            env = os.environ.copy()
            comfyui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
            venv_lib = os.path.join(comfyui_root, ".venv", "lib", "python3.11", "site-packages")

            env['COMFYUI_PATH'] = comfyui_root
            env['VENV_LIB_PATH'] = venv_lib
            pythonpath = env.get('PYTHONPATH', '')
            env['PYTHONPATH'] = f"{comfyui_root}:{venv_lib}:{pythonpath}" if pythonpath else f"{comfyui_root}:{venv_lib}"

            result = subprocess.run(
                [python_executable, worker_script, payload_path],
                capture_output=True,
                text=True,
                timeout=600,
                env=env
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                error_lines = [line for line in error_msg.split('\n')
                               if line.strip() and 'Warning' not in line and 'FutureWarning' not in line]
                clean_error = '\n'.join(error_lines) if error_lines else "Unknown error"

                log(LogEntry(
                    node_class="LlamaCppTextGenerator",
                    title="SUBPROCESS CRASHED",
                    details={"Return Code": result.returncode, "Error": clean_error[:500]},
                    footer="Try setting kv_cache_type to 'q8_0' or 'q4_0', or reduce the number of layers gpu_layers."
                ))

                error_response = f"❌ LLM Process Crashed (CUDA/SWA Cache Error).\n\nDetails: {clean_error[:400]}"
                return (
                    error_response,
                    self._build_metadata(system_prompt, original_user_prompt, error_response)
                )

            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    response_data = json.load(f)

                if response_data.get("status") == "success":
                    clean_text = response_data["response"]
                    usage = response_data.get("usage", {})

                    end_time = time.perf_counter()
                    generation_time = end_time - start_time

                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    out_tokens = len(clean_text)
                    tokens_per_sec = round(completion_tokens / generation_time, 2) if generation_time > 0 else 0.0

                    log_end(LogEntry(
                        node_class="LlamaCppTextGenerator",
                        title="DONE",
                        details={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "out_tokens": out_tokens,
                            "tokens_per_sec": tokens_per_sec,
                            "time_sec": round(generation_time, 2)
                        }
                    ))

                    return (
                        clean_text,
                        self._build_metadata(system_prompt, original_user_prompt, clean_text)
                    )
                else:
                    error = response_data.get("error", "Unknown error")
                    log(LogEntry(
                        node_class="LlamaCppTextGenerator",
                        title="LLM Error",
                        details={"Error": error},
                        footer="Check console for details."
                    ))
                    error_response = f"❌ LLM Error: {error}"
                    return (
                        error_response,
                        self._build_metadata(system_prompt, original_user_prompt, error_response)
                    )
            else:
                error_response = "❌ LLM Subprocess failed to produce an output file."
                return (
                    error_response,
                    self._build_metadata(system_prompt, original_user_prompt, error_response)
                )

        except subprocess.TimeoutExpired:
            error_response = "❌ LLM Generation Timed Out (10 minutes)."
            return (
                error_response,
                self._build_metadata(system_prompt, original_user_prompt, error_response)
            )
        except Exception as e:
            error_response = f"❌ Critical Node Error: {str(e)}"
            return (
                error_response,
                self._build_metadata(system_prompt, original_user_prompt, error_response)
            )
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass