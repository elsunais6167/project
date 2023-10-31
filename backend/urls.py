from . import views
from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='home'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('login/', views.signin, name='login'),
    path('register/', views.Register, name='register'),
    path('password_reset/', views.custom_password_reset, name='password_reset'),
    path('password_reset_confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('change_password/', views.change_password, name='change_password'),
    path('admin-cop/', views.cop_admin, name='admin-cop'),
    path('organisations/', views.org, name='organisations'),
    path('logout/', views.logout, name='logout'),
    path('org_prof/<str:pk>/', views.org_prof, name='org_prof'),
    path('accreditation/', views.accreditation, name='accreditation'),
    path('side_event/', views.side_event, name='side_event'),
    path('event/<str:pk>/', views.event_profile, name='event'),
    path('announcement/', views.announcement, name='announcement'),
    path('event_list/', views.event_list, name='event_list'),
    path('event_view/<str:pk>/', views.event_view, name='event_view'),
    path('report_list', views.report_list, name='report_list'),
    path('report_view/<str:pk>/', views.report_view, name='report_view'),
    path('org_dashbord', views.org_dashboard, name='org_dashbord'), 
    path('org_profile/', views.org_register, name='org_profile'),
    path('org_update/', views.org_update, name='org_update'),
    path('org_event/', views.org_event, name='org_event'),
    path('org_event_profile/<str:pk>/', views.org_event_profile, name='org_event_profile'),
    path('activist/', views.activist_dashboard, name='activist'),

]