# 🎬 Управление камерой в Wan 2.2 Image-to-Video: Полное руководство

> **Дата обновления:** Март 2026  
> **Модель:** Wan 2.2 (14B) Image-to-Video  
> **Источники:** Официальная документация, Civitai, HuggingFace, сообщество

---

## 📋 Основные типы движений камеры

Wan 2.2 поддерживает следующие виды движений камеры:

| Тип движения | Описание | Пример промта |
|-------------|---------|---------------|
| Pan Left/Right | Горизонтальное движение влево/вправо | camera pans slowly to the right |
| Tilt Up/Down | Вертикальное движение вверх/вниз | camera tilts up to reveal the sky |
| Dolly In/Out | Приближение/удаление камеры | slow dolly in on subject's face |
| Zoom In/Out | Оптическое приближение/удаление | gradual zoom out to wide shot |
| Tracking Shot | Слежение за объектом | camera tracks behind the runner |
| Orbital/Arc Shot | Круговое движение вокруг объекта | 360 orbital shot around character |
| Crane Up/Down | Подъём/спуск камеры (кран) | crane shot rising above the scene |
| Static Shot | Статичная камера | static shot, locked-off camera |

---

## 🏗️ Структура промта для Wan 2.2 I2V

### Формула для Image-to-Video

Prompt = Motion Description + Camera Movement

Поскольку исходное изображение уже определяет субъект, сцену и стиль, промт должен фокусироваться на движении и поведении камеры.

### 4-частная структура промта

| Элемент | Что включать | Хороший пример |
|---------|-------------|----------------|
| Motion Description | Основное действие/движение | The woman slowly turns her head to the left |
| Camera Behavior | Движение камеры | Slow push-in on subject's face, shallow depth of field |
| Environmental Effects | Свет, погода, атмосфера | Sunlight flickering through leaves |
| Speed & Intensity | Темп и интенсивность | Gentle breeze, slow pacing |

---

## 📝 Примеры промтов от разработчиков и сообщества

### Базовые примеры

Пример 1 - Портрет с приближением:
"The white dragon warrior stands still, eyes full of determination. The camera slowly moves closer, highlighting the powerful presence."

Пример 2 - Пейзаж с панорамированием:
"A wide-angle shot of a misty Scottish glen at dawn. The camera slowly pans right, revealing rolling hills and ancient stone circle."

Пример 3 - Орбитальное движение:
"The dancer spins gracefully in place, camera orbiting clockwise, stage lights creating dramatic shadows, smooth fluid motion."

### Продвинутые кинематографичные промты

Пример 4 - Комбинированное движение:
"Extreme close-up of a mountaineer's ice axe biting into frozen rock. Camera dollies back and tilts up simultaneously, revealing the climber and vast sunrise-lit alpine ridge. Golden rim-light, crisp morning air."

Пример 5 - Pull-back (отъезд):
"Close-up of an arctic explorer's face. Camera pulls back to reveal a lone explorer standing in whiteout blizzard. Pull back further to reveal nothing but endless ice in every direction."

Пример 6 - Tracking shot:
"A dense ancient forest in morning mist. Camera tracks behind an elf in green robes sprinting through underbrush, bow in hand. Shafts of sunlight pierce through canopy above."

---

## 🔧 LoRA для управления камерой (Civitai/HuggingFace)

### Специализированные Camera Control LoRA

| LoRA | Описание | Сила (рекомендуемая) |
|------|---------|---------------------|
| wan22-camera-arcshot-rank16 | Дуга/орбита вокруг объекта | 0.6-0.8 |
| wan22-camera-drone-rank16 | Дрон-съёмка, вид сверху | 0.6-0.8 |
| wan22-camera-earthzoomout | Dramatic zoom-out (как из космоса) | 0.7-0.9 |
| wan22-camera-rotation-rank16 | Круговое вращение | 0.6-0.8 |
| wan22-camera-push-in | Push-in движение | 0.7-0.8 |
| crash-zoom-in/out | Быстрый зум (эффект удара) | 0.8-1.0 |
| 360-orbit | Полная 360 орбита | 0.7-0.9 |
| crane-down | Кран-съёмка вниз | 0.6-0.8 |

### Использование LoRA в промте (Python/Diffusers)

pipe.load_lora_weights(
    "path/to/loras",
    weight_name="wan22-camera-arcshot-rank16-i2v-a14b-high.safetensors",
    adapter_name="camera_arcshot"
)
pipe.set_adapters(["camera_arcshot"], adapter_weights=[0.75])

prompt = "Cinematic arc shot around person, dramatic lighting"

ВАЖНО: Используйте одну Camera LoRA за раз для стабильного движения.

---

## ⚙️ ComfyUI Wan2.2 Fun Camera Control

### WanCameraEmbedding Node

| Параметр | Значения |
|---------|---------|
| Camera Motion | Zoom In, Zoom Out, Pan Up, Pan Down, Pan Left, Pan Right, Static |
| Width/Height | Разрешение (например, 640x640, 720x944) |
| Length | Количество кадров (по умолчанию 81) |
| Speed | Скорость (по умолчанию 1.0) |

### Рабочий процесс

1. Загрузите модель wan2.2_fun_camera_high_noise_14B_fp8_scaled.safetensors
2. Подключите LoRA (опционально для ускорения)
3. В узле WanCameraEmbedding выберите тип движения камеры
4. Загрузите исходное изображение
5. Напишите промт с описанием движения
6. Запустите генерацию

---

## 🎯 Рекомендации разработчиков

### Что работает хорошо

- Естественные движения — волосы, ткань, вода
- Медленные зумы и панорамы — кинематографичный вид
- Статичные кадры — используйте static shot или locked-off camera
- Короткие клипы — до 5 секунд, до 120 кадров

### Чего избегать

- Противоречивые инструкции — не смешивайте противоположные движения
- Слишком быстрые движения — может вызвать размытие
- Несоответствие изображению — описывайте только видимые элементы
- Сложные взаимодействия — несколько объектов с координацией

### Негативные промты

morphing, warping, distortion, blurry, low quality, face deformation, flickering, jittering, sudden changes, inconsistent lighting

---

## 📊 Сравнение Wan 2.1 vs Wan 2.2 для камеры

| Функция | Wan 2.1 | Wan 2.2 |
|---------|---------|---------|
| Точность камеры | Средняя | Высокая |
| Поддержка LoRA | Ограниченная | Полная |
| Сложные движения | Часто ломается | Стабильно |
| ComfyUI интеграция | Базовая | Native Camera Node |
| MoE архитектура | Нет | Да (лучше детали) |

---

## 🚀 Быстрые шаблоны промтов

Шаблон 1 - Портрет:
[Subject] remains still with subtle breathing, camera slowly dollies in, soft natural lighting, slow pacing

Шаблон 2 - Пейзаж:
Camera pans left across [landscape], revealing [detail], golden hour lighting, smooth cinematic motion

Шаблон 3 - Экшен:
[Subject] [action], camera tracks alongside, dynamic lighting, moderate to fast speed

Шаблон 4 - Статичный:
Static shot, locked-off camera, subtle environmental movement only, calm atmosphere

---

## 💡 Итоговые советы

1. Начинайте просто — одно движение камеры за раз
2. Используйте конкретные глаголы — pans, zooms, tracks, а не cinematic
3. Тестируйте на низком разрешении — 512x880 для проверки промта
4. Комбинируйте LoRA осторожно — камера + свет ок, две камеры — нет
5. Повышайте разрешение постепенно — 720x1024 для финала

---

## 🔗 Полезные ресурсы

| Ресурс | Описание |
|--------|---------|
| Civitai Video Guide | https://education.civitai.com/civitais-guide-to-video-gen-prompting/ |
| ComfyUI Wan2.2 Docs | https://docs.comfy.org/tutorials/video/wan/wan2-2-fun-camera |
| HuggingFace LoRA Collection | https://huggingface.co/wangkanai/wan22-fp8-i2v-loras |
| Fal.ai Wan 2.2 | https://fal.ai/models/fal-ai/wan/v2.2-a14b/image-to-video |

---

## 📌 Глоссарий терминов

| Термин | Значение |
|--------|---------|
| Dolly | Физическое перемещение камеры вперёд/назад |
| Zoom | Оптическое приближение/удаление (изменение фокусного) |
| Pan | Горизонтальное вращение камеры на штативе |
| Tilt | Вертикальное вращение камеры на штативе |
| Tracking | Камера движется параллельно объекту |
| Crane | Камера поднимается/опускается на кране |
| Orbital | Камера вращается вокруг объекта по кругу |
| Static | Камера зафиксирована, без движения |

---

## 🎬 Дополнительные техники промтинга

### Комбинирование движений камеры

Примеры сложных движений:

1. Dolly + Tilt: "Camera dollies back while tilting up, revealing the full scale of the cathedral"

2. Pan + Zoom: "Slow pan right with subtle zoom out, creating vertigo effect"

3. Track + Arc: "Camera tracks forward while arcing left around the subject"

### Контроль скорости движения

| Скорость | Ключевые слова | Использование |
|----------|---------------|---------------|
| Очень медленно | slow, gradual, subtle | Портреты, эмоции |
| Медленно | slowly, gentle, smooth | Пейзажи, атмосфера |
| Умеренно | moderate, steady | Диалоги, экшен |
| Быстро | fast, rapid, quick | Экшен, переходы |
| Очень быстро | crash, snap, whip | Эффекты, удары |

### Работа с освещением в движении

- "Camera pushes in as light fades"
- "Pan across scene with changing golden hour light"
- "Tracking shot with flickering neon signs"
- "Orbital shot with dynamic volumetric lighting"

---

## ⚠️ Частые ошибки и решения

| Проблема | Причина | Решение |
|----------|---------|---------|
| Дрожание камеры | Слишком быстрое движение | Добавьте "smooth, stable" в промт |
| Искажение лица | Слишком сильный зум | Уменьшите силу LoRA до 0.5-0.6 |
| Несоответствие движению | Противоречивые инструкции | Используйте одно движение за раз |
| Размытие | Высокая скорость | Добавьте "sharp, clear" в промт |
| Мерцание | Нестабильная генерация | Увеличьте steps до 50+ |

---

## 📁 Структура файлов для проекта

wan22-camera-project/
├── models/
│   └── wan2.2_fun_camera_high_noise_14B_fp8_scaled.safetensors
├── loras/
│   ├── wan22-camera-arcshot-rank16.safetensors
│   ├── wan22-camera-push-in.safetensors
│   └── wan22-camera-earthzoomout.safetensors
├── inputs/
│   └── source_images/
├── outputs/
│   └── generated_videos/
├── workflows/
│   └── comfyui_camera_control.json
└── wan22-camera-guide.md (этот файл)

---

Документ подготовлен для быстрого использования при работе с Wan 2.2 Image-to-Video
Автор: AI Assistant | Версия: 1.0 | Март 2026