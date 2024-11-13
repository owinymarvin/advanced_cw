from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='get_started'),
    path('signin/', views.signin, name='signin'),
    # path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path("home/", views.chat_view, name="home"),
    path('query/history/', views.QueryHistory, name='query_history'),
    path('query/FAQ/', views.FAQ, name='FAQ'),
    path('Export/PDF/', views.ExportPDF, name='export_pdf'),
    path('Export/CSV/', views.ExportCSV, name='export_csv'),



    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
