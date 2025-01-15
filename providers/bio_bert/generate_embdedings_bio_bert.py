# import torch
# import numpy as np
# from tqdm import tqdm
# from transformers import AutoTokenizer, AutoModel
#
# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#
# # Load models and tokenizers
# models = {
#     "BioBERT": "dmis-lab/biobert-base-cased-v1.1"
# }
# tokenizers = {name: AutoTokenizer.from_pretrained(model_name) for name, model_name in models.items()}
# models = {name: AutoModel.from_pretrained(model_name).to(device) for name, model_name in models.items()}
#
# def generate_embeddings(text_list, model, tokenizer, model_name):
#     embeddings = []
#     for text in tqdm(text_list, desc=f"Generating {model_name} embeddings"):
#         inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
#         inputs = {k: v.to(device) for k, v in inputs.items()}  # Move inputs to GPU if available
#         with torch.no_grad():
#             outputs = model(**inputs)
#             cls_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy().flatten()  # Flatten to (768,)
#             embeddings.append(cls_embedding)
#     return np.array(embeddings)
#
# # Function to generate embeddings
# def generate_embeddings_from_model_named(text_list, model_name):
#     return generate_embeddings(text_list, models[model_name], tokenizers[model_name], model_name)
#
# def generated_aggregated_embeddings(input_string) -> dict:
#     final_response = {
#         "success": False,
#         "message": "Generating aggregated embeddings",
#         "data": None
#     }
#     try:
#           # Convert data to Chunks
#           tokens = tokenizers["BioBERT"].tokenize(input_string)
#           chunk_size = 500
#           chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
#           chunk_texts = [tokenizers["BioBERT"].convert_tokens_to_string(chunk) for chunk in chunks]
#           chunk_embeddings = [generate_embeddings_from_model_named(text_list=[chunk_text], model_name="BioBERT") for
#                               chunk_text in chunk_texts]
#           document_embeddings = np.mean(chunk_embeddings, axis=0)
#           final_response["success"] = True
#           final_response["data"] = document_embeddings
#           final_response["message"] = "Generated aggregated embeddings"
#           return final_response
#     except Exception as e:
#         print(f"Unable to generate aggregated embeddings: {e}")
#         final_response["success"] = False
#         final_response["message"] = f"Unable to generate aggregated embeddings: {e}"
#         return final_response