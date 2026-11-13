"""The HyperFrames version this skill is checked and rendered with, and the npx command that runs it."""
import os

NPX = "npx.cmd" if os.name == "nt" else "npx"
HF = "hyperframes@0.8.207"
