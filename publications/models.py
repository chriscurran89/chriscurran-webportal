from django.db import models

class Publication(models.Model):
    title = models.CharField(max_length=100)
    publication_date = models.DateField()
    abstract = models.TextField()
    journal_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    weblink = models.URLField(max_length=200)

