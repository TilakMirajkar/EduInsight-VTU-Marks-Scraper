from django.urls import path
from .apiviews import ScraperAPIView

urlpatterns = [
    # path('', automate, name='automate'),
    # path('insights/', insights, name='insights'),
    path('', ScraperAPIView.as_view(), name='form-api'),
]