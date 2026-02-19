import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import os

model_name = "pranaydeeps/Ancient-Greek-BERT"
print(f"Loading tokenizer and model: {model_name}...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

import argparse

def main(base_ms='B', ablation_type=None):
    if ablation_type:
        input_file = f"data/variants_ablation_{ablation_type}.csv"
        suffix = f"ablation_{ablation_type}"
    else:
        input_file = f"data/variants_full_john_{base_ms}.csv"
        suffix = base_ms
        
    if not os.path.exists(input_file):
        print(f"{input_file} not found.")
        return
        
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} refined variants for John 1-21 (Suffix: {suffix}). Computing embeddings...")
    
    batch_size = 16
    all_change_vectors = []
    
    base_contexts = df['base_context_10w'].tolist()
    ms_contexts = df['ms_context_10w'].tolist()
    
    for i in range(0, len(df), batch_size):
        batch_base = base_contexts[i:i+batch_size]
        batch_ms = ms_contexts[i:i+batch_size]
        
        def get_batch_embeddings(texts):
            # Convert NaN to empty string just in case
            texts = [str(t) if pd.notna(t) else "" for t in texts]
            inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=128)
            with torch.no_grad():
                outputs = model(**inputs)
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            return (sum_embeddings / sum_mask).numpy()

        embs_base = get_batch_embeddings(batch_base)
        embs_ms = get_batch_embeddings(batch_ms)
        
        batch_changes = embs_ms - embs_base
        all_change_vectors.extend(list(batch_changes))
        
        if (i + batch_size) % 160 == 0 or (i + batch_size) >= len(df):
            print(f"Processed {min(i + batch_size, len(df))}/{len(df)} variants...")
            
    df['change_vector'] = all_change_vectors
    
    os.makedirs('outputs', exist_ok=True)
    df.to_pickle(f"outputs/variants_full_with_vectors_{suffix}.pkl")
    
    manuscripts = df['manuscript'].unique()
    profiles = {}
    for ms in manuscripts:
        ms_vectors = np.array(df[df['manuscript'] == ms]['change_vector'].tolist())
        profiles[ms] = np.mean(ms_vectors, axis=0)
    
    np.savez(f"outputs/scribal_profiles_full_{suffix}.npz", **profiles)
    
    chapters = df['chapter'].unique()
    chapter_profiles = {}
    for ms in manuscripts:
        for ch in chapters:
            subset = df[(df['manuscript'] == ms) & (df['chapter'] == ch)]
            if len(subset) > 0:
                vecs = np.array(subset['change_vector'].tolist())
                chapter_profiles[f"{ms}_ch{ch}"] = np.mean(vecs, axis=0)
    
    np.savez(f"outputs/chapter_profiles_full_{suffix}.npz", **chapter_profiles)

    prop_data = []
    for ms in manuscripts:
        ms_df = df[df['manuscript'] == ms]
        total = len(ms_df)
        if total == 0: continue
        counts = ms_df['type'].value_counts()
        prop_data.append({
            'manuscript': ms,
            'substitution_morphological': counts.get('substitution_morphological', 0),
            'substitution_lexical': counts.get('substitution_lexical', 0),
            'substitution_word_order': counts.get('substitution_word_order', 0),
            'addition': counts.get('addition', 0),
            'omission': counts.get('omission', 0),
            'total_variants': total
        })
        
    pd.DataFrame(prop_data).to_csv(f"outputs/type_counts_full_{suffix}.csv", index=False)
    print(f"Saved all embeddings and profiles for {suffix} to outputs/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=str, default='B', help='Baseline MS')
    parser.add_argument('--ablation', type=str, default=None, help='Ablation type (func_words, masked)')
    args = parser.parse_args()
    main(base_ms=args.baseline, ablation_type=args.ablation)
