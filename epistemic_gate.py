"""Conservative actor knowledge matching; similarity never establishes a fact.

Paraphrases must be explicitly added to the actor ledger after semantic review.
The caller remains responsible for extracting every material claim from prose.
"""
import re
import unicodedata


def canonical_fact(value):
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.findall(r"[\w'-]+", text))


def fact_supported(claim, ledger):
    fact = canonical_fact(claim)
    return bool(fact) and isinstance(ledger, list) and any(
        canonical_fact(item) == fact for item in ledger if isinstance(item, str)
    )
