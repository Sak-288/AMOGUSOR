from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.file.name