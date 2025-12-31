import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

model_name = "./experiments/qwen2.5-coder-7b-inst"

# 加载模型，确保返回注意力权重
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto",
    output_attentions=True  # 确保模型返回注意力权重
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 准备输入
prompt = "who are you?"
messages = [
    {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# 生成文本并提取注意力权重
with torch.no_grad():
    outputs = model.generate(
        **model_inputs,
        max_new_tokens=512,
        return_dict_in_generate=True,  # 返回完整的输出字典
        output_attentions=True         # 确保返回注意力权重
    )

# 提取生成的文本
generated_ids = outputs.sequences
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
print("Generated Response:", response)

# 提取注意力权重
attentions = outputs.attentions  # 注意力权重是一个嵌套的元组
print(len(generated_ids[0]))
print(len(attentions))
len_prompt = len(generated_ids[0]) - len(attentions)
len_response = len(attentions)

layer = -1  # 层数
arr = np.zeros((len_response-1, len_prompt))  # response 最后一个 token 为 `<|im_end|>` 不再 forward pass
# 从第一到最后一个生成步骤
for step in range(1, len(attentions)):
    # attention_weights shape: (num_heads, 1, seq_length)
    attention_weights = attentions[step][layer][0].detach().cpu().float().numpy()  # 提取注意力权重
    # 取各个 heads 的平均
    arr[step-1] = np.squeeze(np.mean(attention_weights, axis=0))[: len_prompt]
print(arr.shape)

generated_tokens = tokenizer.convert_ids_to_tokens(generated_ids[0])
prompt_tokens = generated_tokens[: len_prompt]
response_tokens = generated_tokens[len_prompt:]
print(prompt_tokens)
print(response_tokens)
np.save('arr', arr)

# 绘制热图
plt.figure(figsize=(10, 10))
sns.heatmap(arr, cmap="viridis", xticklabels=prompt_tokens, yticklabels=response_tokens[:-1])
plt.title(f"Layer {layer} Attention Weights")
plt.xlabel("Input and Generated Tokens")
plt.ylabel("Input and Generated Tokens")
plt.show()
