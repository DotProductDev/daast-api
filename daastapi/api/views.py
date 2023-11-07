from django.shortcuts import render

# Create your views here.

# We should use ETag and last modified timestamps for serving manifests.
# https://docs.djangoproject.com/en/4.2/topics/conditional-view-processing/