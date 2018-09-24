class GameStats:

    def __init__(self, ai_settings):
        """Track statistics for Alien Invasion"""
        self.ai_settings = ai_settings
        self.game_active = False
        self.reset_stats()

    def reset_stats(self):
        """Initialize statistics that can change during the game."""
        self.ships_left = self.ai_settings.ships_limit



