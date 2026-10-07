# Douyin Daily Report Integration

This integration preserves the supplied daily report workflow assets. It provides the source Skill instructions, HTML template, sample JSON, and shareable prompt. The sample is a structural fixture only and is not real account data.

The ZIP did not include an executable renderer. The repository adds `scripts/render_daily_report.py` as a minimal field-substitution renderer; it writes a new output file and never overwrites an existing report.
