#!/bin/bash
export TRANSFORMERS_CACHE='/comp_robot/rentianhe/caohe/cache'
python3 -m fastchat.model.apply_delta \
	--base /comp_robot/LLaMA/llama-13b-hf \
	--target ./ckpts/vicuna-13b \
	--delta lmsys/vicuna-13b-delta-v1.1
