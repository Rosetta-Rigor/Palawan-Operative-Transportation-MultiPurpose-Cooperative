from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from coop import views
from coop.views import custom_logout

urlpatterns = [
    path('accounts/<int:user_id>/edit/', views.edit_account, name='edit_account'),
    path("admin/user-approvals/", views.user_approvals, name="user_approvals"),
    path("admin/approve-user/<int:user_id>/", views.approve_user, name="approve_user"),
    path('admin/profile/edit/', views.admin_profile_edit, name='admin_profile_edit'),
    path("user/documents/upload/", views.user_upload_document, name="user_upload_document"),
    path("documents/approve/", views.approve_documents, name="approve_documents"),
    path("documents/approve/<int:doc_id>/", views.approve_document, name="approve_document"),
    path("documents/reject/<int:doc_id>/", views.reject_document, name="reject_document"),
    path("broadcast/", views.broadcast, name="broadcast"),
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    
    # BATCH
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),

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
    path("documents/add/", views.document_add, name="document_add"),
    path("documents/<int:pk>/", views.DocumentDetailView.as_view(), name="document_detail"),
    path("documents/<int:pk>/edit/", views.DocumentUpdateView.as_view(), name="document_edit"),
    path("documents/<int:pk>/delete/", views.DocumentDeleteView.as_view(), name="document_delete"),
    path("documents/<int:pk>/add_entry/", views.DocumentEntryCreateView.as_view(), name="document_entry_add"),

    # MEMBER RENEWAL
    path('members/<int:pk>/renew/', views.member_renewal_update, name='member_renewal_update'),

    # USER PAGES
    path("user_home/", views.user_home, name="user_home"),
    path('user/profile/', views.user_profile, name='user_profile'),
    path('user/announcements/', views.user_announcements, name='user_announcements'),
    path('user/documents/', views.user_documents, name='user_documents'),
    path('profile/', views.my_profile, name='my_profile'),
    path('user/profile/edit/', views.my_profile, name='user_profile_edit'),

    # AUTH
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/<int:user_id>/deactivate/', views.deactivate_account, name='deactivate_account'),
    path('accounts/<int:user_id>/activate/', views.activate_account, name='activate_account'),
    path('accounts/<int:user_id>/edit/', views.edit_account, name='edit_account'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('members/<int:pk>/view/', views.member_view, name='member_view'),
    path('api/members/search/', views.member_search_api, name='member_search_api'),
    path('api/user/document-entry-count/', views.user_document_entry_count_api, name='user_document_entry_count_api'),
    path('api/pending_counts/', views.pending_counts_api, name='api_pending_counts'),
    path('api/users/search/', views.user_search_api, name='user_search_api'),
    path('api/vehicle-member-select2/', views.vehicle_member_select2_api, name='vehicle_member_select2_api'),
    path('user/vehicles/', views.user_vehicles, name='user_vehicles'),
    path('payments/', views.payment_year_list, name='payment_year_list'),
    path('payments/<int:year_id>/', views.payment_year_detail, name='payment_year_detail'),
    path('payments/<int:year_id>/add-type/', views.add_payment_type, name='add_payment_type'),
    path('payments/<int:year_id>/add-entry/', views.add_payment_entry, name='add_payment_entry'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
