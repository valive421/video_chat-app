from django.db import models
import json

# Model to store the maze and player positions
class GameState(models.Model):
    maze = models.TextField()  # Store the maze as a JSON string
    player_positions = models.JSONField()  # Store player positions as a JSON object
