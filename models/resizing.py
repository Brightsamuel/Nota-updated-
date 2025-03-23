from kivy.core.window import Window

def on_window_resize(self, window, width, height):
    """Adjust layout when window is resized"""
    #Recalculate positions and sizes based on new dimensions
    return True

def on_size(self, *args):
    """Handle window size events"""
    #Update your layout based on the new window size
    Window.bind(on_resize=self.on_window_resize)
