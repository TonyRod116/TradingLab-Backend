from django.db import models
from users.models import User

# Create your models here.
class Strategy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
