from django.db import models

# โครงสร้างตาราง
class Employee(models.Model):
    name = models.CharField(max_length=100)
 
    def __str__(self):
        return self.name 
