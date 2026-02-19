import pandas as pd
import numpy as np
import os
import re

def is_function_word(word):
    # Comprehensive heuristic list of Greek function words/particles/pronouns
    func_words = {
        # Conjunctions & Particles
        'και', 'δε', 'γαρ', 'μεν', 'ουν', 'τε', 'αλλα', 'ει', 'εαν', 'ινα', 'οπως', 'ως', 'οτι', 'διο', 'διοτι', 
        'δη', 'ειτε', 'επει', 'επειδη', 'η', 'μην', 'οτε', 'ουτε', 'πλην', 'που', 'πως', 'αρα', 'γε', 'ετι', 'τε',
        
        # Prepositions
        'εν', 'εις', 'εκ', 'εξ', 'προς', 'απο', 'επι', 'περι', 'κατα', 'μετα', 'δια', 'υπο', 'υπερ', 'παρα', 'συν',
        'αντι', 'προ', 'αμα', 'ανευ', 'εως', 'νεκα', 'οπισθεν', 'χωρις', 'εμπροσθεν', 'ενωπιον',
        
        # Article
        'ο', 'η', 'το', 'οι', 'αι', 'τα', 'του', 'της', 'των', 'τω', 'τη', 'τοις', 'ταις', 'τον', 'την',
        
        # Personal/Demonstrative/Relative Pronouns
        'αυτος', 'αυτου', 'αυτω', 'αυτον', 'αυτοι', 'αυτων', 'αυτοις', 'αυτους', 'αυτη', 'αυτης', 'αυτην', 'αυται', 'αυταις', 'αυτας',
        'εγω', 'εμου', 'μου', 'εμοι', 'μοι', 'εμε', 'με', 'ημεις', 'ημων', 'ημιν', 'ημας',
        'συ', 'σου', 'σοι', 'σε', 'υμεις', 'υμων', 'υμιν', 'υμας',
        'τις', 'τι', 'τινος', 'τινι', 'τινα', 'τινες', 'τινων', 'τισι', 'τινας',
        'ος', 'ης', 'ω', 'ον', 'ην', 'α', 'ων', 'οις', 'αις', 'ους', 'ας',
        'ουτος', 'τουτο', 'τουτου', 'τουτω', 'τουτον', 'ουτοι', 'ταυτα', 'τουτων', 'τουτοις', 'τουτους', 
        'αυτη', 'ταυτης', 'ταυτη', 'ταυτην', 'αυται', 'ταυταις', 'ταυτας',
        'εκεινος', 'εκεινη', 'εκεινο', 'εκεινου', 'εκεινω', 'εκεινον', 'εκεινοι', 'εκεινων', 'εκεινοις', 'εκεινους',
        'τις', 'τι', 'τινος', 'τινι', 'τινα', 'τινες', 'τινων', 'τισι', 'τινας', 'οστις', 'ητις', 'οτι',
        
        # Negations
        'ου', 'ουκ', 'ουχ', 'μη', 'ουδε', 'μηδε', 'ουτε', 'μητε'
    }
    w = word.lower()
    return w in func_words

def apply_function_words_filter(df):
    filtered_indices = []
    
    for idx, row in df.iterrows():
        br = str(row['base_reading'])
        mr = str(row['ms_reading'])
        
        # Keep variants where BOTH readings consist entirely of function words, 
        # or OMIT/ADD involving only function words.
        b_words = [] if br == '[ADD]' else br.split()
        m_words = [] if mr == '[OMIT]' else mr.split()
        
        all_words = b_words + m_words
        if not all_words: 
            continue
            
        is_all_func = all(is_function_word(w) for w in all_words)
        if is_all_func:
            filtered_indices.append(idx)
            
    return df.iloc[filtered_indices].copy()

def apply_content_masking(df):
    masked_df = df.copy()
    
    def mask_text(text):
        if pd.isna(text) or text in ['[ADD]', '[OMIT]']: return text
        words = text.split()
        masked_words = [w if is_function_word(w) else 'CONTENT' for w in words]
        return " ".join(masked_words)
        
    masked_df['base_reading'] = masked_df['base_reading'].apply(mask_text)
    masked_df['ms_reading'] = masked_df['ms_reading'].apply(mask_text)
    masked_df['base_context_10w'] = masked_df['base_context_10w'].apply(mask_text)
    masked_df['ms_context_10w'] = masked_df['ms_context_10w'].apply(mask_text)
    
    return masked_df

def main():
    base_file = "data/variants_full_john_B.csv"
    if not os.path.exists(base_file):
        print(f"Base file {base_file} not found. Please run baseline B extraction first.")
        return
        
    df = pd.read_csv(base_file)
    print(f"Loaded original full corpus: {len(df)} variants.")
    
    # 1. Function Words Only dataset
    func_df = apply_function_words_filter(df)
    func_file = "data/variants_ablation_func_words.csv"
    func_df.to_csv(func_file, index=False)
    print(f"Created Function Words Only dataset: {len(func_df)} variants -> {func_file}")
    
    # 2. Content Masked dataset
    masked_df = apply_content_masking(df)
    masked_file = "data/variants_ablation_masked.csv"
    masked_df.to_csv(masked_file, index=False)
    print(f"Created Content Masked dataset: {len(masked_df)} variants -> {masked_file}")

if __name__ == "__main__":
    main()
