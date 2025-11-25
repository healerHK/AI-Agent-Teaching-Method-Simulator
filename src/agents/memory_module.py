class MemoryModule:
    """
    Simple conceptual internal memory for student agents.
    Tracks knowledge, misconceptions, and engagement over time.
    """

    def __init__(self):
        self.knowledge = 0.0
        self.misconceptions = 1.0
        self.engagement = 0.5
        self.history = []

    def update(self, knowledge_delta, misconception_delta, engagement_delta):
        self.knowledge = max(0, min(1, self.knowledge + knowledge_delta))
        self.misconceptions = max(0, min(1, self.misconceptions + misconception_delta))
        self.engagement = max(0, min(1, self.engagement + engagement_delta))

    def log(self, event: str):
        self.history.append(event)
