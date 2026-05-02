import { app } from "../../../scripts/app.js";

// Name of the node we want to modify (must match the Python class name)
const nodeName = "JsonBuilder";

// Register the extension
app.registerExtension({
    name: "Stalkervr.JsonBuilder", // Unique extension name
    // Use beforeRegisterNodeDef as recommended in the documentation
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Check if this is the target node
        if (nodeData.name === nodeName) {
            console.log(`[JsonBuilder Extension] Found target node: ${nodeName}`);

            // --- Logic for adding button and managing inputs ---
            // We add the button and functions to the onNodeCreated method, which is called for each node instance
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                // Call the original method if it exists
                if (originalOnNodeCreated) {
                    originalOnNodeCreated.apply(this, arguments);
                }

                console.log(`[JsonBuilder Extension] onNodeCreated called for instance of ${nodeName}`);

                // --- Add button ---
                // Find the widget that controls the number of pairs (num_pairs)
                const numPairsWidget = this.widgets.find(w => w.name === "num_pairs");

                if (numPairsWidget) {
                    // Add the "Update inputs" button
                    const updateButton = this.addWidget("button", "Update pairs", false, () => {
                        console.log(`[JsonBuilder Extension] Update inputs button clicked on instance of ${nodeName}`);
                        // Call the input update function
                        this.updateDynamicInputs();
                    }, { property: "update_button" });

                    console.log(`[JsonBuilder Extension] Added 'Update pairs' button to ${nodeName} instance.`);

                    // Initialize inputs when the node is created based on the initial num_pairs value
                    this.updateDynamicInputs();
                } else {
                    console.warn(`[JsonBuilder Extension] Widget 'num_pairs' not found during onNodeCreated for ${nodeName}.`);
                }
            };

            // --- Add method to prototype for updating inputs ---
            nodeType.prototype.updateDynamicInputs = function() {
                const nodeName = "JsonBuilder";
                console.log(`[${nodeName} Extension] Updating inputs.`);

                // Get the num_pairs value
                const numPairsWidget = this.widgets.find(w => w.name === "num_pairs");
                if (!numPairsWidget) {
                    console.warn(`[${nodeName} Extension] Widget 'num_pairs' not found during updateDynamicInputs.`);
                    return;
                }

                const newNumPairs = Math.max(0, Math.min(100, numPairsWidget.value));

                // --- PARTIAL UPDATE LOGIC (with 1-based indexing) ---
                // 1. Determine the current number of dynamic inputs
                // Filter by names starting with 'key_' or 'value_', and with index >= 1
                const dynamicInputs = this.inputs.filter(input =>
                    (input.name.startsWith('key_') || input.name.startsWith('value_')) &&
                    parseInt(input.name.split('_')[1]) >= 1 // Ensure index >= 1
                );
                // Sort inputs by index to correctly remove from the end
                dynamicInputs.sort((a, b) => {
                     const indexA = parseInt(a.name.split('_')[1]);
                     const indexB = parseInt(b.name.split('_')[1]);
                     return indexA - indexB;
                });

                // Now calculate the number of pairs based on the sorted list
                // Assume pairs are strictly sequential: key_1, value_1, key_2, value_2, ...
                let currentNumPairs = 0;
                if (dynamicInputs.length > 0) {
                     // Get the index of the last input in the sorted list
                     const lastInputName = dynamicInputs[dynamicInputs.length - 1].name;
                     const lastInputIndex = parseInt(lastInputName.split('_')[1]);
                     // Number of pairs is the maximum index, assuming correct structure
                     // For more reliable counting, iterate through the list and count unique indices >= 1
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

                // 2. Remove excess inputs (from the end, i.e., with highest indices)
                if (newNumPairs < currentNumPairs) {
                    // Find indices to remove (from newNumPairs+1 to currentNumPairs)
                    const indicesToRemove = [];
                    for (let i = newNumPairs + 1; i <= currentNumPairs; i++) {
                         indicesToRemove.push(i);
                    }
                    console.log(`[${nodeName} Extension] Indices to remove: [${indicesToRemove.join(', ')}]`);

                    // Remove in reverse order so remaining indices don't shift
                    for (let i = indicesToRemove.length - 1; i >= 0; i--) {
                        const idx = indicesToRemove[i];

                        // Remove value_ (odd index in pair, actually matches idx)
                        const valueInputIndex = this.inputs.findIndex(input => input.name === `value_${idx}`);
                        if (valueInputIndex !== -1) {
                            this.removeInput(valueInputIndex);
                            console.log(`[${nodeName} Extension] Removed input: value_${idx}`);
                        } else {
                             console.warn(`[${nodeName} Extension] Input value_${idx} not found for removal.`);
                        }

                        // Remove key_ (even index in pair, actually matches idx)
                        const keyInputIndex = this.inputs.findIndex(input => input.name === `key_${idx}`);
                        if (keyInputIndex !== -1) {
                            this.removeInput(keyInputIndex);
                            console.log(`[${nodeName} Extension] Removed input: key_${idx}`);
                        } else {
                             console.warn(`[${nodeName} Extension] Input key_${idx} not found for removal.`);
                        }
                    }
                }

                // 3. Add missing inputs (at the end, starting from currentNumPairs+1)
                if (newNumPairs > currentNumPairs) {
                    const pairsToAdd = newNumPairs - currentNumPairs;
                    console.log(`[${nodeName} Extension] Adding ${pairsToAdd} pairs of inputs, starting from index ${currentNumPairs + 1}.`);

                    // Add new inputs starting from index currentNumPairs + 1
                    for (let i = currentNumPairs + 1; i <= newNumPairs; i++) {
                         // Add inputs
                         this.addInput(`key_${i}`, "STRING");
                         this.addInput(`value_${i}`, "*");
                         console.log(`[${nodeName} Extension] Added input: key_${i}`);
                         console.log(`[${nodeName} Extension] Added input: value_${i}`);
                    }
                }

                // 4. Update node size
                this.setSize(this.computeSize());
            };
        }
        // else {
        //     // Not our node, do nothing for it.
        // }
    },
});