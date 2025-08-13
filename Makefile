#!/bin/bash

# The full, absolute path to your model file.
MODEL_FULL_PATH="/home/donovan/Documents/LocalLLMs/Lexi-Llama-3-8B-Uncensored-Q8_0.gguf"
MODELFILE_NAME="Modelfile"

# --- Create the Modelfile ---
echo "Creating Modelfile pointing to $MODEL_FULL_PATH..."

cat <<EOF > "$MODELFILE_NAME"
# Tell Ollama to use the model at the specified absolute path.
FROM $MODEL_FULL_PATH

# --- System Prompt ---
# Sets the default behavior and personality for the model.
SYSTEM """
You are Lexi-Llama, an uncensored and helpful AI assistant. You will provide factual and direct responses.
"""
EOF

echo "Successfully created '$MODELFILE_NAME'."
echo "You can now build the model from any directory where this Modelfile is located."
