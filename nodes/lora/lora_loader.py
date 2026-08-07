import os
import folder_paths
import comfy.utils
import comfy.sd
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log, log_end, log_start

# Специальный тип для передачи LoRA вместе с параметрами
# В ComfyUI можно использовать любой строковый идентификатор как тип
LORA_CONTAINER_TYPE = "LORA_CONTAINER"


class LoraSelect:
    """
    Selects a LoRA file and packs it with its strength parameter into a container object.
    Supports chaining via prev_lora input to build sequences of adapters.
    Pure container builder — no logging or name string handling.
    """

    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(cls):
        file_list = folder_paths.get_filename_list("loras")
        display_list = ["None"] + file_list

        return {
            "required": {},
            "optional": {
                "prev_lora": (LORA_CONTAINER_TYPE,),
                "lora_name": (display_list, {"default": "None"}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "enable_lora": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = (LORA_CONTAINER_TYPE,)
    RETURN_NAMES = ("lora",)
    FUNCTION = "select"
    CATEGORY = f"{CATEGORY_PREFIX}/Loaders"
    DESCRIPTION = """
    Selects a LoRA file and packs it with its strength parameter into a container object.
    Supports chaining via prev_lora input to build sequences of adapters.
    Pure container builder — no logging or name string handling.
    """

    # @classmethod
    # def IS_CHANGED(cls, **kwargs):
    #     return float("nan")

    def select(self, prev_lora=None, lora_name="None",
               strength_model=1.0, enable_lora=True):

        # Начинаем со списка из предыдущей цепочки или пустого
        lora_chain = list(prev_lora) if prev_lora else []

        if enable_lora and lora_name != "None" and lora_name != "":
            try:
                lora_path = folder_paths.get_full_path("loras", lora_name)

                # Кэширование файла
                lora_data = None
                if self.loaded_lora is not None and self.loaded_lora[0] == lora_path:
                    lora_data = self.loaded_lora[1]
                else:
                    self.loaded_lora = None

                if lora_data is None:
                    lora_data = comfy.utils.load_torch_file(lora_path, safe_load=True)
                    self.loaded_lora = (lora_path, lora_data)

                # Упаковываем: (path, tensor, strength, display_name)
                container_item = {
                    "path": lora_path,
                    "data": lora_data,
                    "strength": strength_model,
                    "name": lora_name + " | " + f"{strength_model:.2f}"
                }
                lora_chain.append(container_item)

            except Exception:
                # Тихо пропускаем ошибки загрузки, чтобы не ломать цепочку
                pass

        return (lora_chain,)


class LoraSelectBatch:
    """
    Batch LoRA selector with 5 independent slots.
    Each slot has its own name, strength, and enable toggle.
    All selected LoRAs are packed into a single container chain.
    Fully compatible with LoraSelect chaining via prev_lora.
    Pure container builder — no logging or name string handling.
    """

    def __init__(self):
        self.loaded_loras = {}

    @classmethod
    def INPUT_TYPES(cls):
        file_list = folder_paths.get_filename_list("loras")
        display_list = ["None"] + file_list

        inputs = {
            "required": {},
            "optional": {
                "prev_lora": (LORA_CONTAINER_TYPE,),
            }
        }

        # Генерируем 5 идентичных наборов полей
        for i in range(1, 6):
            inputs["optional"][f"lora_{i}_name"] = (display_list, {"default": "None"})
            inputs["optional"][f"lora_{i}_strength"] = ("FLOAT", {
                "default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01
            })
            inputs["optional"][f"lora_{i}_enable"] = ("BOOLEAN", {"default": True})

        return inputs

    RETURN_TYPES = (LORA_CONTAINER_TYPE,)
    RETURN_NAMES = ("lora",)
    FUNCTION = "select_batch"
    CATEGORY = f"{CATEGORY_PREFIX}/Loaders"
    DESCRIPTION = """
    Selects up to 5 LoRAs in a single node. Each slot operates independently
    with its own name, strength, and enable toggle. Results are merged into
    one container chain compatible with LoraApply.
    Pure container builder — no logging or name string handling.
    """

    # @classmethod
    # def IS_CHANGED(cls, **kwargs):
    #     return float("nan")

    def _load_single_lora(self, lora_name, strength):
        """Вспомогательный метод загрузки одной LoRA с кэшированием."""
        if not lora_name or lora_name == "None":
            return None

        try:
            lora_path = folder_paths.get_full_path("loras", lora_name)

            # Индивидуальное кэширование по пути файла
            cache_key = lora_path
            if cache_key in self.loaded_loras:
                lora_data = self.loaded_loras[cache_key]
            else:
                lora_data = comfy.utils.load_torch_file(lora_path, safe_load=True)
                self.loaded_loras[cache_key] = lora_data

            return {
                "path": lora_path,
                "data": lora_data,
                "strength": strength,
                "name": f"{lora_name} | {strength:.2f}"
            }
        except Exception:
            # Тихо пропускаем ошибки загрузки, чтобы не ломать цепочку
            return None

    def select_batch(self, prev_lora=None,
                     lora_1_name="None", lora_1_strength=1.0, lora_1_enable=True,
                     lora_2_name="None", lora_2_strength=1.0, lora_2_enable=True,
                     lora_3_name="None", lora_3_strength=1.0, lora_3_enable=True,
                     lora_4_name="None", lora_4_strength=1.0, lora_4_enable=True,
                     lora_5_name="None", lora_5_strength=1.0, lora_5_enable=True):

        # Начинаем с предыдущей цепочки
        lora_chain = list(prev_lora) if prev_lora else []

        # Собираем все 5 слотов в список для итерации
        slots = [
            (lora_1_name, lora_1_strength, lora_1_enable),
            (lora_2_name, lora_2_strength, lora_2_enable),
            (lora_3_name, lora_3_strength, lora_3_enable),
            (lora_4_name, lora_4_strength, lora_4_enable),
            (lora_5_name, lora_5_strength, lora_5_enable),
        ]

        for name, strength, enabled in slots:
            if not enabled or name == "None" or name == "":
                continue

            item = self._load_single_lora(name, strength)
            if item is not None:
                lora_chain.append(item)

        return (lora_chain,)


class LoraApply:
    """
    Applies a chain of pre-configured LoRA containers to Model/CLIP.
    Pure technical node: takes base model and full LoRA container, returns patched model.
    No name string handling — that is the responsibility of LoraSelect.
    """

    _base_model = None
    _base_clip = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora": ("LORA_CONTAINER",),
            }
        }

    # Добавляем третий выход типа * (Wildcard) для передачи списка строк как объекта
    RETURN_TYPES = ("MODEL", "CLIP", "*")
    RETURN_NAMES = ("MODEL", "CLIP", "applied_loras")
    FUNCTION = "apply"
    CATEGORY = f"{CATEGORY_PREFIX}/Loaders"
    DESCRIPTION = """
    Applies a chain of pre-configured LoRA containers to Model/CLIP.
    Pure technical node: takes base model and full LoRA container, returns patched model.
    No name string handling — that is the responsibility of LoraSelect.
    """

    # @classmethod
    # def IS_CHANGED(cls, **kwargs):
    #     return float("nan")

    def apply(self, model=None, clip=None, lora=None):
        # Обновляем базу только при наличии явного входа
        if model is not None:
            LoraApply._base_model = model
        if clip is not None:
            LoraApply._base_clip = clip

        active_model = LoraApply._base_model
        active_clip = LoraApply._base_clip

        # Инициализируем пустой список для имен
        applied_loras_list = []

        if active_model is None or active_clip is None:
            log_start(LogEntry(
                node_class="LoraApply",
                title="START",
                details={"Status": "Waiting for base model/clip"}
            ))
            log_end(LogEntry(
                node_class="LoraApply",
                title="DONE",
                details={"Status": "No base model or clip available yet"}
            ))
            return (active_model, active_clip, applied_loras_list)

        current_model = active_model
        current_clip = active_clip

        # START логирование
        log_start(LogEntry(
            node_class="LoraApply",
            title="START",
            details={
                "Total LoRAs to apply": len(lora) if lora else 0
            }
        ))

        if lora:
            try:
                # Словарь для детального логирования
                log_details = {}

                for idx, item in enumerate(lora, 1):
                    # item["name"] уже содержит формат "filename.safetensors | 1.25"
                    log_details[f"LoRA {idx}"] = item["name"]

                    # Добавляем имя в список для вывода
                    applied_loras_list.append(item["name"])

                    # Применяем LoRA к модели и клипу
                    current_model, current_clip = comfy.sd.load_lora_for_models(
                        current_model, current_clip,
                        item["data"], item["strength"], item["strength"]
                    )

                # END логирование с деталями
                log_details["Status"] = "Successfully applied"
                log_end(LogEntry(
                    node_class="LoraApply",
                    title="DONE",
                    details=log_details
                ))

            except Exception as e:
                log_end(LogEntry(
                    node_class="LoraApply",
                    title="DONE",
                    details={"Status": "Failed", "Error": str(e)}
                ))
                return (active_model, active_clip, applied_loras_list)
        else:
            log_end(LogEntry(
                node_class="LoraApply",
                title="DONE",
                details={"Status": "No LoRA container provided"}
            ))

        return (current_model, current_clip, applied_loras_list)


class LoraApplyModelOnly:
    """
    Applies a chain of pre-configured LoRA containers to MODEL only.
    Pure technical node: takes base model and full LoRA container, returns patched model.
    Does not touch or require CLIP. Uses internal caching to prevent duplicate application.
    """

    _base_model = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "model": ("MODEL",),
                "lora": ("LORA_CONTAINER",),
            }
        }

    # Добавляем второй выход типа * (Wildcard) для передачи списка строк как объекта
    RETURN_TYPES = ("MODEL", "*")
    RETURN_NAMES = ("MODEL", "applied_loras")
    FUNCTION = "apply"
    CATEGORY = f"{CATEGORY_PREFIX}/Loaders"
    DESCRIPTION = """
    Applies LoRA containers to MODEL only without affecting CLIP.
    Ideal for workflows where text encoder modifications are handled separately
    or when using models that do not rely on standard CLIP conditioning.
    """

    # @classmethod
    # def IS_CHANGED(cls, **kwargs):
    #     return float("nan")

    def apply(self, model=None, lora=None):
        # Обновляем базу только при наличии явного входа
        if model is not None:
            LoraApplyModelOnly._base_model = model

        active_model = LoraApplyModelOnly._base_model

        # Инициализируем пустой список для имен
        applied_loras_list = []

        if active_model is None:
            log_start(LogEntry(
                node_class="LoraApplyModelOnly",
                title="START",
                details={"Status": "Waiting for base model"}
            ))
            log_end(LogEntry(
                node_class="LoraApplyModelOnly",
                title="DONE",
                details={"Status": "No base model available yet"}
            ))
            return (active_model, applied_loras_list)

        current_model = active_model

        # START логирование
        log_start(LogEntry(
            node_class="LoraApplyModelOnly",
            title="START",
            details={
                "Total LoRAs to apply": len(lora) if lora else 0
            }
        ))

        if lora:
            try:
                # Словарь для детального логирования
                log_details = {}

                for idx, item in enumerate(lora, 1):
                    # item["name"] уже содержит формат "filename.safetensors | 1.25"
                    log_details[f"LoRA {idx}"] = item["name"]

                    # Добавляем имя в список для вывода
                    applied_loras_list.append(item["name"])

                    # Применяем LoRA только к модели, передавая None вместо clip
                    current_model = comfy.sd.load_lora_for_models(
                        current_model, None,
                        item["data"], item["strength"], item["strength"]
                    )[0]  # Берем только первый элемент кортежа (model)

                # END логирование с деталями
                log_details["Status"] = "Successfully applied"
                log_end(LogEntry(
                    node_class="LoraApplyModelOnly",
                    title="DONE",
                    details=log_details
                ))

            except Exception as e:
                log_end(LogEntry(
                    node_class="LoraApplyModelOnly",
                    title="DONE",
                    details={"Status": "Failed", "Error": str(e)}
                ))
                return (active_model, applied_loras_list)
        else:
            log_end(LogEntry(
                node_class="LoraApplyModelOnly",
                title="DONE",
                details={"Status": "No LoRA container provided"}
            ))

        return (current_model, applied_loras_list)