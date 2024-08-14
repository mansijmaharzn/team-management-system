from django.db import models
from django.contrib.auth.models import User


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(User, related_name="teams")
    slug = models.SlugField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(
        User, related_name="created_teams", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.name} by {self.created_by.username}"


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    team = models.ForeignKey(Team, related_name="tasks", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(
        User,
        related_name="assigned_tasks",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    due_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return self.title
