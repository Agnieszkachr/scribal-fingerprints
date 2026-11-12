"""Two checks on the embedding results for John.

1. Layers. The change vectors are computed at each of the thirteen layers of
   Ancient-Greek-BERT (0 = the input embeddings, 12 = the last layer, the one
   ``profile_scribes.py`` uses), with the same context windows and the same
   attention-masked mean pooling, under the anchors B, A and aleph. For each
   layer: Cohen's d (inter- against intra-witness cosine distance) and its
   within-chapter permutation p; for anchor B also the chapter-level
   block-bootstrap interval.
2. Mask token. The content-masked dataset and the five random-masked draws of
   ``run_ablation_study.py`` are embedded with the model's own mask token in
   place of the placeholder ``CONTENT`` (last layer). Reported: d under content
   masking with its bootstrap interval, its permutation p and the null that
   keeps each witness's mixture of variant types; d under each random draw; and
   the difference (content masked minus the mean of the random draws) with its
   paired chapter-level bootstrap interval, computed as in
   ``supplementary_checks.py``.

The vectors are cached in outputs/ (``layer_vectors_<anchor>.npz``,
``mask_token_vectors_<dataset>.npz``; not part of the repository).

    python layer_and_mask_checks.py [layers] [masking]
        ->  outputs/layer_and_mask_checks.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src import stats_core as sc
from supplementary_checks import RANDOM_DRAWS, fast_block_bootstrap_d, fast_inter_intra_d

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
RESULT = OUT / "layer_and_mask_checks.json"
ANCHORS = ["B", "A", "aleph"]
BOOTSTRAP_ANCHORS = ["B"]
PLACEHOLDER = "CONTENT"
N_PERM_LAYER = sc.N_PERM      # permutations per layer
BATCH_SIZE = 32

_model = None


def load_model():
    """Tokenizer, model and device, loaded once."""
    global _model
    if _model is None:
        import torch
        from transformers import AutoModel, AutoTokenizer
        from profile_scribes import MODEL_NAME
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME).to(device).eval()
        try:        # the snapshot folder of the downloaded model is named after its revision
            from huggingface_hub import snapshot_download
            revision = Path(snapshot_download(MODEL_NAME, local_files_only=True)).name
        except Exception:
            revision = ""
        _model = (tokenizer, model, device, MODEL_NAME, revision)
    return _model


def embed_layers(texts):
    """Attention-masked mean of the token vectors at every layer: array (13, n, 768)."""
    import torch
    tokenizer, model, device, _, _ = load_model()
    texts = [str(t) if pd.notna(t) else "" for t in texts]
    out = []
    for i in range(0, len(texts), BATCH_SIZE):
        inputs = tokenizer(texts[i:i + BATCH_SIZE], return_tensors="pt", truncation=True,
                           padding=True, max_length=128).to(device)
        with torch.no_grad():
            hidden = model(**inputs, output_hidden_states=True).hidden_states
        mask = inputs["attention_mask"].unsqueeze(-1).float()
        counts = mask.sum(1).clamp(min=1e-9)
        out.append(torch.stack([(h * mask).sum(1) / counts for h in hidden]).cpu().numpy())
    return np.concatenate(out, axis=1)


def change_vectors(df, mask_token=None):
    """Change vectors (manuscript context minus baseline context) at every layer.
    With ``mask_token``, every placeholder word in the contexts is replaced by it."""
    base, ms = df["base_context_10w"], df["ms_context_10w"]
    if mask_token:
        def swap(text):
            if pd.isna(text):
                return text
            return " ".join(mask_token if w == PLACEHOLDER else w for w in str(text).split())
        base, ms = base.map(swap), ms.map(swap)
    return (embed_layers(ms.tolist()) - embed_layers(base.tolist())).astype(np.float32)


def cached(path, compute):
    """Vectors and model revision from the cache, or computed and cached."""
    if path.exists():
        with np.load(path) as z:
            return z["vectors"], str(z["revision"])
    vectors = compute()
    revision = load_model()[4]
    np.savez(path, vectors=vectors, revision=revision)
    return vectors, revision


def with_vectors(df, vectors):
    out = df.copy()
    out["change_vector"] = list(np.asarray(vectors, dtype=float))
    return out


def d_tests(df, n_perm, bootstrap=False, type_stratified=False):
    d, p, perm = sc.block_permutation_cohens_d(df, n_perm=n_perm)
    res = {"n": int(min(len(df), sc.D_MAX_N)), "d": round(float(d), 4),
           "null_mean": round(float(np.mean(perm)), 4), "null_sd": round(float(np.std(perm)), 4),
           "p": round(float(p), 6), "n_perm": len(perm)}
    if bootstrap:
        _, low, high, _ = fast_block_bootstrap_d(df)
        res.update(ci_low=round(low, 4), ci_high=round(high, 4), n_boot=sc.N_BOOT)
    if type_stratified:
        # chapter x type as the block keeps the type mixture of every witness in every chapter
        strat = df.copy()
        strat["chapter"] = df["chapter"].astype(str) + "|" + df[sc.type_column(df)].astype(str)
        _, ps, perms = sc.block_permutation_cohens_d(strat, n_perm=n_perm)
        res.update(type_stratified_null_mean=round(float(np.mean(perms)), 4),
                   type_stratified_null_sd=round(float(np.std(perms)), 4),
                   type_stratified_p=round(float(ps), 6))
    return res


def save(key, value):
    out = {}
    if RESULT.exists():
        with open(RESULT, encoding="utf-8") as f:
            out = json.load(f)
    out[key] = value
    with open(RESULT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


# 1 ─ Cohen's d at every layer ───────────────────────────────────────

def layers():
    out = {}
    for anchor in ANCHORS:
        df = pd.read_csv(ROOT / "data" / f"variants_full_john_{anchor}.csv")
        vectors, revision = cached(OUT / f"layer_vectors_{anchor}.npz", lambda: change_vectors(df))
        out["model_revision"] = revision
        out[anchor] = {}
        for layer in range(vectors.shape[0]):
            res = d_tests(with_vectors(df, vectors[layer]), N_PERM_LAYER, bootstrap=anchor in BOOTSTRAP_ANCHORS)
            out[anchor][str(layer)] = res
            print(anchor, "layer", layer, res, flush=True)
        save("layers", out)


# 2 ─ masking with the model's mask token ────────────────────────────

def masking():
    def last_layer(name):
        df = pd.read_csv(ROOT / "data" / f"variants_ablation_{name}.csv")
        vectors, revision = cached(
            OUT / f"mask_token_vectors_{name}.npz",
            lambda: change_vectors(df, mask_token=load_model()[0].mask_token)[-1])
        return with_vectors(df, vectors), revision

    masked, revision = last_layer("masked")
    out = {"model_revision": revision, "placeholder_replaced": PLACEHOLDER,
           "content_masked": d_tests(masked, sc.N_PERM_D, bootstrap=True, type_stratified=True)}
    print("content_masked", out["content_masked"], flush=True)
    draws = {}
    random_vectors = []
    for name in RANDOM_DRAWS:
        df, _ = last_layer(name)
        draws[name] = d_tests(df, sc.N_PERM_D)
        random_vectors.append(sc.vectors(df))
        print(name, draws[name], flush=True)
    out["random_masked"] = draws

    # content masked minus the mean of the random draws, bootstrapped in pairs over chapters
    vm = sc.vectors(masked)
    labels = masked["manuscript"].to_numpy()
    chapters = masked["chapter"].to_numpy()

    def d_on(rows, ids):
        dm = fast_inter_intra_d(vm[rows], labels[rows], ids)
        dr = [fast_inter_intra_d(v[rows], labels[rows], ids) for v in random_vectors]
        return dm, dr

    pm, pr = d_on(np.arange(len(masked)), None)
    r = sc.rng()
    uniq = np.unique(chapters)
    by_ch = {c: np.flatnonzero(chapters == c) for c in uniq}
    diffs = []
    for _ in range(sc.N_BOOT):
        sampled = r.choice(uniq, size=len(uniq), replace=True)
        rows = np.concatenate([by_ch[c] for c in sampled])
        rows = rows[r.choice(len(rows), size=min(len(rows), sc.D_BOOT_MAX_N), replace=False)]
        dm, dr = d_on(rows, rows)
        diffs.append(dm - float(np.mean(dr)))
    diffs = np.array(diffs)
    out["content_minus_random"] = {
        "content_masked_d": round(pm, 4), "random_masked_mean_d": round(float(np.mean(pr)), 4),
        "random_masked_min_d": round(float(np.min(pr)), 4), "random_masked_max_d": round(float(np.max(pr)), 4),
        "difference": round(pm - float(np.mean(pr)), 4),
        "boot_ci_low": round(float(np.percentile(diffs, 2.5)), 4),
        "boot_ci_high": round(float(np.percentile(diffs, 97.5)), 4),
        "boot_share_le_0": round(float(np.mean(diffs <= 0)), 4), "n_boot": sc.N_BOOT,
        "sample_per_replicate": sc.D_BOOT_MAX_N}
    print("content_minus_random", out["content_minus_random"], flush=True)
    save("mask_token", out)


def main(parts=("layers", "masking")):
    OUT.mkdir(exist_ok=True)
    if "layers" in parts:
        layers()
    if "masking" in parts:
        masking()


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("layers", "masking"))
