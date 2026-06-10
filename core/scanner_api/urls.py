from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('analyze/', view.analyze_password, name='analyze_password'),
    
]
