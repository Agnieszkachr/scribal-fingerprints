"""
Function Word List
==================

Closed-class Greek words (conjunctions and particles, prepositions, the
article, pronouns, negations) in the unaccented lower-case orthography of the
transcriptions, including elided forms. Used by the feature-isolation study to
select function-word-only variants and to decide which words content masking
hides. Shared by the SCRIPTA pipeline and the scribal-fingerprints repository.
"""

from typing import Set

from src.utils.token_normalizer import clean_surface

# Heuristic list of Greek function words (articles, pronouns, particles,
# conjunctions, prepositions, negations) in the unaccented orthography of the
# transcriptions.
FUNCTION_WORDS: Set[str] = {
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


def is_function_word(word: str) -> bool:
    """True if *word* (Greek, possibly accented) is a function word."""
    return clean_surface(str(word)) in FUNCTION_WORDS
