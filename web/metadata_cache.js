// ComfyUI-StalkerVr/web/metadata_cache.js
import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "Stalker.MetadataCache",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        // Match the renamed node class
        if (nodeData.name === "ImageLoadWithMetadata") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated?.apply(this, arguments);

                const imageWidget = this.widgets.find(w => w.name === "image");
                if (imageWidget) {
                    console.log("[MetadataCache] Image widget found in ImageLoadWithMetadata");

                    const originalCallback = imageWidget.callback;

                    imageWidget.callback = async (value) => {
                        console.log(`[MetadataCache] Image selection changed: "${value}"`);

                        // Skip temporary mask editor files
                        if (!value || typeof value !== 'string' || value.includes("clipspace-painted-masked-")) {
                            console.warn(`[MetadataCache] Skipping temp mask file: "${value}"`);
                            return originalCallback?.(value);
                        }

                        try {
                            console.log(`[MetadataCache] Sending cache request for: "${value}"`);

                            const response = await fetch("/stalker/metadata_cache", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ filename: value })
                            });

                            if (response.ok) {
                                console.log(`[MetadataCache] Successfully cached metadata for: "${value}"`);
                            } else {
                                const errorText = await response.text();
                                console.error(`[MetadataCache] Server error (${response.status}):`, errorText);
                            }
                        } catch (e) {
                            console.error(`[MetadataCache] Failed to cache metadata for "${value}":`, e);
                        }

                        return originalCallback?.(value);
                    };

                    console.log("[MetadataCache] Callback override installed");
                } else {
                    console.warn("[MetadataCache] Image widget NOT found in ImageLoadWithMetadata");
                }

                return r;
            };
        }
    }
});