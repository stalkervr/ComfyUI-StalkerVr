import { app } from "../../../scripts/app.js";

// Name of the node we want to modify (must match the Python class name)
const nodeName = "StringBuilder";

app.registerExtension({
    name: "Stalkervr.StringBuilder", // Unique extension name
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Check if this is the target node
        if (nodeData.name === nodeName) {
            // Save the original onNodeCreated method
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

            // Override the onNodeCreated method to modify the node instance
            nodeType.prototype.onNodeCreated = function() {
                // Call the original method if it exists
                if (originalOnNodeCreated) {
                    originalOnNodeCreated.apply(this, arguments);
                }

                console.log(`[${nodeName}] Node instance created.`);

                // --- Initialization and setup logic ---
                // We use setTimeout to ensure that this.widgets and this.inputs
                // are fully initialized by ComfyUI before we start modifying them.
                setTimeout(() => {
                    this.initDynamicInputs();
                }, 50); // Small 50ms delay
            };

            // Add method to prototype for convenient initialization
            nodeType.prototype.initDynamicInputs = function() {
                const nodeName = "StringBuilder";
                console.log(`[${nodeName}] Initializing dynamic input logic.`);

                // Find the widget that controls the number of inputs (num_inputs)
                const numInputsWidget = this.widgets.find(w => w.name === "num_inputs");

                if (numInputsWidget) {
                    // Add the "Update inputs" button
                    const updateButton = this.addWidget("button", "Update inputs", false, () => {
                        console.log(`[${nodeName}] Update inputs button clicked.`);
                        // Call the input update function
                        this.updateDynamicInputs();
                    }, { property: "update_button" });

                    // Initialize inputs when the node is created based on the initial num_inputs value
                    this.updateDynamicInputs();
                } else {
                    console.warn(`[${nodeName}] Widget 'num_inputs' not found during initDynamicInputs.`);
                }
            };

            // Add method to prototype for updating inputs
            nodeType.prototype.updateDynamicInputs = function() {
                const nodeName = "StringBuilder";
                console.log(`[${nodeName}] Updating inputs.`);

                // Get the num_inputs value
                const numInputsWidget = this.widgets.find(w => w.name === "num_inputs");
                if (!numInputsWidget) {
                    console.warn(`[${nodeName}] Widget 'num_inputs' not found during updateDynamicInputs.`);
                    return;
                }

                const newNumInputs = Math.max(0, Math.min(100, numInputsWidget.value));

                // --- PARTIAL UPDATE LOGIC (with 1-based indexing) ---
                // 1. Determine the current number of dynamic inputs
                // Filter by names starting with 'string_', and with index >= 1
                const dynamicInputs = this.inputs.filter(input =>
                    (input.name.startsWith('string_')) &&
                    parseInt(input.name.split('_')[1]) >= 1 // Ensure index >= 1
                );
                // Sort inputs by index to correctly remove from the end
                dynamicInputs.sort((a, b) => {
                     const indexA = parseInt(a.name.split('_')[1]);
                     const indexB = parseInt(b.name.split('_')[1]);
                     return indexA - indexB;
                });

                // Now calculate the number of inputs based on the sorted list
                let currentNumInputs = 0;
                if (dynamicInputs.length > 0) {
                     // Get the index of the last input in the sorted list
                     const lastInputName = dynamicInputs[dynamicInputs.length - 1].name;
                     const lastInputIndex = parseInt(lastInputName.split('_')[1]);
                     // Number of inputs is the maximum index, assuming correct structure
                     // For more reliable counting, iterate through the list and count unique indices >= 1
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

                // 2. Remove excess inputs (from the end, i.e., with highest indices)
                if (newNumInputs < currentNumInputs) {
                    // Find indices to remove (from newNumInputs+1 to currentNumInputs)
                    const indicesToRemove = [];
                    for (let i = newNumInputs + 1; i <= currentNumInputs; i++) {
                         indicesToRemove.push(i);
                    }
                    console.log(`[${nodeName}] Indices to remove: [${indicesToRemove.join(', ')}]`);

                    // Remove in reverse order so remaining indices don't shift
                    for (let i = indicesToRemove.length - 1; i >= 0; i--) {
                        const idx = indicesToRemove[i];

                        // Remove string_ (even index in pair, actually matches idx)
                        const inputIndex = this.inputs.findIndex(input => input.name === `string_${idx}`);
                        if (inputIndex !== -1) {
                            this.removeInput(inputIndex);
                            console.log(`[${nodeName}] Removed input: string_${idx}`);
                        } else {
                             console.warn(`[${nodeName}] Input string_${idx} not found for removal.`);
                        }
                    }
                }

                // 3. Add missing inputs (at the end, starting from currentNumInputs+1)
                if (newNumInputs > currentNumInputs) {
                    const inputsToAdd = newNumInputs - currentNumInputs;
                    console.log(`[${nodeName}] Adding ${inputsToAdd} inputs, starting from index ${currentNumInputs + 1}.`);

                    // Add new inputs starting from index currentNumInputs + 1
                    for (let i = currentNumInputs + 1; i <= newNumInputs; i++) {
                         // Add inputs
                         this.addInput(`string_${i}`, "STRING");
                         console.log(`[${nodeName}] Added input: string_${i}`);
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