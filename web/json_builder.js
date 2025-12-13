import { api } from "../../../scripts/api.js";
import { app } from "../../../scripts/app.js";

// Имя ноды, которую мы хотим модифицировать (должно совпадать с именем Python-класса)
const nodeName = "JsonBuilder";

// Регистрируем расширение
app.registerExtension({
    name: "Stalkervr.JsonBuilder", // Уникальное имя расширения
    // Используем beforeRegisterNodeDef, как рекомендовано в документации
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Проверяем, что это нужная нам нода
        if (nodeData.name === nodeName) {
            console.log(`[JsonBuilder Extension] Found target node: ${nodeName}`);

            // --- Логика добавления кнопки и управления входами ---
            // Мы добавим кнопку и функции в метод onNodeCreated, который вызывается для каждого экземпляра ноды
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                // Вызываем оригинальный метод, если он существует
                if (originalOnNodeCreated) {
                    originalOnNodeCreated.apply(this, arguments);
                }

                console.log(`[JsonBuilder Extension] onNodeCreated called for instance of ${nodeName}`);

                // --- Добавление кнопки ---
                // Ищем виджет, управляющий количеством пар (num_pairs)
                const numPairsWidget = this.widgets.find(w => w.name === "num_pairs");

                if (numPairsWidget) {
                    // Добавляем кнопку "Update inputs"
                    const updateButton = this.addWidget("button", "Update pairs", false, () => {
                        console.log(`[JsonBuilder Extension] Update inputs button clicked on instance of ${nodeName}`);
                        // Вызываем функцию обновления входов
                        this.updateDynamicInputs();
                    }, { property: "update_button" });

                    console.log(`[JsonBuilder Extension] Added 'Update pairs' button to ${nodeName} instance.`);

                    // Инициализируем входы при создании ноды на основе начального значения num_pairs
                    this.updateDynamicInputs();
                } else {
                    console.warn(`[JsonBuilder Extension] Widget 'num_pairs' not found during onNodeCreated for ${nodeName}.`);
                }
            };

            // --- Добавляем метод к прототипу для обновления входов ---
            nodeType.prototype.updateDynamicInputs = function() {
                const nodeName = "JsonBuilder";
                console.log(`[${nodeName} Extension] Updating inputs.`);

                // Получаем значение num_pairs
                const numPairsWidget = this.widgets.find(w => w.name === "num_pairs");
                if (!numPairsWidget) {
                    console.warn(`[${nodeName} Extension] Widget 'num_pairs' not found during updateDynamicInputs.`);
                    return;
                }

                const newNumPairs = Math.max(0, Math.min(20, numPairsWidget.value));

                // --- ЛОГИКА ЧАСТИЧНОГО ОБНОВЛЕНИЯ (с нумерацией с 1) ---
                // 1. Определяем текущее количество динамических входов
                // Фильтруем по именам, начинающимся с 'key_' или 'value_', и у которых индекс >= 1
                const dynamicInputs = this.inputs.filter(input =>
                    (input.name.startsWith('key_') || input.name.startsWith('value_')) &&
                    parseInt(input.name.split('_')[1]) >= 1 // Убедимся, что индекс >= 1
                );
                // Сортируем входы по индексу, чтобы корректно удалять с конца
                dynamicInputs.sort((a, b) => {
                     const indexA = parseInt(a.name.split('_')[1]);
                     const indexB = parseInt(b.name.split('_')[1]);
                     return indexA - indexB;
                });

                // Теперь вычисляем количество пар на основе отсортированного списка
                // Предполагаем, что пары идут строго подряд: key_1, value_1, key_2, value_2, ...
                let currentNumPairs = 0;
                if (dynamicInputs.length > 0) {
                     // Берём индекс последнего входа в отсортированном списке
                     const lastInputName = dynamicInputs[dynamicInputs.length - 1].name;
                     const lastInputIndex = parseInt(lastInputName.split('_')[1]);
                     // Количество пар - это максимальный индекс, при условии, что структура правильная
                     // Для более надёжного подсчёта можно пройтись по списку и посчитать уникальные индексы >= 1
                     const uniqueIndices = new Set();
                     for (const input of dynamicInputs) {
                         const index = parseInt(input.name.split('_')[1]);
                         if (index >= 1) {
                             uniqueIndices.add(index);
                         }
                     }
                     currentNumPairs = uniqueIndices.size;
                }

                console.log(`[${nodeName} Extension] Current pairs (calculated): ${currentNumPairs}, Requested pairs: ${newNumPairs}`);

                // 2. Удаляем лишние входы (с конца, т.е. с наибольшими индексами)
                if (newNumPairs < currentNumPairs) {
                    // Найдём индексы, которые нужно удалить (от newNumPairs+1 до currentNumPairs)
                    const indicesToRemove = [];
                    for (let i = newNumPairs + 1; i <= currentNumPairs; i++) {
                         indicesToRemove.push(i);
                    }
                    console.log(`[${nodeName} Extension] Indices to remove: [${indicesToRemove.join(', ')}]`);

                    // Удаляем в обратном порядке, чтобы индексы оставшихся не сдвигались
                    for (let i = indicesToRemove.length - 1; i >= 0; i--) {
                        const idx = indicesToRemove[i];

                        // Удаляем value_ (нечётный индекс в паре, на самом деле совпадает с idx)
                        const valueInputIndex = this.inputs.findIndex(input => input.name === `value_${idx}`);
                        if (valueInputIndex !== -1) {
                            this.removeInput(valueInputIndex);
                            console.log(`[${nodeName} Extension] Removed input: value_${idx}`);
                        } else {
                             console.warn(`[${nodeName} Extension] Input value_${idx} not found for removal.`);
                        }

                        // Удаляем key_ (чётный индекс в паре, на самом деле совпадает с idx)
                        const keyInputIndex = this.inputs.findIndex(input => input.name === `key_${idx}`);
                        if (keyInputIndex !== -1) {
                            this.removeInput(keyInputIndex);
                            console.log(`[${nodeName} Extension] Removed input: key_${idx}`);
                        } else {
                             console.warn(`[${nodeName} Extension] Input key_${idx} not found for removal.`);
                        }
                    }
                }

                // 3. Добавляем недостающие входы (в конец, начиная с currentNumPairs+1)
                if (newNumPairs > currentNumPairs) {
                    const pairsToAdd = newNumPairs - currentNumPairs;
                    console.log(`[${nodeName} Extension] Adding ${pairsToAdd} pairs of inputs, starting from index ${currentNumPairs + 1}.`);

                    // Добавляем новые входы, начиная с индекса currentNumPairs + 1
                    for (let i = currentNumPairs + 1; i <= newNumPairs; i++) {
                         // Добавляем входы
                         this.addInput(`key_${i}`, "STRING");
                         this.addInput(`value_${i}`, "STRING");
                         console.log(`[${nodeName} Extension] Added input: key_${i}`);
                         console.log(`[${nodeName} Extension] Added input: value_${i}`);
                    }
                }

                // 4. Обновляем размер ноды
                this.setSize(this.computeSize());
            };
        }
        // else {
        //     // Не наша нода, ничего не делаем для неё.
        // }
    },
});