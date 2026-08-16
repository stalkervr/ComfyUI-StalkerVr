import sys
import json
import os
import gc

comfyui_dir = os.environ.get('COMFYUI_PATH', '')
if comfyui_dir and comfyui_dir not in sys.path:
    sys.path.insert(0, comfyui_dir)

venv_lib = os.environ.get('VENV_LIB_PATH', '')
if venv_lib and venv_lib not in sys.path:
    sys.path.insert(0, venv_lib)

from llama_cpp import Llama
from llama_cpp.llama_chat_format import (
    Llava15ChatHandler, Llava16ChatHandler, MiniCPMv26ChatHandler,
    Qwen3VLChatHandler, Qwen35ChatHandler, Gemma4ChatHandler,
)


def _build_handler(handler_cls, mmproj_path, kwargs):
    """
    Новые версии llama-cpp-python требуют mmproj_path,
    старые используют clip_model_path. Пробуем оба варианта.
    """
    try:
        return handler_cls(mmproj_path=mmproj_path, **kwargs)
    except TypeError:
        return handler_cls(clip_model_path=mmproj_path, **kwargs)


def create_handler(handler_type, mmproj_path, enable_thinking):
    # Явные проверки с понятными ошибками
    if not mmproj_path:
        raise Exception("mmproj path is empty in payload")
    if not os.path.exists(mmproj_path):
        raise Exception(f"mmproj file not found on disk: {mmproj_path}")

    if handler_type == "qwen35":
        return _build_handler(Qwen35ChatHandler, mmproj_path,
                              {"enable_thinking": enable_thinking, "verbose": False})
    if handler_type == "qwen3vl":
        return _build_handler(Qwen3VLChatHandler, mmproj_path, {"verbose": False})
    if handler_type == "llava16":
        return _build_handler(Llava16ChatHandler, mmproj_path, {})
    if handler_type == "llava15":
        return _build_handler(Llava15ChatHandler, mmproj_path, {})
    if handler_type == "minicpmv26":
        return _build_handler(MiniCPMv26ChatHandler, mmproj_path, {})
    if handler_type == "gemma4":
        return _build_handler(Gemma4ChatHandler, mmproj_path,
                              {"enable_thinking": enable_thinking, "verbose": False})
    raise Exception(f"Unsupported handler: {handler_type}")


def main():
    if len(sys.argv) < 2:
        print("Error: No payload file specified", file=sys.stderr)
        sys.exit(1)

    payload_file = sys.argv[1]

    try:
        with open(payload_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        output_file = data['output_file']

        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass

        handler = create_handler(data['handler_type'], data['mmproj_full_path'], data['enable_thinking'])

        # ДОБАВЛЕНЫ: kv_cache_type и flash_attn
        llm = Llama(
            model_path=data['model_full_path'],
            chat_handler=handler,
            n_ctx=data['context_length'],
            n_gpu_layers=data['gpu_layers'],
            seed=data['seed'],
            verbose=False,
            kv_cache_type=data.get('kv_cache_type', 'f16'),
            flash_attn=data.get('flash_attn', True),
        )

        messages = data['messages']

        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=data['max_tokens'],
            temperature=data['temperature'],
            top_p=data['top_p'],
            top_k=data['top_k'],
            min_p=data['min_p'],
            repeat_penalty=data['repeat_penalty'],
            present_penalty=data['present_penalty'],
            frequency_penalty=data['frequency_penalty'],
            seed=data['seed'],
        )

        msg = output["choices"][0]["message"]
        raw_text = msg.get("content") or msg.get("reasoning_content") or str(output)

        import re
        clean_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
        clean_text = re.sub(r"</?think>", "", clean_text)
        clean_text = clean_text.replace("```", "")
        if "<channel|>" in clean_text:
            clean_text = clean_text.split("<channel|>")[-1]
        clean_text = re.sub(r"^\s*[\*\-]\s+.*?$", "", clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r"Self-Correction:.*?$", "", clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r"\n{2,}", "\n\n", clean_text)
        clean_text = clean_text.strip()

        result_data = {
            "status": "success",
            "response": clean_text,
            "usage": output.get("usage", {})
        }

    except Exception as e:
        import traceback
        result_data = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    finally:
        if 'llm' in locals():
            try:
                del llm
            except:
                pass
        if 'handler' in locals():
            try:
                del handler
            except:
                pass
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to write output: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()