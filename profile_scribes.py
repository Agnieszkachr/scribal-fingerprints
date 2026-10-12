"""Compute contextual change vectors for every variant.

For each variant the 10-word baseline context and the corresponding
manuscript context are embedded with Ancient-Greek-BERT (mean pooling over
the token vectors of the last hidden layer, attention-masked).  The change
vector is the difference ``ms_embedding - base_embedding``.  Manuscript
profiles are the mean change vector per manuscript (and per chapter).
"""
import argparse
import os

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

from download_itsee_data import write_type_counts

MODEL_NAME = "pranaydeeps/Ancient-Greek-BERT"


def load_model(device):
    print(f"Loading tokenizer and model: {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).to(device).eval()
    return tokenizer, model


def embed_texts(texts, tokenizer, model, device, max_length=128):
    """Mean-pooled last-layer embeddings (one 768-d vector per text)."""
    texts = [str(t) if pd.notna(t) else "" for t in texts]
    inputs = tokenizer(texts, return_tensors="pt", truncation=True,
                       padding=True, max_length=max_length).to(device)
    with torch.no_grad():
        hidden = model(**inputs).last_hidden_state
    mask = inputs['attention_mask'].unsqueeze(-1).float()
    summed = (hidden * mask).sum(1)
    counts = mask.sum(1).clamp(min=1e-9)
    return (summed / counts).cpu().numpy()


def main(base_ms='B', ablation_type=None, batch_size=16, device=None):
    if ablation_type:
        input_file = f"data/variants_ablation_{ablation_type}.csv"
        suffix = f"ablation_{ablation_type}"
    else:
        input_file = f"data/variants_full_john_{base_ms}.csv"
        suffix = base_ms
    if not os.path.exists(input_file):
        print(f"{input_file} not found.")
        return

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer, model = load_model(device)

    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} variants (suffix: {suffix}). Computing embeddings on {device}...")

    base_contexts = df['base_context_10w'].tolist()
    ms_contexts = df['ms_context_10w'].tolist()
    change_vectors = []
    for i in range(0, len(df), batch_size):
        embs_base = embed_texts(base_contexts[i:i + batch_size], tokenizer, model, device)
        embs_ms = embed_texts(ms_contexts[i:i + batch_size], tokenizer, model, device)
        change_vectors.extend(list(embs_ms - embs_base))
        done = min(i + batch_size, len(df))
        if done % (batch_size * 50) == 0 or done == len(df):
            print(f"Processed {done}/{len(df)} variants...")

    df['change_vector'] = change_vectors
    os.makedirs('outputs', exist_ok=True)
    df.to_pickle(f"outputs/variants_full_with_vectors_{suffix}.pkl")

    manuscripts = sorted(df['manuscript'].unique())
    profiles = {ms: np.mean(np.array(df.loc[df['manuscript'] == ms, 'change_vector'].tolist()), axis=0)
                for ms in manuscripts}
    np.savez(f"outputs/scribal_profiles_full_{suffix}.npz", **profiles)

    chapter_profiles = {}
    for ms in manuscripts:
        for ch in sorted(df['chapter'].unique()):
            subset = df[(df['manuscript'] == ms) & (df['chapter'] == ch)]
            if len(subset):
                chapter_profiles[f"{ms}_ch{ch}"] = np.mean(np.array(subset['change_vector'].tolist()), axis=0)
    np.savez(f"outputs/chapter_profiles_full_{suffix}.npz", **chapter_profiles)

    write_type_counts(df, suffix)
    print(f"Saved embeddings and profiles for {suffix} to outputs/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=str, default='B', help='Baseline MS')
    parser.add_argument('--ablation', type=str, default=None,
                        help='Ablation dataset (matched, func_words, masked)')
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--device', type=str, default=None, help='cpu or cuda (default: auto)')
    args = parser.parse_args()
    main(base_ms=args.baseline, ablation_type=args.ablation,
         batch_size=args.batch_size, device=args.device)
