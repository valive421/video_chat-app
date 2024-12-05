from django.db import models

class Maze(models.Model):
    maze_data = models.TextField()  # Assuming maze is stored as JSON
