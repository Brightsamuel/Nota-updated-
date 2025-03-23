from kivymd.app import MDApp

def track_event(event_type, **kwargs):
    """
    Utility function to track events from anywhere in the app.
    
    Args:
        event_type (str): The type of event to track
        **kwargs: Additional event data
    """
    app = MDApp.get_running_app()
    if hasattr(app, 'root'):
        # Find the TagManager instance
        for screen in app.root.screens:
            if hasattr(screen, 'tag_manager'):
                screen.tag_manager.track_event(event_type, **kwargs)
                return
    
    print(f"Warning: Unable to track event {event_type}, TagManager not found")