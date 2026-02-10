class KeywordDetector:
    def __init__(self):
        self.keywords = [
            "help", "help me", "please help", "save me", "someone help",
            "stop", "leave me", "leave me alone", "go away",
            "don’t follow me", "stop following me",
            "i’m in danger", "i need help",
            "call police", "call the police", "police please", "emergency"
        ]

    def detect(self, text):
        detected = [k for k in self.keywords if k in text]
        return detected, len(detected) > 0
