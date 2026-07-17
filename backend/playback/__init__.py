"""Playback package.

The package intentionally avoids eager re-exports so importers can depend on
individual playback modules without triggering circular imports during backend
startup.
"""
