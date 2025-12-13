import { app } from "/scripts/app.js";

// Имя ноды, которую мы хотим модифицировать (должно совпадать с именем Python-класса)
const nodeName = "StringBuilder";

app.registerExtension({
    name: "Stalkervr.StringBuilder", // Уникальное имя расширения
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Проверяем, что это нужная нам нода
        if (nodeData.name === nodeName) {
            // Сохраняем оригинальный метод onNodeCreated
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

            // Переопределяем метод onNodeCreated для модификации экземпляра ноды
            nodeType.prototype.onNodeCreated = function() {
                // Вызываем оригинальный метод, если он существует
                if (originalOnNodeCreated) {
                    originalOnNodeCreated.apply(this, arguments);
                }

                console.log(`[${nodeName}] Node instance created.`);

                // --- Инициализация и установка логики ---
                // Мы используем setTimeout, чтобы убедиться, что this.widgets и this.inputs
                // полностью инициализированы ComfyUI перед тем, как мы начнем их модифицировать.
                setTimeout(() => {
                    this.initDynamicInputs();
                }, 50); // Небольшая задержка 50мс
            };

            // Добавляем метод к прототипу для удобства инициализации
            nodeType.prototype.initDynamicInputs = function() {
                const nodeName = "StringBuilder";
                console.log(`[${nodeName}] Initializing dynamic input logic.`);

                // Ищем виджет, управляющий количеством входов (num_inputs)
                const numInputsWidget = this.widgets.find(w => w.name === "num_inputs");

                if (numInputsWidget) {
                    // Добавляем кнопку "Update inputs"
                    const updateButton = this.addWidget("button", "Update inputs", false, () => {
                        console.log(`[${nodeName}] Update inputs button clicked.`);
                        // Вызываем функцию обновления входов
                        this.updateDynamicInputs();
                    }, { property: "update_button" });

                    // Инициализируем входы при создании ноды на основе начального значения num_inputs
                    this.updateDynamicInputs();
                } else {
                    console.warn(`[${nodeName}] Widget 'num_inputs' not found during initDynamicInputs.`);
                }
            };

            // Добавляем метод к прототипу для обновления входов
            nodeType.prototype.updateDynamicInputs = function() {
                const nodeName = "StringBuilder";
                console.log(`[${nodeName}] Updating inputs.`);

                // Получаем значение num_inputs
                const numInputsWidget = this.widgets.find(w => w.name === "num_inputs");
                if (!numInputsWidget) {
                    console.warn(`[${nodeName}] Widget 'num_inputs' not found during updateDynamicInputs.`);
                    return;
                }

                const newNumInputs = Math.max(0, Math.min(20, numInputsWidget.value));

                // --- ЛОГИКА ЧАСТИЧНОГО ОБНОВЛЕНИЯ (с нумерацией с 1) ---
                // 1. Определяем текущее количество динамических входов
                // Фильтруем по именам, начинающимся с 'string_', и у которых индекс >= 1
                const dynamicInputs = this.inputs.filter(input =>
                    (input.name.startsWith('string_')) &&
                    parseInt(input.name.split('_')[1]) >= 1 // Убедимся, что индекс >= 1
                );
                // Сортируем входы по индексу, чтобы корректно удалять с конца
                dynamicInputs.sort((a, b) => {
                     const indexA = parseInt(a.name.split('_')[1]);
                     const indexB = parseInt(b.name.split('_')[1]);
                     return indexA - indexB;
                });

                // Теперь вычисляем количество пар на основе отсортированного списка
                let currentNumInputs = 0;
                if (dynamicInputs.length > 0) {
                     // Берём индекс последнего входа в отсортированном списке
                     const lastInputName = dynamicInputs[dynamicInputs.length - 1].name;
                     const lastInputIndex = parseInt(lastInputName.split('_')[1]);
                     // Количество входов - это максимальный индекс, при условии, что структура правильная
                     // Для более надёжного подсчёта можно пройтись по списку и посчитать уникальные индексы >= 1
                     const uniqueIndices = new Set();
                     for (const input of dynamicInputs) {
                         const index = parseInt(input.name.split('_')[1]);
                         if (index >= 1) {
                             uniqueIndices.add(index);
                         }
                     }
                     currentNumInputs = uniqueIndices.size;
                }

                console.log(`[${nodeName}] Current inputs (calculated): ${currentNumInputs}, Requested inputs: ${newNumInputs}`);

                // 2. Удаляем лишние входы (с конца, т.е. с наибольшими индексами)
                if (newNumInputs < currentNumInputs) {
                    // Найдём индексы, которые нужно удалить (от newNumInputs+1 до currentNumInputs)
                    const indicesToRemove = [];
                    for (let i = newNumInputs + 1; i <= currentNumInputs; i++) {
                         indicesToRemove.push(i);
                    }
                    console.log(`[${nodeName}] Indices to remove: [${indicesToRemove.join(', ')}]`);

                    // Удаляем в обратном порядке, чтобы индексы оставшихся не сдвигались
                    for (let i = indicesToRemove.length - 1; i >= 0; i--) {
                        const idx = indicesToRemove[i];

                        // Удаляем string_ (чётный индекс в паре, на самом деле совпадает с idx)
                        const inputIndex = this.inputs.findIndex(input => input.name === `string_${idx}`);
                        if (inputIndex !== -1) {
                            this.removeInput(inputIndex);
                            console.log(`[${nodeName}] Removed input: string_${idx}`);
                        } else {
                             console.warn(`[${nodeName}] Input string_${idx} not found for removal.`);
                        }
                    }
                }

                // 3. Добавляем недостающие входы (в конец, начиная с currentNumInputs+1)
                if (newNumInputs > currentNumInputs) {
                    const inputsToAdd = newNumInputs - currentNumInputs;
                    console.log(`[${nodeName}] Adding ${inputsToAdd} inputs, starting from index ${currentNumInputs + 1}.`);

                    // Добавляем новые входы, начиная с индекса currentNumInputs + 1
                    for (let i = currentNumInputs + 1; i <= newNumInputs; i++) {
                         // Добавляем входы
                         this.addInput(`string_${i}`, "STRING");
                         console.log(`[${nodeName}] Added input: string_${i}`);
                    }
                }

                // 4. Обновляем размер ноды
                this.setSize(this.computeSize());
            };
        }
    },
});