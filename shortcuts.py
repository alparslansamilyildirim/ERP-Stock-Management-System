"""
shortcuts.py

This module provides functions to bind keyboard shortcuts for fullscreen, undo, and reload actions
in the ERP application's GUI windows.
"""

def toggle_fullscreen_for_window(window, state_attr='_is_fullscreen'):
    """
    Toggle fullscreen mode for any Tkinter window (Tk or Toplevel).
    Tracks fullscreen state using a custom window attribute.
    """
    is_fullscreen = getattr(window, state_attr, False)
    is_fullscreen = not is_fullscreen
    setattr(window, state_attr, is_fullscreen)
    window.attributes("-fullscreen", is_fullscreen)


def bind_fullscreen_shortcuts(window):
    """
    Bind F11 and Ctrl+Cmd+F to toggle fullscreen for the given window.
    """
    window.bind('<F11>', lambda e: toggle_fullscreen_for_window(window))
    window.bind('<Control-Command-f>', lambda e: toggle_fullscreen_for_window(window))


def bind_common_shortcuts(window, undo_callback=None, reload_callback=None):
    """
    Bind common shortcuts (undo, reload) to the given window.
    Pass the callback functions for undo and reload actions.
    """
    if undo_callback:
        window.bind('<Command-z>', undo_callback)
        window.bind('<Control-z>', undo_callback)
    if reload_callback:
        window.bind('<F5>', reload_callback)
        window.bind('<Command-r>', reload_callback)
        window.bind('<Control-r>', reload_callback) 