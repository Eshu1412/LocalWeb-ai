"""Discovery Agent — Category expansion prompt."""

DISCOVERY_CATEGORY_PROMPT = """Given the business category '{category}', list 10 related search terms
a person would use to find this type of business on Google Maps.
Return as a JSON array of strings. Be specific to local search intent.
Example: 'restaurant' → ['best restaurant near me', 'local diner', 'family restaurant', ...]"""
