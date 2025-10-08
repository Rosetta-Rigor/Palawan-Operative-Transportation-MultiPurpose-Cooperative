from django.contrib import admin
from django.urls import path, include
from coop import views 
from django.urls import path, re_path
from coop.views import custom_logout
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/user-approvals/", views.user_approvals, name="user_approvals"),
    path("admin/approve-user/<int:user_id>/", views.approve_user, name="approve_user"),
    path("user/documents/upload/", views.user_upload_document, name="user_upload_document"),
    path("documents/approve/", views.approve_documents, name="approve_documents"),
    path("documents/approve/<int:doc_id>/", views.approve_document, name="approve_document"),
    path("broadcast/", views.broadcast, name="broadcast"),
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),

    # MEMBER CRUD
    path("members/", views.MemberListView.as_view(), name="member_list"),
    path("members/add/", views.member_add, name="member_add"),
    path("members/<int:pk>/edit/", views.member_edit, name="member_edit"),
    path("members/<int:pk>/delete/", views.MemberDeleteView.as_view(), name="member_confirm_delete"),
    path("members/<int:pk>/dormant_toggle/", views.member_dormant_toggle, name="member_dormant_toggle"),

    # VEHICLE CRUD
    path("vehicles/", views.VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/add/", views.VehicleCreateView.as_view(), name="vehicle_add"),
    path("vehicles/<int:pk>/edit/", views.VehicleUpdateView.as_view(), name="vehicle_edit"),
    path("vehicles/<int:pk>/delete/", views.VehicleDeleteView.as_view(), name="vehicle_delete"),

    # DOCUMENT CRUD
    path("documents/", views.DocumentListView.as_view(), name="document_list"),
    path("documents/add/", views.DocumentCreateView.as_view(), name="document_add"),
    path('documents/add/<int:vehicle_id>/<str:renewal_date>/', views.document_add_renewal, name='document_add_renewal'),

    # MEMBER RENEWAL
    path('members/<int:pk>/renew/', views.member_renewal_update, name='member_renewal_update'),

    # USER PAGES
    path("user_home/", views.user_home, name="user_home"),
    path('user/profile/', views.user_profile, name='user_profile'),
    path('user/announcements/', views.user_announcements, name='user_announcements'),
    path('user/documents/', views.user_documents, name='user_documents'),

    # AUTH
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', custom_logout, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
