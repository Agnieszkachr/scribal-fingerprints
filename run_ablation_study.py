"""Create the two content-ablation datasets from the baseline-B variants.

* ``func_words``   – only variants in which every word of both readings is a
                     function word (contexts are left intact).
* ``masked``       – all variants, with every content word in the readings
                     and in the context windows replaced by the token
                     ``CONTENT``, so that only function words and word
                     positions remain visible to the embedding model.
* ``random_masked`` – control for ``masked``: in every field the same
                     number of words as the content masking removes is
                     replaced by ``CONTENT``, but the positions are drawn
                     at random (seeded per variant), irrespective of word
                     class. Any difference between ``masked`` and
                     ``random_masked`` is attributable to *which* words are
                     hidden rather than to how many.
"""
import os
import random

import pandas as pd

from download_itsee_data import write_type_counts

# Heuristic list of Greek function words (articles, pronouns, particles,
# conjunctions, prepositions, negations) in the unaccented orthography of the
# transcriptions.
FUNCTION_WORDS = {
    # conjunctions and particles
    'και', 'δε', 'γαρ', 'μεν', 'ουν', 'τε', 'αλλα', 'αλλ', 'ει', 'εαν', 'ινα', 'οπως', 'ως',
    'οτι', 'διο', 'διοτι', 'δη', 'ειτε', 'επει', 'επειδη', 'η', 'μην', 'οτε', 'ουτε',
    'πλην', 'που', 'πως', 'αρα', 'γε', 'ετι', 'αν', 'οταν', 'καθως', 'ωσπερ', 'ουτως',
    'νυν', 'ηδη', 'παλιν', 'τοτε', 'ιδου', 'ιδε', 'ναι', 'αμην',
    # prepositions
    'εν', 'εις', 'εκ', 'εξ', 'προς', 'απο', 'απ', 'αφ', 'επι', 'επ', 'εφ', 'περι', 'κατα',
    'κατ', 'καθ', 'μετα', 'μετ', 'μεθ', 'δια', 'δι', 'υπο', 'υπ', 'υφ', 'υπερ', 'παρα',
    'παρ', 'συν', 'αντι', 'προ', 'αμα', 'ανευ', 'εως', 'ενεκα', 'οπισθεν', 'χωρις',
    'εμπροσθεν', 'ενωπιον', 'αχρι', 'μεχρι',
    # article
    'ο', 'το', 'οι', 'αι', 'τα', 'του', 'της', 'των', 'τω', 'τη', 'τοις', 'ταις',
    'τον', 'την', 'τους', 'τας',
    # personal, demonstrative, relative and indefinite pronouns
    'αυτος', 'αυτου', 'αυτω', 'αυτον', 'αυτοι', 'αυτων', 'αυτοις', 'αυτους', 'αυτη',
    'αυτης', 'αυτην', 'αυται', 'αυταις', 'αυτας', 'αυτο',
    'εγω', 'εμου', 'μου', 'εμοι', 'μοι', 'εμε', 'με', 'ημεις', 'ημων', 'ημιν', 'ημας',
    'συ', 'σου', 'σοι', 'σε', 'υμεις', 'υμων', 'υμιν', 'υμας',
    'τις', 'τι', 'τινος', 'τινι', 'τινα', 'τινες', 'τινων', 'τισι', 'τινας',
    'ος', 'ης', 'ω', 'ον', 'ην', 'α', 'ων', 'οις', 'αις', 'ους', 'ας',
    'ουτος', 'τουτο', 'τουτου', 'τουτω', 'τουτον', 'ουτοι', 'ταυτα', 'τουτων',
    'τουτοις', 'τουτους', 'ταυτης', 'ταυτη', 'ταυτην', 'ταυταις', 'ταυτας',
    'εκεινος', 'εκεινη', 'εκεινο', 'εκεινου', 'εκεινω', 'εκεινον', 'εκεινοι',
    'εκεινων', 'εκεινοις', 'εκεινους', 'οστις', 'ητις', 'εαυτου', 'εαυτω', 'εαυτον',
    'εαυτους', 'εαυτων', 'εαυτοις', 'εαυτην',
    # negations
    'ου', 'ουκ', 'ουχ', 'ουχι', 'μη', 'ουδε', 'μηδε', 'μητε', 'ουδεν', 'μηδεν',
    'ουδεις', 'μηδεις', 'ουπω', 'μηπω', 'ουκετι', 'μηκετι',
}


def is_function_word(word):
    return word.lower() in FUNCTION_WORDS


def apply_function_words_filter(df):
    """Keep variants whose readings consist entirely of function words."""
    keep = []
    for idx, row in df.iterrows():
        br, mr = str(row['base_reading']), str(row['ms_reading'])
        b_words = [] if br == '[ADD]' else br.split()
        m_words = [] if mr == '[OMIT]' else mr.split()
        words = b_words + m_words
        if words and all(is_function_word(w) for w in words):
            keep.append(idx)
    return df.loc[keep].copy()


def mask_text(text):
    if pd.isna(text) or text in ('[ADD]', '[OMIT]'):
        return text
    return ' '.join(w if is_function_word(w) else 'CONTENT' for w in str(text).split())


def mask_random(text, n_mask, rng):
    if pd.isna(text) or text in ('[ADD]', '[OMIT]'):
        return text
    words = str(text).split()
    if n_mask <= 0 or not words:
        return text
    positions = set(rng.sample(range(len(words)), min(n_mask, len(words))))
    return ' '.join('CONTENT' if i in positions else w for i, w in enumerate(words))


def apply_random_masking(df, seed=42):
    """Mask as many words per field as content masking does, at random positions."""
    masked = df.copy()
    for col in ('base_reading', 'ms_reading', 'base_context_10w', 'ms_context_10w'):
        out = []
        for idx, text in zip(df.index, df[col]):
            if pd.isna(text) or text in ('[ADD]', '[OMIT]'):
                out.append(text)
                continue
            n_mask = sum(not is_function_word(w) for w in str(text).split())
            rng = random.Random(f"{seed}:{idx}:{col}")
            out.append(mask_random(text, n_mask, rng))
        masked[col] = out
    return masked


def apply_content_masking(df):
    masked = df.copy()
    for col in ('base_reading', 'ms_reading', 'base_context_10w', 'ms_context_10w'):
        masked[col] = masked[col].apply(mask_text)
    return masked


def main(base_ms='B'):
    base_file = f"data/variants_full_john_{base_ms}.csv"
    if not os.path.exists(base_file):
        print(f"{base_file} not found. Run download_itsee_data.py first.")
        return
    df = pd.read_csv(base_file)
    print(f"Loaded full corpus: {len(df)} variants.")

    func_df = apply_function_words_filter(df)
    func_df.to_csv("data/variants_ablation_func_words.csv", index=False)
    write_type_counts(func_df, 'ablation_func_words')
    print(f"Function-words-only dataset: {len(func_df)} variants")

    masked_df = apply_content_masking(df)
    masked_df.to_csv("data/variants_ablation_masked.csv", index=False)
    write_type_counts(masked_df, 'ablation_masked')
    print(f"Content-masked dataset: {len(masked_df)} variants "
          f"({(masked_df['base_context_10w'] == masked_df['ms_context_10w']).sum()} with identical masked contexts)")

    random_df = apply_random_masking(df)
    random_df.to_csv("data/variants_ablation_random_masked.csv", index=False)
    write_type_counts(random_df, 'ablation_random_masked')
    print(f"Random-masked control dataset: {len(random_df)} variants "
          f"({(random_df['base_context_10w'] == random_df['ms_context_10w']).sum()} with identical masked contexts)")


if __name__ == "__main__":
    main()
