"""Workarounds for KivyMD 2.0 issues. Import this before creating any widgets.

Lazy ripple framebuffers
------------------------
Every KivyMD 2.0 widget with a touch ripple (buttons, list items, cards,
switches) creates an Fbo and compiles the ripple shader in its constructor.
On some GPUs that takes ~100 ms per widget, so a list of 20 note cards took
seconds to build. The ripple code already skips drawing while ``fbo`` is None,
so we create the Fbo on the first touch instead of up front.
"""
from kivymd.uix.behaviors.ripple_behavior import M3CommonRipple

_create_fbos = M3CommonRipple.init_fbos
_start_ripple = M3CommonRipple.call_ripple_animation_methods


def _defer_fbos(self):
    self._phase = 0.0
    self.ripple_pos = (0, 0)
    self.fbo = None


def _start_ripple_with_fbos(self, touch):
    if self.fbo is None:
        _create_fbos(self)
    _start_ripple(self, touch)


M3CommonRipple.init_fbos = _defer_fbos
M3CommonRipple.call_ripple_animation_methods = _start_ripple_with_fbos
