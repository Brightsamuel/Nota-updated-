from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import DictProperty, BooleanProperty
from kivy.clock import Clock
from kivy.app import App
import json
import requests

class TagManager(MDBoxLayout):
    consent_prefs = DictProperty({})
    analytics_loaded = BooleanProperty(False)
    marketing_loaded = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_consent()
        self.pending_events = []

    def load_consent(self):
        try:
            app = App.get_running_app()
            if hasattr(app, 'config'):
                try:
                    consent_json = app.config.get('tagmanager', 'consent')
                    if consent_json:
                        self.consent_prefs = json.loads(consent_json)
                except:
                    self.consent_prefs = {}
        except:
            self.consent_prefs = {}

    def save_consent(self):
        app = App.get_running_app()
        if hasattr(app, 'config'):
            app.config.set('tagmanager', 'consent', json.dumps(self.consent_prefs))
            app.config.write()
        
        # Load appropriate tags based on consent
        if self.consent_prefs.get('analytics'):
            self.load_analytics()
        if self.consent_prefs.get('marketing'):
            self.load_marketing()
            
        # Process queued events
        Clock.schedule_once(lambda dt: self.process_pending_events())

    def track_event(self, event_type, **kwargs):
        if self.analytics_loaded or self.marketing_loaded:
            self.send_event(event_type, **kwargs)
        else:
            self.pending_events.append((event_type, kwargs))

    def send_event(self, event_type, **kwargs):
        # Implement actual event tracking here
        print(f"Tracking event: {event_type} with data: {kwargs}")
        
        # Example: Send to analytics endpoint
        if self.analytics_loaded:
            try:
                requests.post(
                    'https://analytics.example.com/collect',
                    data={'event': event_type, **kwargs}
                )
            except Exception as e:
                print(f"Error sending analytics: {e}")

    def process_pending_events(self):
        for event_type, kwargs in self.pending_events:
            self.send_event(event_type, **kwargs)
        self.pending_events = []

    def load_analytics(self):
        # Initialize analytics SDK
        self.analytics_loaded = True
        print("Analytics loaded")

    def load_marketing(self):
        # Initialize marketing SDK
        self.marketing_loaded = True
        print("Marketing loaded")

class ConsentPopupContent(BoxLayout):
    def __init__(self, tag_manager, **kwargs):
        super().__init__(**kwargs)
        self.tag_manager = tag_manager
        self.orientation = 'vertical'
        self.spacing = 15

    def accept_all(self):
        self.tag_manager.consent_prefs = {
            'analytics': True,
            'marketing': True
        }
        self.tag_manager.save_consent()
        self.tag_manager.popup.dismiss()

    def reject_all(self):
        self.tag_manager.consent_prefs = {
            'analytics': False,
            'marketing': False
        }
        self.tag_manager.save_consent()
        self.tag_manager.popup.dismiss()