
from django.contrib import admin
from django.urls import path, include
from coop import views 
from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
# ...existing code...
urlpatterns = [
    # Removed old admin_approve_documents and admin_approve_document patterns
    path("user/documents/upload/", views.user_upload_document, name="user_upload_document"),
    path("documents/approve/", views.approve_documents, name="approve_documents"),
    path("documents/approve/<int:doc_id>/", views.approve_document, name="approve_document"),
    path("broadcast/", views.broadcast, name="broadcast"),
    path("admin/", admin.site.urls),
    # Removed old admin_broadcast pattern
    path("", views.home, name="home"),
    path("members/", views.MemberListView.as_view(), name="member-list"),
    path("members/add/", views.member_add, name="member-add"),
    path("vehicles/", views.VehicleListView.as_view(), name="vehicle-list"),
    path("vehicles/add/", views.VehicleCreateView.as_view(), name="vehicle-add"),
    path("user_home/", views.user_home, name="user_home"),
    path('user/profile/', views.user_profile, name='user_profile'),
    path('user/announcements/', views.user_announcements, name='user_announcements'),
    path('user/documents/', views.user_documents, name='user_documents'),

    path('login/', views.custom_login, name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
    path("members/<int:pk>/edit/", views.member_edit, name="member-edit"),
    path("members/<int:pk>/delete/", views.MemberDeleteView.as_view(), name="member-delete"),
    path("vehicles/<int:pk>/edit/", views.VehicleUpdateView.as_view(), name="vehicle-edit"),
    path("vehicles/<int:pk>/delete/", views.VehicleDeleteView.as_view(), name="vehicle-delete"),
    path("documents/", views.DocumentListView.as_view(), name="document-list"),
    path("documents/add/", views.DocumentCreateView.as_view(), name="document-add"),
    path('members/<int:pk>/renew/', views.member_renewal_update, name='member-renewal-update'),
    path('documents/add/<int:vehicle_id>/<str:renewal_date>/', views.document_add_renewal, name='document-add-renewal'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
