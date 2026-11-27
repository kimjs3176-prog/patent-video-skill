"""The HyperFrames version this skill is checked and rendered with, and the npx command that runs it."""
import os

NPX = "npx.cmd" if os.name == "nt" else "npx"
HF = "hyperframes@0.9.103"
# The HyperFrames CLI reports usage to PostHog unless this is set; the skill's runs (check, render) leave it off.
# A value the user set themselves is kept.
os.environ.setdefault("HYPERFRAMES_NO_TELEMETRY", "1")
