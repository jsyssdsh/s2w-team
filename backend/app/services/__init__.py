"""Deterministic calculation services for S2W.

Every function here is pure Python (no DB I/O, no LLM calls) so it can be
unit tested directly against the example tables in planning/SPEC.md section 5.
Routes fetch rows via app.db, pass them through these functions, then hand
the results to app.llm for natural-language explanation. No number that
appears in an LLM output is computed inside the LLM -- it always originates
here.
"""
