"""Sample Builder — Website content generation prompt."""

SAMPLE_BUILDER_PROMPT = """Business Name: {name}
Address: {address}
Category: {category}
Extra Google data: {google_data}

Generate professional, engaging website content for this local business.
Always sound human, local, and authentic. Avoid generic phrases.

Return ONLY valid JSON with these keys:
{{
  "headline": "Hero headline, max 8 words",
  "tagline": "Subheadline, max 15 words",
  "about": "3-sentence about paragraph",
  "services": [{{"name": "...", "description": "...", "price_hint": "..."}}],
  "cta_text": "Call-to-action button text",
  "color_scheme": {{"primary": "#hex", "secondary": "#hex", "accent": "#hex"}},
  "seo_title": "SEO-optimized page title",
  "meta_description": "155 char meta description"
}}"""
