from django.views.decorators.http import require_POST
# ==== User Approval (Admin) ====
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from matplotlib.style import context
from .models import Batch, User, Member
import json
from django.utils import timezone
from datetime import timedelta, date, datetime

from django.db import models
from django.contrib import messages
from .models import Announcement
from .forms import AnnouncementForm
from django.db.models import Q

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from django.contrib.auth import get_user_model, login as auth_login
from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import Http404
import qrcode
from io import BytesIO
from .models import QRLoginToken
from pyzbar.pyzbar import decode
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.db.models import Sum, Q

@user_passes_test(lambda u: u.is_staff)
def user_approvals(request):
    User = get_user_model()
    users = User.objects.filter(is_active=False, role='client')
    members = Member.objects.all()
    return render(request, 'user_approvals.html', {'users': users, 'members': members})

@user_passes_test(lambda u: u.is_staff)
@require_POST
def approve_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    member_id = request.POST.get('member_id')
    member = get_object_or_404(Member, pk=member_id)
    # Tie both sides of the relationship
    user.member_profile = member
    member.user_account = user
    user.is_active = True
    user.save()
    member.save()
    return redirect('user_approvals')
from django.contrib.auth import get_user_model
from .forms import CustomUserRegistrationForm
# ==== Registration View ====
def register(request):
    from django.contrib.auth import logout
    from django.contrib.sessions.models import Session
    from .notifications import notify_all_staff
    
    # Only handle POST requests for registration
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require admin approval
            user.role = 'client'  # Set role to client
            user.save()
            
            # Create notification for all staff
            notify_all_staff(
                title="New User Registration Pending",
                message=f"{user.full_name} ({user.username}) has registered and is awaiting account approval.",
                category='user_registration',
                priority='high',
                action_url='/accounts/',
                action_text='Review & Approve'
            )
            
            messages.success(request, 'Registration successful! Please wait for admin approval.')
            return redirect('login')
        else:
            # Form has validation errors - show specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f"{error}")
                    else:
                        messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
            
            # Always redirect back to login page to avoid URL conflicts
            return redirect('login')
    
    # GET requests should not access /register/ directly
    # Redirect to login page where registration form is embedded
    return redirect('login')
# ==== Member Dormant/Activate Toggle ====
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def member_dormant_toggle(request, pk):
    """
    Toggle dormant/activate status for a member (listview action button).
    """
    member = get_object_or_404(Member, pk=pk)
    member.is_dormant = not member.is_dormant
    member.save()
    return redirect('member_list')

# ==== Imports ====
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
# ==== Custom Logout View ====
def custom_logout(request):
    """
    Logs out the user and flushes the session completely.
    """
    logout(request)
    request.session.flush()
    return redirect('login')
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Member, Vehicle, Document
from .forms import MemberForm, VehicleForm, DocumentForm

# ==== Inline Formset for Member-Vehicle ====
# This formset allows you to manage Vehicle objects related to a Member
# on the same form (add/edit member and their vehicles together).
VehicleFormSet = inlineformset_factory(
    Member, Vehicle, form=VehicleForm, fields="__all__", extra=1, can_delete=True
)

# ==== Function-based Views ====

@login_required
def member_add(request):
    """
    Handles creation of a new Member.
    - Accepts POST data for MemberForm and VehicleFormSet.
    - Assigns an existing vehicle to the member if selected in the form.
    - Saves any new vehicles entered in the formset.
    - Optionally creates a Document and DocumentEntry if provided.
    - Redirects to member list on success.
    """
    if request.method == "POST":
        member_form = MemberForm(request.POST)
        if member_form.is_valid():
            member = member_form.save()

            # Get selected existing vehicle from the form (optional)
            selected_vehicle = member_form.cleaned_data.get('vehicle')

            # Handle new vehicle creation via formset
            formset = VehicleFormSet(request.POST, instance=member)
            if formset.is_valid():
                # Validate duplicates between selected_vehicle, existing member vehicles and formset entries
                member_existing_plates = set(v.plate_number for v in member.vehicles.all())
                plate_set = set(member_existing_plates)
                if selected_vehicle:
                    plate_set.add(selected_vehicle.plate_number)

                duplicate_found = False
                for f in formset.forms:
                    if not hasattr(f, 'cleaned_data'):
                        continue
                    cd = f.cleaned_data
                    if not cd or cd.get('DELETE', False):
                        continue
                    plate = cd.get('plate_number')
                    inst = getattr(f, 'instance', None)
                    # If this form is editing an existing vehicle and the plate is unchanged, allow it
                    if inst and getattr(inst, 'pk', None):
                        existing_plate = getattr(inst, 'plate_number', None)
                        if existing_plate and plate == existing_plate:
                            plate_set.add(plate)
                            continue
                    if plate:
                        if plate in plate_set:
                            f.add_error('plate_number', 'Vehicle with this Plate number already exists.')
                            duplicate_found = True
                        else:
                            plate_set.add(plate)
                if duplicate_found:
                    # Re-render with errors
                    return render(request, "member_add.html", {"form": member_form, "formset": formset})

                # Save formset and attach selected existing vehicle if provided
                saved_vehicles = formset.save()
                if selected_vehicle:
                    # Untie from previous member if necessary
                    if selected_vehicle.member and selected_vehicle.member != member:
                        prev = selected_vehicle.member
                        selected_vehicle.member = member
                    else:
                        selected_vehicle.member = member
                    selected_vehicle.save()
                
                # Handle optional document submission (Step 3)
                tin = request.POST.get('tin', '').strip()
                renewal_date_str = request.POST.get('renewal_date', '').strip()
                official_receipt = request.FILES.get('official_receipt')
                certificate_of_registration = request.FILES.get('certificate_of_registration')
                
                # Only create document if TIN is provided
                if tin:
                    # Get the first vehicle (either from formset or selected_vehicle)
                    target_vehicle = None
                    if saved_vehicles:
                        target_vehicle = saved_vehicles[0]
                    elif selected_vehicle:
                        target_vehicle = selected_vehicle
                    
                    if target_vehicle:
                        # Create Document
                        document = Document.objects.create(
                            tin=tin,
                            vehicle=target_vehicle
                        )
                        
                        # Create DocumentEntry if renewal_date and files are provided
                        if renewal_date_str:
                            from datetime import datetime
                            try:
                                renewal_date = datetime.strptime(renewal_date_str, '%Y-%m-%d').date()
                                
                                DocumentEntry.objects.create(
                                    document=document,
                                    renewal_date=renewal_date,
                                    official_receipt=official_receipt,
                                    certificate_of_registration=certificate_of_registration,
                                    status='pending'
                                )
                                messages.success(request, 'Member, vehicle, and document created successfully!')
                            except ValueError:
                                messages.warning(request, 'Member and vehicle created, but document renewal date was invalid.')
                        else:
                            messages.success(request, 'Member and vehicle created successfully!')
                    else:
                        messages.warning(request, 'Member created, but no vehicle available to attach document.')
                else:
                    messages.success(request, 'Member created successfully!')
                    
                return redirect("member_list")
        else:
            formset = VehicleFormSet(request.POST)
    else:
        member_form = MemberForm()
        formset = VehicleFormSet()
    return render(request, "member_add.html", {"form": member_form, "formset": formset})
    
@login_required
def member_list(request):
    """
    List members with AJAX search + pagination.
    Returns full page for normal requests and JSON { html, pagination_html } for AJAX.
    """
    q = (request.GET.get('q') or '').strip()
    page_number = request.GET.get('page', 1)

    qs = Member.objects.select_related('user_account', 'batch').prefetch_related('vehicles').order_by('full_name')

    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(vehicles__plate_number__icontains=q)).distinct()

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'object_list': list(page_obj.object_list),
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'q': q,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        rows_html = render_to_string('includes/member_table_rows.html', context, request=request)
        pagination_html = render_to_string('includes/pagination.html', context, request=request)
        return JsonResponse({'html': rows_html, 'pagination_html': pagination_html})

    # normal render
    return render(request, 'memberlist.html', context)

# ==== User Views ====

@login_required
def user_home(request):
    """
    Renders the home page for logged-in users (user side).
    Only users with role 'client' can access.
    """
    if not hasattr(request.user, 'role') or request.user.role != 'client':
        from django.contrib import messages
        messages.error(request, "You do not have access to the user portal.")
        return redirect('login')
    return render(request, "user_home.html")

# ==== User-Side Views ====

@login_required
def user_profile(request):
    """
    Display the logged-in user's profile information.
    """
    user = request.user
    return render(request, "user_profile.html", {"user": user})

@login_required
def user_announcements(request):
    """
    Display announcements for the user side (placeholder content).
    """
    return render(request, "user_announcements.html")

@login_required
def user_documents(request):
    """
    Display documents for the user side (placeholder content).
    """
    return render(request, "user_documents.html")

@login_required
def user_payments(request):
    """
    Display list of payment years as cards for the logged-in user.
    Users can click on a year card to view detailed payments for that year.
    """
    user = request.user
    member = getattr(user, 'member_profile', None)
    
    if not member:
        messages.warning(request, "Your account is not linked to a member profile. Please contact the administrator to link your account.")
        return render(request, "user_payments.html", {'member': None, 'payment_years': []})
    
    # Get all payment years
    payment_years = PaymentYear.objects.all().order_by('-year')
    
    # Build year summary data
    years_data = []
    for year in payment_years:
        # Count total payment types for this year (from_members + other)
        from_members_count = PaymentType.objects.filter(
            year=year, 
            payment_type='from_members'
        ).count()
        
        other_count = PaymentType.objects.filter(
            year=year, 
            payment_type='other'
        ).count()
        
        # Count member's payments for this year
        member_payments = PaymentEntry.objects.filter(
            payment_type__year=year,
            member=member
        ).exclude(amount_paid=0).count()
        
        # Calculate total amount paid by member for this year
        from django.db.models import Sum
        total_paid = PaymentEntry.objects.filter(
            payment_type__year=year,
            member=member
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        years_data.append({
            'year': year,
            'from_members_count': from_members_count,
            'other_count': other_count,
            'member_payments_count': member_payments,
            'total_paid': total_paid,
        })
    
    context = {
        'member': member,
        'payment_years': years_data,
    }
    return render(request, "user_payments.html", context)


@login_required
def user_payment_year_detail(request, year_id):
    """
    Display detailed payment records for a specific year.
    Shows both "From Members" and "Other" payment types with monthly breakdown.
    """
    user = request.user
    member = getattr(user, 'member_profile', None)
    
    if not member:
        messages.warning(request, "Your account is not linked to a member profile. Please contact the administrator.")
        return redirect('user_payments')
    
    # Get the specific payment year
    year = get_object_or_404(PaymentYear, id=year_id)
    
    # Get "From Members" payment types
    from_members_types = PaymentType.objects.filter(
        year=year, 
        payment_type='from_members'
    ).order_by('name')
    
    # Get "Other" payment types
    other_types = PaymentType.objects.filter(
        year=year, 
        payment_type='other'
    ).order_by('name')
    
    # Build payment data for "From Members"
    from_members_data = []
    for payment_type in from_members_types:
        monthly_totals = []
        for month_num in range(1, 13):
            # Aggregate all payment entries for this payment type, member, and month
            total = PaymentEntry.objects.filter(
                payment_type=payment_type,
                member=member,
                month=month_num
            ).aggregate(total=Sum('amount_paid'))['total']
            
            # total will be None if no payments exist, or the sum if they do
            monthly_totals.append(total)
        
        from_members_data.append({
            'payment_type': payment_type,
            'monthly_totals': monthly_totals,
        })
    
    # Build payment data for "Other"
    other_data = []
    for payment_type in other_types:
        monthly_totals = []
        for month_num in range(1, 13):
            # Aggregate all payment entries for this payment type, member, and month
            total = PaymentEntry.objects.filter(
                payment_type=payment_type,
                member=member,
                month=month_num
            ).aggregate(total=Sum('amount_paid'))['total']
            
            # total will be None if no payments exist, or the sum if they do
            monthly_totals.append(total)
        
        other_data.append({
            'payment_type': payment_type,
            'monthly_totals': monthly_totals,
        })
    
    # Calculate totals (Sum is already imported at module level)
    total_paid = PaymentEntry.objects.filter(
        payment_type__year=year,
        member=member
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    context = {
        'member': member,
        'year': year,
        'from_members_data': from_members_data,
        'other_data': other_data,
        'total_paid': total_paid,
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    }
    return render(request, "user_payment_year_detail.html", context)


@login_required
def member_edit(request, pk):
    """
    Handles editing of an existing Member.
    - Accepts POST data for MemberForm and VehicleFormSet.
    - Updates assigned vehicle if changed.
    - Updates related vehicles via formset.
    - Redirects to member list on success.
    """
    member = get_object_or_404(Member, pk=pk)
    if request.method == "POST":
        member_form = MemberForm(request.POST, instance=member)
        formset = VehicleFormSet(request.POST, instance=member)
        if member_form.is_valid() and formset.is_valid():
            member = member_form.save()
            selected_vehicle = member_form.cleaned_data.get('vehicle')

            # Validate duplicates between selected_vehicle, existing member vehicles and formset entries
            member_existing_plates = set(v.plate_number for v in member.vehicles.all())
            plate_set = set(member_existing_plates)
            if selected_vehicle:
                plate_set.add(selected_vehicle.plate_number)

            duplicate_found = False
            for f in formset.forms:
                if not hasattr(f, 'cleaned_data'):
                    continue
                cd = f.cleaned_data
                if not cd or cd.get('DELETE', False):
                    continue
                plate = cd.get('plate_number')
                inst = getattr(f, 'instance', None)
                # If editing an existing vehicle and plate unchanged, allow it
                if inst and getattr(inst, 'pk', None):
                    existing_plate = getattr(inst, 'plate_number', None)
                    if existing_plate and plate == existing_plate:
                        plate_set.add(plate)
                        continue
                if plate:
                    if plate in plate_set:
                        f.add_error('plate_number', 'Vehicle with this Plate number already exists.')
                        duplicate_found = True
                    else:
                        plate_set.add(plate)
            if duplicate_found:
                return render(request, "member_add.html", {"form": member_form, "formset": formset})

            formset.save()

            if selected_vehicle:
                # Attach selected existing vehicle to this member
                if selected_vehicle.member and selected_vehicle.member != member:
                    # reassign ownership
                    selected_vehicle.member = member
                else:
                    selected_vehicle.member = member
                selected_vehicle.save()

            return redirect("member_list")
    else:
        member_form = MemberForm(instance=member)
        formset = VehicleFormSet(instance=member)
    return render(request, "member_add.html", {"form": member_form, "formset": formset})

@login_required
def member_renewal_update(request, pk):
    """
    Updates the member's renewal date by +1 year and redirects to add a new document for their vehicle.
    """
    member = get_object_or_404(Member, pk=pk)
    old_date = member.renewal_date
    new_date = old_date.replace(year=old_date.year + 1)
    member.renewal_date = new_date
    member.save()
    # Redirect to add document for this vehicle, pre-filling renewal_date
    vehicle = getattr(member, 'vehicle', None)
    if vehicle:
        return redirect('document-add-renewal', vehicle_id=vehicle.id, renewal_date=new_date)
    return redirect('member_list')

@login_required
def document_add_renewal(request, vehicle_id, renewal_date):
    """
    Add a new document for a vehicle for a specific renewal date.
    """
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.vehicle = vehicle
            doc.renewal_date = renewal_date
            doc.save()
            return redirect('document-list')
    else:
        form = DocumentForm(initial={'vehicle': vehicle, 'renewal_date': renewal_date})
    return render(request, "document_add.html", {"form": form, "vehicle": vehicle, "renewal_date": renewal_date})


# ==== Approve Documents ====
from django.contrib.admin.views.decorators import staff_member_required
from .models import DocumentEntry

@staff_member_required
def approve_documents(request):
    q_member = request.GET.get('member') or ''
    page = request.GET.get('page', 1)

    # Only show pending entries uploaded by users (exclude manager-created entries)
    qs = DocumentEntry.objects.filter(status='pending', uploaded_by__isnull=False) \
        .select_related('document__vehicle__member', 'uploaded_by') \
        .order_by('-id')

    if q_member:
        qs = qs.filter(
            Q(document__vehicle__member__id=q_member) |
            Q(document__vehicle__member__full_name__icontains=q_member)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page)

    context = {
        'documents': list(page_obj.object_list),
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('includes/approve_documents_rows.html', context, request=request)
        pagination_html = render_to_string('includes/pagination.html', context, request=request)
        return JsonResponse({'html': html, 'pagination_html': pagination_html})

    return render(request, 'approve_documents.html', context)

@staff_member_required
@require_POST
def approve_document(request, doc_id):
    from .notifications import create_notification
    
    entry = get_object_or_404(DocumentEntry, pk=doc_id)
    entry.status = "approved"
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.manager_notes = request.POST.get("manager_notes", "")
    entry.save()
    
    # Notify the uploader
    if entry.uploaded_by:
        vehicle_plate = entry.document.vehicle.plate_number if entry.document and entry.document.vehicle else "unknown vehicle"
        create_notification(
            recipient=entry.uploaded_by,
            title="✅ Document Approved",
            message=f"Your document for {vehicle_plate} has been approved.",
            category='document_approved',
            priority='normal',
            action_url='/user/documents/',
            action_text='View Documents',
            related_object_type='document_entry',
            related_object_id=entry.id,
            created_by=request.user
        )
    
    messages.success(request, "Document entry approved.")
    return redirect("approve_documents")

@staff_member_required
@require_POST
def reject_document(request, doc_id):
    from .notifications import create_notification
    
    entry = get_object_or_404(DocumentEntry, pk=doc_id)
    entry.status = "rejected"
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.manager_notes = request.POST.get("manager_notes", "")
    entry.save()
    
    # Notify the uploader
    if entry.uploaded_by:
        vehicle_plate = entry.document.vehicle.plate_number if entry.document and entry.document.vehicle else "unknown vehicle"
        reason = entry.manager_notes if entry.manager_notes else "Please check the document requirements."
        create_notification(
            recipient=entry.uploaded_by,
            title="⚠️ Document Requires Resubmission",
            message=f"Your document for {vehicle_plate} was not approved. Reason: {reason}",
            category='document_rejected',
            priority='high',
            action_url='/user/documents/upload/',
            action_text='Upload Again',
            related_object_type='document_entry',
            related_object_id=entry.id,
            created_by=request.user
        )
    
    messages.success(request, "Document entry rejected.")
    return redirect("approve_documents")

# ==== User: Upload Document ====
from django.contrib.auth.decorators import login_required

@login_required
def user_upload_document(request):
    """
    User view to upload a document (placeholder logic).
    """
    if request.method == "POST":
        form = DocumentEntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.document = document
            entry.uploaded_by = user
            entry.status = "pending"

            # apply client-side timestamp if provided (ISO 8601)
            uploaded_at_str = request.POST.get('uploaded_at')
            if uploaded_at_str:
                from django.utils.dateparse import parse_datetime
                dt = parse_datetime(uploaded_at_str)
                if dt:
                    # make aware if naive
                    from django.utils import timezone as dj_tz
                    if dj_tz.is_naive(dt):
                        dt = dj_tz.make_aware(dt, dj_tz.get_current_timezone())
                    entry.created_at = dt

            entry.save()
            
            # Notify all staff that a new document was uploaded
            from .notifications import notify_all_staff
            member_name = user.member_profile.full_name if hasattr(user, 'member_profile') and user.member_profile else user.full_name
            vehicle_plate = document.vehicle.plate_number if document and document.vehicle else "unknown vehicle"
            notify_all_staff(
                title="New Document Uploaded",
                message=f"{member_name} uploaded documents for {vehicle_plate}.",
                category='document_uploaded',
                priority='high',
                action_url='/documents/approve/',
                action_text='Review Document'
            )
            
            messages.success(request, "Document uploaded successfully and is pending manager approval.")
            return redirect("user_upload_document")
        else:
            messages.error(request, "Please fix the errors below.")

# ==== Broadcast View ====
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def broadcast(request):
    """
    View to broadcast announcements and notifications to users.
    Handles GET (show form and recent broadcasts) and POST (save new broadcast).
    """
    if 'broadcasts' not in request.session:
        request.session['broadcasts'] = []
    broadcasts = request.session['broadcasts']
    if request.method == "POST":
        title = request.POST.get('announcement_title')
        message = request.POST.get('announcement_message')
        ntype = request.POST.get('notification_type')
        broadcasts.append({'title': title, 'message': message, 'type': ntype})
        request.session['broadcasts'] = broadcasts
    return render(request, "broadcast.html", {"broadcasts": broadcasts})


# ==== Class-based Views: Member ====

from django.db.models import Q, Exists, OuterRef

from .models import Member, Vehicle, Document  # ensure Document imported above

@method_decorator(login_required, name='dispatch')
class MemberListView(ListView):
    """
    Displays a paginated list of members.
    Supports searching across Member fields, related Vehicle fields,
    related Documents (by TIN) and linked User account fields.
    """
    model = Member
    template_name = "memberlist.html"
    context_object_name = "object_list"
    paginate_by = 10

    def get_queryset(self):
        # ensure we pull the linked user fields efficiently
        qs = super().get_queryset().select_related('batch', 'user_account').prefetch_related('vehicles')
        q = (self.request.GET.get("q") or "").strip()
        if not q:
            return qs
        # Subquery: any Document whose vehicle is owned by the member and tin matches q
        doc_qs = Document.objects.filter(vehicle__member=OuterRef('pk'), tin__icontains=q)

        
        queryset = qs.annotate(has_doc=Exists(doc_qs)).filter(
            Q(full_name__icontains=q) |
            Q(batch__number__icontains=q) |
            Q(batch_monitoring_number__icontains=q) |
            Q(vehicles__plate_number__icontains=q) |
            Q(vehicles__engine_number__icontains=q) |
            Q(vehicles__chassis_number__icontains=q) |
            Q(user_account__username__icontains=q) |
            Q(user_account__email__icontains=q) |
            Q(user_account__phone_number__icontains=q) |
            Q(has_doc=True)
        ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        """Add start_index for global row numbering across pages."""
        context = super().get_context_data(**kwargs)
        page_obj = context.get('page_obj')
        if page_obj:
            try:
                start = (page_obj.number - 1) * (self.paginate_by or 0)
            except Exception:
                start = 0
        else:
            start = 0
        context['start_index'] = start
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string("includes/member_table_rows.html", context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)

@method_decorator(login_required, name='dispatch')
class MemberDeleteView(DeleteView):
    """
    Handles deletion of a Member.
    - Shows confirmation page.
    - Redirects to member list after deletion.
    """
    model = Member
    template_name = "member_confirm_delete.html"
    success_url = reverse_lazy("member_list")

# ==== Class-based Views: Vehicle ====

@method_decorator(login_required, name='dispatch')
class VehicleListView(ListView):
    """
    Displays a paginated list of vehicles.
    - Supports search via 'q' GET parameter (searches plate, engine, etc.).
    - If AJAX request, returns only the table rows HTML for dynamic updates.
    """
    model = Vehicle
    template_name = "vehiclelist.html"
    context_object_name = "object_list"
    paginate_by = 10

    def get_queryset(self):
        # Filter queryset based on search query
        queryset = super().get_queryset().select_related('member')
        q = self.request.GET.get("q", "")
        if q:
            queryset = queryset.filter(
                Q(plate_number__icontains=q) |
                Q(engine_number__icontains=q) |
                Q(chassis_number__icontains=q) |
                Q(make_brand__icontains=q) |
                Q(body_type__icontains=q) |
                Q(year_model__icontains=q) |
                Q(series__icontains=q) |
                Q(color__icontains=q) |
                Q(member__full_name__icontains=q)
            )
        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string("includes/vehicle_table_rows.html", context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)

@method_decorator(login_required, name='dispatch')
class VehicleCreateView(CreateView):
    """
    Handles creation of a new Vehicle.
    - Uses VehicleForm for input.
    - Validates that a member can only have a maximum of 2 vehicles.
    - Redirects to vehicle list after creation.
    """
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicle_add.html"
    success_url = reverse_lazy("vehicle_list")
    
    def form_valid(self, form):
        # Check if member is selected and already has 2 vehicles
        member = form.cleaned_data.get('member')
        if member:
            vehicle_count = Vehicle.objects.filter(member=member).count()
            if vehicle_count >= 2:
                messages.error(
                    self.request,
                    f"Cannot assign vehicle to {member.full_name}. "
                    "This member already has 2 vehicles (cooperative maximum)."
                )
                return self.form_invalid(form)
        
        messages.success(self.request, "Vehicle added successfully!")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class VehicleUpdateView(UpdateView):
    """
    Handles editing of an existing Vehicle.
    - Uses VehicleForm for input.
    - Validates that a member can only have a maximum of 2 vehicles.
    - Redirects to vehicle list after update.
    """
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicle_add.html"
    success_url = reverse_lazy("vehicle_list")
    
    def form_valid(self, form):
        # Check if member is being changed and new member already has 2 vehicles
        member = form.cleaned_data.get('member')
        if member:
            # Exclude the current vehicle being edited from the count
            vehicle_count = Vehicle.objects.filter(member=member).exclude(pk=self.object.pk).count()
            if vehicle_count >= 2:
                messages.error(
                    self.request,
                    f"Cannot assign vehicle to {member.full_name}. "
                    "This member already has 2 vehicles (cooperative maximum)."
                )
                return self.form_invalid(form)
        
        messages.success(self.request, "Vehicle updated successfully!")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class VehicleDeleteView(DeleteView):
    """
    Handles deletion of a Vehicle.
    - Shows confirmation page.
    - Redirects to vehicle list after deletion.
    """
    model = Vehicle
    template_name = "vehicle_confirm_delete.html"
    success_url = reverse_lazy("vehicle_list")


# ==== Class-based Views: Document ====

from django.db.models import Max, Q
from .models import DocumentEntry

@method_decorator(login_required, name='dispatch')
class DocumentListView(ListView):
    model = Document
    template_name = "documentlist.html"
    context_object_name = "object_list"
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().select_related('vehicle', 'vehicle__member')
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(tin__icontains=q) |
                Q(vehicle__plate_number__icontains=q) |
                Q(vehicle__member__full_name__icontains=q)
            ).distinct()
        # Annotate with latest approved/manager renewal date
        qs = qs.annotate(
            latest_approved_renewal=Max(
                'entries__renewal_date',
                filter=Q(entries__status="approved") | Q(entries__uploaded_by__isnull=True)
            )
        )
        return qs

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string("includes/document_table_rows.html", context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)

@method_decorator(login_required, name='dispatch')
class DocumentCreateView(CreateView):
    """
    Handles creation of a new Document.
    - Uses DocumentForm for input.
    - Redirects to document list after creation.
    """
    model = Document
    form_class = DocumentForm
    template_name = "document_add.html"
    success_url = reverse_lazy("document-list")

# ==== AJAX Views ====

def get_vehicle_data(request):
    """
    AJAX endpoint to fetch vehicle details by vehicle_id.
    - Returns vehicle fields as JSON.
    - Used for autofilling vehicle form fields when assigning an existing vehicle.
    """
    vehicle_id = request.GET.get('vehicle_id')
    member_id = request.GET.get('member_id')
    data = {}
    
    # If member_id is provided, return all vehicles for that member
    if member_id:
        try:
            vehicles = Vehicle.objects.filter(member_id=member_id).values('id', 'plate_number')
            data = {'vehicles': list(vehicles)}
        except Exception:
            data = {'vehicles': []}
    # If vehicle_id is provided, return vehicle details
    elif vehicle_id:
        try:
            vehicle = Vehicle.objects.get(pk=vehicle_id)
            data = {
                'plate_number': vehicle.plate_number,
                'engine_number': vehicle.engine_number,
                'chassis_number': vehicle.chassis_number,
                'make_brand': vehicle.make_brand,
                'body_type': vehicle.body_type,
                'year_model': vehicle.year_model,
                'series': vehicle.series,
                'color': vehicle.color,
            }
        except Vehicle.DoesNotExist:
            pass
    return JsonResponse(data)
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages

@method_decorator(login_required, name='dispatch')
class DocumentUpdateView(UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "document_edit.html"
    success_url = reverse_lazy("document_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc = self.get_object()
        current_vehicle = getattr(doc, 'vehicle', None)
        if current_vehicle:
            member_name = getattr(current_vehicle.member, 'full_name', None)
            if member_name:
                label = f'{member_name} ("{current_vehicle.plate_number}")'
            else:
                label = current_vehicle.plate_number
            # expose plate (not id) for the template/select2 initial option
            context['current_vehicle_plate'] = current_vehicle.plate_number
            context['current_vehicle_label'] = label
        else:
            context['current_vehicle_plate'] = None
            context['current_vehicle_label'] = None
        return context

    def form_valid(self, form):
        # Select2 now posts a plate_number string as the "vehicle" field
        vehicle_plate = self.request.POST.get('vehicle')
        vehicle_obj = None
        if vehicle_plate:
            try:
                vehicle_obj = Vehicle.objects.get(plate_number=vehicle_plate)
            except Vehicle.DoesNotExist:
                form.add_error('vehicle', 'Selected vehicle does not exist.')
                return self.form_invalid(form)

            # Prevent selecting a vehicle that is already tied to another document
            exists = Document.objects.filter(vehicle=vehicle_obj).exclude(pk=self.object.pk).exists()
            if exists:
                form.add_error('vehicle', 'Selected vehicle is already tied to another document.')
                return self.form_invalid(form)

        form.instance.vehicle = vehicle_obj
        return super().form_valid(form)


# ==== Custom Login View ====
def custom_login(request):

    if request.user.is_authenticated:
        if request.user.is_staff or (hasattr(request.user, 'role') and request.user.role == 'manager'):
            return redirect("home")
        elif hasattr(request.user, 'role') and request.user.role == 'client':
            return redirect("user_home")
        else:
            # User doesn't have proper role, log them out
            logout(request)
            request.session.flush()
    
    # Clear session and logout on GET for unauthenticated users
    if request.method == "GET":
        return render(request, "login.html")
    
    if request.method == "POST":
        username_input = (request.POST.get("username") or "").strip()
        password = request.POST.get("password")
        # first try normal authenticate (treat input as username)
        user = authenticate(request, username=username_input, password=password)
        # fallback: if not found, try to treat input as email and resolve to username
        if user is None and username_input:
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            try:
                user_obj = UserModel.objects.get(email__iexact=username_input)
            except UserModel.DoesNotExist:
                user_obj = None
            if user_obj:
                user = authenticate(request, username=user_obj.get_username(), password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account is not yet approved by the admin.")
                return render(request, "login.html")
            auth_login(request, user)
            # Only staff (admin/manager) can access admin side, not user portal
            if user.is_staff or (hasattr(user, 'role') and user.role == 'manager'):
                return redirect("home")
            elif hasattr(user, 'role') and user.role == 'client':
                return redirect("user_home")
            else:
                messages.error(request, "You do not have access to the user portal.")
                return render(request, "login.html")
        else:
            messages.error(request, "Invalid username/email or password.")
    return render(request, "login.html")



# Document list, detail, renew, and delete views should be implemented as described above.

from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView, CreateView
from django import forms
from .models import Document,DocumentEntry

class DocumentEntryForm(forms.ModelForm):
    class Meta:
        model = DocumentEntry
        fields = ['renewal_date', 'official_receipt', 'certificate_of_registration']
        widgets = {
            'renewal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'official_receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificate_of_registration': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

@login_required
def document_add(request):
    if request.method == "POST":
        doc_form = DocumentForm(request.POST)
        entry_form = DocumentEntryForm(request.POST, request.FILES)
        vehicle_id = request.POST.get('vehicle')
        vehicle_obj = None
        if vehicle_id:
            try:
                vehicle_obj = Vehicle.objects.get(id=vehicle_id)
            except Vehicle.DoesNotExist:
                doc_form.add_error('vehicle', 'Selected vehicle does not exist.')
        if doc_form.is_valid() and entry_form.is_valid() and vehicle_obj:
            document = doc_form.save(commit=False)
            document.vehicle = vehicle_obj
            document.save()
            entry = entry_form.save(commit=False)
            entry.document = document
            entry.save()
            return redirect("document_list")
        return render(request, "document_add.html", {
            "form": doc_form,
            "entry_form": entry_form,
            "selected_vehicle": vehicle_id,
        })
    else:
        doc_form = DocumentForm()
        entry_form = DocumentEntryForm()
        return render(request, "document_add.html", {"form": doc_form, "entry_form": entry_form})
class DocumentDetailView(DetailView):
    model = Document
    template_name = "document_detail.html"
    context_object_name = "document"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_object()
        # Only show manager-created or approved user entries
        context['approved_entries'] = document.entries.filter(
            models.Q(uploaded_by__isnull=True) | models.Q(status="approved")
        ).order_by('renewal_date')
        return context

class DocumentEntryDetailView(DetailView):
    model = DocumentEntry
    template_name = "document_entry_detail.html"
    context_object_name = "entry"

class DocumentUpdateView(UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "document_add.html"  # Or create a separate document_edit.html
    success_url = reverse_lazy("document_list")

class DocumentEntryCreateView(CreateView):
    model = DocumentEntry
    form_class = DocumentEntryForm
    template_name = "document_entry_add.html"

    def get_initial(self):
        initial = super().get_initial()
        document = self.get_document()
        # Get the latest renewal date and add 1 year
        latest_entry = document.entries.order_by('-renewal_date').first()
        if latest_entry and latest_entry.renewal_date:
            next_renewal = latest_entry.renewal_date.replace(year=latest_entry.renewal_date.year + 1)
            initial['renewal_date'] = next_renewal
        else:
            initial['renewal_date'] = None  # Or set to today if you prefer
        initial['document'] = document.pk
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.get_document()
        return context

    def get_document(self):
        from .models import Document
        return Document.objects.get(pk=self.kwargs["pk"])

    def form_valid(self, form):
        form.instance.document = self.get_document()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("document_detail", kwargs={"pk": self.object.document.pk})

class DocumentDeleteView(DeleteView):
    model = Document
    template_name = "document_confirm_delete.html"
    success_url = reverse_lazy("document_list")
from .models import User

def accounts_list(request):
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "all").strip().lower()  # 'all' | 'activated' | 'pending'
    users_qs = User.objects.filter(role__iexact='client')

    # status filter
    if status == 'activated':
        users_qs = users_qs.filter(is_active=True)
    elif status == 'pending':
        users_qs = users_qs.filter(is_active=False)
    # Always order activated users first, then by username
    users_qs = users_qs.order_by('-is_active', 'username')

    if q:
        users_qs = users_qs.filter(
            Q(username__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone_number__icontains=q)
        )

    paginator = Paginator(users_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'users': list(page_obj.object_list),
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'q': q,
        'status': status,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('includes/account_table_rows.html', context, request=request)
        pagination_html = render_to_string('includes/pagination.html', context, request=request)
        return JsonResponse({'html': html, 'pagination_html': pagination_html})

    return render(request, 'accounts.html', context)

@require_POST
def deactivate_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = False
    user.save()
    return redirect('accounts_list')

@login_required
def edit_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    members = Member.objects.all()
    if request.method == "POST":
        user.full_name = request.POST.get("full_name", user.full_name)
        user.email = request.POST.get("email", user.email)
        user.phone_number = request.POST.get("phone_number", user.phone_number)
        member_id = request.POST.get("member_id")

        # Safely get the current member_profile (may not exist)
        current_member = getattr(user, "member_profile", None)

        # Untie previous member if needed
        if current_member and (not member_id or str(current_member.id) != member_id):
            current_member.user_account = None
            current_member.save()
            user.member_profile = None

        # Tie new member if provided
        if member_id:
            member = get_object_or_404(Member, pk=member_id)
            # Untie this member from any previous user
            if member.user_account and member.user_account != user:
                prev_user = member.user_account
                prev_user.member_profile = None
                prev_user.save()
            user.member_profile = member
            member.user_account = user
            member.save()
        else:
            user.member_profile = None

        user.save()
        messages.success(request, "Account updated successfully.")
        return redirect('accounts_list')
    return render(request, "account_edit.html", {"edited_user": user, "members": members})

@staff_member_required
@require_POST
def activate_account(request, user_id):
    from .notifications import create_notification
    
    user = get_object_or_404(User, pk=user_id)

    # If the account is being activated for the first time, set dormant=1
    if user.dormant == 0:
        user.dormant = 1

    user.is_active = True
    user.save()
    
    # Create welcome notification for the user
    create_notification(
        recipient=user,
        title="Welcome! Your Account is Active",
        message="Your POTMPC account has been activated. You can now access all member features.",
        category='account_activated',
        priority='high',
        action_url='/user_home/',
        action_text='Explore Portal',
        created_by=request.user
    )
    
    return redirect('accounts_list')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage

User = get_user_model()

@login_required
def my_profile(request):
    """
    Edit logged-in user's profile (separate edit template).
    Editable fields: full_name, email, phone_number, profile_image.
    """
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('user_profile')  # view-only page after edit
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'user_profile_edit.html', {'form': form, 'user_obj': user})

@login_required
def user_vehicles(request):
    if not getattr(request.user, 'member_profile', None):
        messages.info(request, "No member profile connected to your account.")
    return render(request, "user_vehicles.html")

@login_required
def user_documents(request):
    """
    User-facing documents view.
    Only shows documents when:
      - user is linked to a Member (user.member_profile)
      - that Member has a Vehicle that has a Document assigned
    Otherwise show an informational message and no documents.
    """
    user = request.user
    member = getattr(user, "member_profile", None)

    if not member:
        messages.info(request, "Your account is not assigned to a member. Ask a manager to link you to a member with vehicles/documents.")
        return render(request, "user_documents.html", {"documents": [], "member": None, "allowed": False})

    vehicles = member.vehicles.select_related("document").all()
    documents = []
    for v in vehicles:
        doc = getattr(v, "document", None)
        if doc:
            entries = doc.entries.order_by("-renewal_date")
            documents.append({"vehicle": v, "document": doc, "entries": entries})

    if not documents:
        messages.info(request, "No documents available for your assigned vehicles. A manager must assign a vehicle with a document to your member account.")
        return render(request, "user_documents.html", {"documents": [], "member": member, "allowed": False})

    return render(request, "user_documents.html", {"documents": documents, "member": member, "allowed": True})

@login_required
def user_document_detail(request, document_id):
    """
    User-facing detailed document view.
    Shows complete document information and renewal history for a single vehicle.
    Only accessible if the user is linked to the member that owns the vehicle.
    """
    user = request.user
    member = getattr(user, "member_profile", None)
    
    if not member:
        messages.error(request, "Your account is not linked to a member. Contact the manager.")
        return redirect('user_documents')
    
    # Get the document and verify ownership
    document = get_object_or_404(Document, id=document_id)
    vehicle = document.vehicle
    
    # Verify that this vehicle belongs to the user's member profile
    if vehicle.member != member:
        messages.error(request, "You don't have permission to view this document.")
        return redirect('user_documents')
    
    # Get all document entries for this document, ordered by renewal date (newest first)
    entries = document.entries.select_related('uploaded_by').order_by('-renewal_date')
    
    context = {
        'document': document,
        'vehicle': vehicle,
        'member': member,
        'entries': entries,
    }
    
    return render(request, 'user_document_detail.html', context)

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Member, Document, DocumentEntry, User
from .forms import AdminProfileForm
from datetime import timedelta, date

def _add_years_safe(dt, years=1):
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        # fallback for leap day -> move to Feb 28
        return dt.replace(month=2, day=28, year=dt.year + years)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_profile_edit(request):
    user = request.user
    if request.method == 'POST':
        form = AdminProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('admin_profile_edit')
    else:
        form = AdminProfileForm(instance=user)
    return render(request, 'admin_profile_edit.html', {'form': form})

@staff_member_required
def member_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    user_account = getattr(member, 'user_account', None)
    vehicles = list(member.vehicles.all()) if hasattr(member, 'vehicles') else []
    # Only include documents with at least one approved/manager entry
    documents = []
    for doc in Document.objects.filter(vehicle__in=vehicles):
        # Only approved or manager-created entries
        entries = list(doc.entries.filter(
            models.Q(status="approved") | models.Q(uploaded_by__isnull=True)
        ).order_by('renewal_date'))
        if entries:
            doc.entries_list = entries
            documents.append(doc)
    return render(request, 'member_detail.html', {
        'member': member,
        'user_account': user_account,
        'vehicles': vehicles,
        'documents': documents,
    })


from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import Member
from django.db.models import Count

@require_GET
@login_required
def member_search_api(request):
    """
    Search API for Member objects used by Select2 AJAX widgets.
    Excludes members who already have 2 or more vehicles (cooperative rule).
    When editing a vehicle, pass 'current_member_id' to include that member even if they have 2 vehicles.
    Returns JSON in Select2 { results: [{id, text}, ...] } format.
    """
    q = request.GET.get('q', '').strip()
    current_member_id = request.GET.get('current_member_id', '').strip()
    
    if not q:
        members = []
    else:
        # Annotate with vehicle count
        members_query = Member.objects.annotate(
            vehicle_count=Count('vehicles')
        ).filter(full_name__icontains=q)
        
        # If editing and current member has 2 vehicles, include them
        if current_member_id:
            try:
                current_id = int(current_member_id)
                members = members_query.filter(
                    Q(vehicle_count__lt=2) | Q(id=current_id)
                )[:10]
            except (ValueError, TypeError):
                members = members_query.filter(vehicle_count__lt=2)[:10]
        else:
            # When adding new vehicle, exclude members with 2+ vehicles
            members = members_query.filter(vehicle_count__lt=2)[:10]
    
    results = [{'id': m.id, 'text': m.full_name} for m in members]
    return JsonResponse({'results': results})


@require_GET
@login_required
def user_search_api(request):
    """
    Search API for User objects used by Select2 AJAX widgets.
    Returns JSON in Select2 { results: [{id, text}, ...] } format.
    Only returns activated users without existing member profiles (excluding superusers).
    """
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    q = request.GET.get('q', '').strip()
    if not q:
        users = []
    else:
        # Filter: activated users, not superusers, and without existing member_profile
        users = UserModel.objects.filter(
            Q(username__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q)
        ).filter(
            is_active=True,
            is_superuser=False,
            member_profile__isnull=True
        )[:10]
    results = []
    for u in users:
        label = getattr(u, 'full_name', None) or u.username
        results.append({'id': u.id, 'text': label})
    return JsonResponse({'results': results})


# views.py
@require_GET
@login_required
def vehicle_member_select2_api(request):
    q = request.GET.get('q', '').strip()
    exclude_document_id = request.GET.get('exclude_document_id')
    results = []
    vehicles = Vehicle.objects.select_related('member')

    # Exclude vehicles already tied to any Document, but allow the vehicle
    # currently tied to the document being edited (exclude_document_id).
    if exclude_document_id:
        try:
            exclude_doc_pk = int(exclude_document_id)
        except (TypeError, ValueError):
            exclude_doc_pk = None
        if exclude_doc_pk:
            vehicles = vehicles.filter(models.Q(document__isnull=True) | models.Q(document__pk=exclude_doc_pk))
        else:
            vehicles = vehicles.filter(document__isnull=True)
    else:
        vehicles = vehicles.filter(document__isnull=True)

    if q:
        vehicles = vehicles.filter(
            models.Q(plate_number__icontains=q) |
            models.Q(member__full_name__icontains=q)
        )

    for v in vehicles[:50]:  # limit results
        if v.member:
            label = f'{v.member.full_name} ("{v.plate_number}")'
        else:
            label = v.plate_number
        results.append({'id': v.id, 'text': label})
    return JsonResponse({'results': results})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Member, Vehicle

from django.core.paginator import Paginator

@login_required
def home(request):
    User = get_user_model()
    today = timezone.localtime(timezone.now()).date()

    total_members = Member.objects.count()
    accounts_count = User.objects.filter(is_active=True).count()
    vehicles_count = Vehicle.objects.count()
    batch_count = Batch.objects.count()
    document_count = Document.objects.count()

    urgent_members = []
    warning_members = []
    
    # Track total renewals for whiteboard
    total_renewals_count = 0

    batch_cards = []
    for batch in Batch.objects.all():
        members_qs = batch.members.select_related('user_account').prefetch_related('vehicles__document__entries').all().order_by('full_name')
        total_count = members_qs.count()

        urgent_count = 0
        upcoming_count = 0
        members_preview = []   # for client-side preview (member -> vehicles list)

        for idx, member in enumerate(members_qs):
            # collect per-vehicle renewal info for this member
            vehicle_infos = []
            member_has_urgent = False
            member_has_upcoming = False

            for vehicle in member.vehicles.all():
                plate = getattr(vehicle, 'plate_number', 'N/A')
                latest_entry = DocumentEntry.objects.filter(
                    document__vehicle=vehicle
                ).filter(
                    Q(status="approved") | Q(uploaded_by__isnull=True)
                ).order_by('-renewal_date').first()

                expiry_date = None
                if latest_entry and latest_entry.renewal_date:
                    candidate = latest_entry.renewal_date
                    # convert to date if datetime
                    if hasattr(candidate, "date"):
                        candidate = candidate.date()
                    # if stored date is in the past, advance year-by-year to next expected expiry
                    attempts = 0
                    while candidate < today and attempts < 5:
                        candidate = _add_years_safe(candidate, 1)
                        attempts += 1
                    expiry_date = candidate

                if expiry_date:
                    days_left = (expiry_date - today).days
                    status = 'normal'
                    if 0 <= days_left <= 29:
                        status = 'urgent'
                        member_has_urgent = True
                        total_renewals_count += 1  # Count for whiteboard
                    elif 30 <= days_left <= 60:
                        status = 'upcoming'
                        # only mark upcoming if not already urgent
                        if not member_has_urgent:
                            member_has_upcoming = True
                        total_renewals_count += 1  # Count for whiteboard
                    vehicle_infos.append({
                        'plate': plate,
                        'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                        'days_left': days_left,
                        'status': status
                    })
                else:
                    # include vehicle even if no entry so UI shows plate with N/A
                    vehicle_infos.append({
                        'plate': plate,
                        'expiry_date': None,
                        'days_left': None,
                        'status': 'none'
                    })

            # decide member bucket (urgent > upcoming > normal)
            if member_has_urgent:
                urgent_count += 1
                urgent_members.append({'name': member.full_name, 'vehicles': [v for v in vehicle_infos if v['status'] == 'urgent' or v['status']=='upcoming' or v['status']=='normal']})
            elif member_has_upcoming:
                upcoming_count += 1
                warning_members.append({'name': member.full_name, 'vehicles': [v for v in vehicle_infos if v['status'] == 'upcoming' or v['status']=='normal']})
            # members_preview contains vehicles info for client-side chart fallback
            if idx < 50:  # keep preview reasonably sized
                members_preview.append({
                    'member_name': member.full_name,
                    'vehicles': vehicle_infos
                })

        batch_cards.append({
            'id': batch.id,
            'number': batch.number,
            'total': total_count,
            'urgent': urgent_count,
            'warning': upcoming_count,
            'members_preview': members_preview,
        })

    context = {
        'total_members': total_members,
        'accounts_count': accounts_count,
        'vehicles_count': vehicles_count,
        'batch_count': batch_count,
        'document_count': document_count,
        'batch_cards': batch_cards,
        'urgent_members': urgent_members,
        'warning_members': warning_members,
    }
    
    # Add whiteboard data with renewal counts
    from django.urls import reverse
    try:
        UserModel = get_user_model()
        accounts_pending = UserModel.objects.filter(is_active=False, dormant=0).count()
        documents_pending = DocumentEntry.objects.filter(status__iexact="pending", uploaded_by__isnull=False).count()
        
        pending_counts = {
            'accounts': accounts_pending,
            'documents': documents_pending,
            'renewals': total_renewals_count
        }
        whiteboard_links = {
            'accounts': reverse('accounts_list'),
            'documents': reverse('approve_documents'),
            'renewals': reverse('renewals_hub')
        }
        context['pending_counts_json'] = json.dumps(pending_counts)
        context['whiteboard_links_json'] = json.dumps(whiteboard_links)
    except Exception as e:
        context['pending_counts_json'] = '{}'
        context['whiteboard_links_json'] = '{}'
    
    try:
        context['batch_cards_json'] = json.dumps(batch_cards, default=str)
    except Exception:
        context['batch_cards_json'] = '[]'
    return render(request, "home.html", context)

@staff_member_required
def broadcast(request):
    """
    Admin/Manager page to create announcements targeted to client users.
    If recipients left empty in the form, the announcement will be considered
    broadcast to all clients (handled when clients fetch announcements).
    """
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            form.save_m2m()
            
            # Create notifications for recipients
            from .notifications import create_notification
            recipients = ann.recipients.all()
            if not recipients.exists():
                # Broadcast to all active clients
                recipients = User.objects.filter(role='client', is_active=True)
            
            for recipient in recipients:
                create_notification(
                    recipient=recipient,
                    title="📢 New Announcement",
                    message=ann.message[:200] + ('...' if len(ann.message) > 200 else ''),
                    category='announcement_posted',
                    priority='normal',
                    action_url='/user/announcements/',
                    action_text='Read More',
                    related_object_type='announcement',
                    related_object_id=ann.id,
                    created_by=request.user
                )
            
            messages.success(request, "Announcement created.")
            # Placeholder for dispatch (email/push). Implement send logic here if desired.
            return redirect('broadcast')
    else:
        form = AnnouncementForm()

    broadcasts = Announcement.objects.order_by('-created_at')[:50]
    return render(request, "broadcast.html", {"form": form, "broadcasts": broadcasts})


@login_required
def user_announcements(request):
    """
    Client-facing announcement list:
    - Show announcements that either target this user (recipients includes user)
      OR have no recipients (meaning broadcast to all clients).
    """
    user = request.user
    qs = Announcement.objects.filter(Q(recipients__isnull=True) | Q(recipients=user)).distinct().order_by('-created_at')
    return render(request, "user_announcements.html", {"announcements": qs})

@login_required
def user_upload_document(request):
    """
    Allow client users to add a DocumentEntry only if their account is tied:
    User -> Member -> Vehicle -> Document. Saves OR/CR and renewal_date under
    the existing Document. Redirects to user_documents on success.
    Supports multiple vehicles - user can select which vehicle to upload for.
    """
    user = request.user
    if getattr(user, "role", None) != "client":
        messages.error(request, "Only client users can upload document entries.")
        return redirect("home")

    member = getattr(user, "member_profile", None)
    if not member:
        messages.error(request, "No member profile assigned to your account.")
        return redirect("user_home")

    # Get all vehicles with documents for this member
    available_vehicles = []
    for v in member.vehicles.all():
        if getattr(v, "document", None):
            available_vehicles.append(v)
    
    if not available_vehicles:
        messages.error(request, "No document assigned to any of your vehicles. Contact your manager.")
        return redirect("user_home")
    
    # Get selected vehicle ID from GET parameter, default to first vehicle
    selected_vehicle_id = request.GET.get('vehicle_id')
    vehicle = None
    document = None
    
    if selected_vehicle_id:
        try:
            vehicle = next((v for v in available_vehicles if str(v.id) == str(selected_vehicle_id)), None)
        except (ValueError, TypeError):
            vehicle = None
    
    # If no valid selection, use first available vehicle
    if not vehicle:
        vehicle = available_vehicles[0]
    
    document = vehicle.document

    # List user's entries for this document
    user_entries = DocumentEntry.objects.filter(document=document, uploaded_by=user).order_by('-id')

    if request.method == "POST":
        form = DocumentEntryForm(request.POST, request.FILES)
        if form.is_valid():
            from .notifications import notify_all_staff
            
            entry = form.save(commit=False)
            entry.document = document
            entry.uploaded_by = user
            entry.status = "pending"
            entry.save()
            
            # Notify all staff about the new document upload
            member_name = member.full_name if member else user.username
            vehicle_plate = vehicle.plate_number if vehicle else "Unknown Vehicle"
            
            notify_all_staff(
                title="New Document Uploaded",
                message=f"{member_name} uploaded documents for {vehicle_plate}.",
                category='document_uploaded',
                priority='high',
                action_url='/documents/approve/',
                action_text='Review Document',
                related_object_type='document_entry',
                related_object_id=entry.id,
                created_by=user
            )
            
            messages.success(request, "Document uploaded successfully and is pending manager approval.")
            # Redirect with vehicle_id to maintain selection
            return redirect(f"{reverse('user_upload_document')}?vehicle_id={vehicle.id}")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        latest = document.entries.order_by("-renewal_date").first()
        initial = {}
        if latest and latest.renewal_date:
            try:
                initial_date = latest.renewal_date.replace(year=latest.renewal_date.year + 1)
            except Exception:
                initial_date = latest.renewal_date
            initial["renewal_date"] = initial_date
        form = DocumentEntryForm(initial=initial)

    return render(request, "user_upload_document.html", {
        "form": form,
        "vehicle": vehicle,
        "document": document,
        "entries": user_entries,
        "available_vehicles": available_vehicles,
        "selected_vehicle_id": vehicle.id,
    })


@login_required
def user_document_entry_count_api(request):
    """
    Returns the total number of DocumentEntry objects for the logged-in user's documents.
    JSON response: { "count": <int> }
    Only counts DocumentEntry objects connected to the user's member's vehicles' documents.
    """
    user = request.user
    member = getattr(user, "member_profile", None)
    count = 0
    if member:
        # Get all documents linked to the user's vehicles
        documents = Document.objects.filter(vehicle__member=member)
        # Count all DocumentEntry objects linked to those documents
        count = DocumentEntry.objects.filter(document__in=documents).count()
    return JsonResponse({"count": count})

# ==== AJAX Views: Pending Counts for Whiteboard ====

from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from .models import DocumentEntry

@staff_member_required
def pending_counts_api(request):
    """
    Returns JSON for whiteboard: counts and links.
    Only accessible to staff members.
    """
    UserModel = get_user_model()
    today = timezone.localtime(timezone.now()).date()
    
    # pending accounts: client role and not active
    accounts_pending = UserModel.objects.filter(is_active=False, dormant=0).count()

    # documents pending: entries uploaded by users with status "pending"
    documents_pending = DocumentEntry.objects.filter(status__iexact="pending", uploaded_by__isnull=False).count()

    # Calculate renewal counts (urgent + upcoming)
    renewals_count = 0
    members_query = Member.objects.select_related('user_account', 'batch').prefetch_related(
        'vehicles__document__entries'
    ).all()
    
    for member in members_query:
        for vehicle in member.vehicles.all():
            # Get latest approved document entry
            latest_entry = DocumentEntry.objects.filter(
                document__vehicle=vehicle
            ).filter(
                Q(status="approved") | Q(uploaded_by__isnull=True)
            ).order_by('-renewal_date').first()
            
            if latest_entry and latest_entry.renewal_date:
                candidate = latest_entry.renewal_date
                
                # Convert to date if datetime
                if hasattr(candidate, "date"):
                    candidate = candidate.date()
                
                # Normalize expiry date to future
                attempts = 0
                while candidate < today and attempts < 5:
                    candidate = _add_years_safe(candidate, 1)
                    attempts += 1
                
                days_left = (candidate - today).days
                
                # Count urgent (0-29 days) and upcoming (30-60 days)
                if 0 <= days_left <= 60:
                    renewals_count += 1

    # resolve links with reverse (safe fallback)
    try:
        accounts_link = reverse('accounts_list')
    except:
        accounts_link = '/accounts/'
    try:
        documents_link = reverse('approve_documents')
    except:
        documents_link = '/approve_documents/'
    try:
        renewals_link = reverse('renewals_hub')
    except:
        renewals_link = '/renewals/'

    counts = {
        'accounts': accounts_pending,
        'documents': documents_pending,
        'renewals': renewals_count
    }
    links = {
        'accounts': accounts_link,
        'documents': documents_link,
        'renewals': renewals_link
    }

    return JsonResponse({'counts': counts, 'links': links})

# ==== Batch Views: Member, Vehicle and Renewal Date ==== #

from django.template.loader import render_to_string
from django.http import JsonResponse

@login_required
@user_passes_test(lambda u: u.is_staff)
def batch_detail(request, pk):
    """
    Show members in a batch with their vehicles and expiry dates.
    Supports AJAX search/filter:
      - GET params: q (search by member name or plate), status ('urgent'|'upcoming'|'normal' or empty), page
    Returns full page or JSON { html_rows, html_pagination } for AJAX.
    """
    batch = get_object_or_404(Batch, pk=pk)
    q = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or '').strip().lower()
    page_number = request.GET.get('page', 1)

    today = timezone.localtime(timezone.now()).date()

    members_qs = batch.members.prefetch_related('vehicles__document__entries').order_by('full_name')

    members_list = []
    for member in members_qs:
        vehicle_infos = []
        member_has_urgent = False
        member_has_upcoming = False

        for vehicle in member.vehicles.all():
            plate = getattr(vehicle, 'plate_number', 'N/A')
            latest_entry = DocumentEntry.objects.filter(
                document__vehicle=vehicle
            ).filter(
                Q(status="approved") | Q(uploaded_by__isnull=True)
            ).order_by('-renewal_date').first()

            expiry_date = None
            days_left = None
            status = 'none'
            if latest_entry and latest_entry.renewal_date:
                candidate = latest_entry.renewal_date
                if hasattr(candidate, "date"):
                    candidate = candidate.date()
                attempts = 0
                while candidate < today and attempts < 5:
                    candidate = _add_years_safe(candidate, 1)
                    attempts += 1
                expiry_date = candidate
                days_left = (expiry_date - today).days
                if 0 <= days_left <= 15:
                    status = 'urgent'
                    member_has_urgent = True
                elif 30 <= days_left <= 60:
                    status = 'upcoming'
                    if not member_has_urgent:
                        member_has_upcoming = True
                else:
                    status = 'normal'

            vehicle_infos.append({
                'plate': plate,
                'expiry_date': expiry_date.strftime('%Y-%m-%d') if expiry_date else None,
                'days_left': days_left,
                'status': status,
            })

        # decide member-level bucket (urgent > upcoming > normal)
        if member_has_urgent:
            member_status = 'urgent'
        elif member_has_upcoming:
            member_status = 'upcoming'
        else:
            member_status = 'normal'

        members_list.append({
            'id': member.id,
            'name': member.full_name,
            'vehicles': vehicle_infos,
            'status': member_status,
        })

    # apply q filter (name or plate) and status filter
    def matches_filters(m):
        if status_filter and status_filter != m['status']:
            return False
        if not q:
            return True
        qlow = q.lower()
        if qlow in (m['name'] or '').lower():
            return True
        for v in m['vehicles']:
            if v['plate'] and qlow in v['plate'].lower():
                return True
        return False

    filtered = [m for m in members_list if matches_filters(m)]

    # sort so urgent first, upcoming next, normal last (preserve alphabetical within group)
    priority = {'urgent': 0, 'upcoming': 1, 'normal': 2, 'none': 3}
    filtered.sort(key=lambda x: (priority.get(x.get('status'), 3), (x.get('name') or '').lower()))

    # paginate
    paginator = Paginator(filtered, 10)
    page_obj = paginator.get_page(page_number)
    members_page = list(page_obj.object_list)

    # batches for dropdown
    batches = Batch.objects.order_by('number').values('id', 'number')

    context = {
        'batch': batch,
        'members': members_page,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_members': len(members_list),
        'q': q,
        'status_filter': status_filter,
        'batches': batches,
        'selected_batch_id': batch.id,
        'is_paginated': page_obj.has_other_pages(),
        'object_list': page_obj.object_list,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        rows_html = render_to_string('includes/batch_member_rows.html', context, request=request)
        pagination_html = render_to_string('includes/pagination.html', context, request=request)
        return JsonResponse({'html': rows_html, 'pagination': pagination_html})

    return render(request, 'batch_detail.html', context)

def qr_login_view(request, token):
    """
    Visit /qr-login/<token>/ to log in.
    Token is validated and, if valid, user is logged in and redirected.
    """
    try:
        qr = QRLoginToken.objects.get(token=token)
    except QRLoginToken.DoesNotExist:
        # token not found
        raise Http404("Invalid or expired QR code")

    if not qr.is_valid():
        raise Http404("Token invalid or expired")

    user = qr.user
    # Log user in
    auth_login(request, user)

    # If single-use, deactivate it now
    if qr.single_use:
        qr.is_active = False
        qr.save(update_fields=["is_active"])

    # redirect depending on staff / role logic used in your site
    if user.is_staff:
        return redirect("home")
    else:
        return redirect("user_home")

# View to render user's QR as PNG on demand (requires login)
@login_required
def my_qr_view(request):
    """
    Renders the logged-in user's active QR token as an image.
    If none exists (or expired), create a new one with a default TTL.
    """
    user = request.user
    # Try to get a currently valid token
    token_qs = user.qr_tokens.filter(is_active=True)
    valid_token = None
    for t in token_qs:
        if t.is_valid():
            valid_token = t
            break
    if not valid_token:
        # create one: TTL 24 hours, single-use by default
        valid_token = QRLoginToken.create_token_for_user(user, ttl_hours=24, single_use=True)

    login_url = request.build_absolute_uri(f"/qr-login/{valid_token.token}/")
    # create qr PNG
    img = qrcode.make(login_url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type="image/png")

def qr_image_login(request):
    """
    Accepts an uploaded image, decodes the QR code,
    and logs the user in if the token/URL is valid.
    """
    if request.method == "POST" and request.FILES.get("qr_image"):
        img_file: InMemoryUploadedFile = request.FILES["qr_image"]
        img = Image.open(img_file)
        decoded = decode(img)
        if not decoded:
            messages.error(request, "No QR code found in the image.")
            return redirect("login")
        # If there are multiple results, use the first
        qr_text = decoded[0].data.decode("utf-8").strip()

        # If the QR contains a full URL, redirect there.
        # If it only contains the token, build the URL.
        if qr_text.startswith("http"):
            return redirect(qr_text)
        else:
            return redirect(reverse("qr-login", args=[qr_text]))

    # GET requests or errors just go back to login page
    return redirect("login")

def qr_scan_page(request):
    return render(request, 'qr_login.html')
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import PaymentYear, PaymentType, PaymentEntry, Member
from .forms import PaymentYearForm, PaymentTypeForm, PaymentEntryForm

@login_required
def payment_year_list(request):
    filter_type = request.GET.get('filter', 'from_members')  # Default to "From Members"
    years = PaymentYear.objects.order_by('-year')

    context = {
        'years': years,
        'filter_type': filter_type,
    }
    return render(request, 'payments/year_list.html', context)

from django.db.models import Q

@login_required
def from_members_payment_view(request, year_id):
    year = get_object_or_404(PaymentYear, pk=year_id)
    q = (request.GET.get('q') or '').strip()
    member_id = request.GET.get('member_id', '').strip()
    page_number = request.GET.get('page', 1)

    # Fetch members with related data
    members = Member.objects.select_related('user_account', 'batch').prefetch_related('payment_entries').order_by('full_name')

    # Filter by specific member if selected from search
    if member_id:
        members = members.filter(id=member_id)
    # Otherwise filter members based on text search query
    elif q:
        members = members.filter(Q(full_name__icontains=q) | Q(batch__number__icontains=q)).distinct()

    # Annotate members with monthly totals for the selected year
    for member in members:
        # Calculate totals for each month, defaulting to None if no payments exist (will show as "-")
        member.monthly_totals = [
            member.payment_entries.filter(payment_type__year=year, month=month).aggregate(total=Sum('amount_paid'))['total']
            for month in range(1, 13)
        ]

    paginator = Paginator(members, 7)  # Paginate 7 members per page
    page_obj = paginator.get_page(page_number)

    context = {
        'year': year,
        'members': page_obj,
        'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        'paginator': paginator,
        'page_obj': page_obj,
        'q': q,
        'member_id': member_id,
    }
    return render(request, 'payments/from_members_payment.html', context)

@login_required
def other_payments_view(request, year_id):
    year = get_object_or_404(PaymentYear, pk=year_id)
    payments = PaymentEntry.objects.filter(payment_type__payment_type='other', payment_type__year=year)

    paginator = Paginator(payments, 10)  # Paginate 10 payments per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'year': year,
        'payments': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    return render(request, 'payments/other_payments.html', context)

@login_required
def payment_year_detail(request, year_id):
    year = get_object_or_404(PaymentYear, pk=year_id)
    
    # Separate payment types by category
    from_members_types = PaymentType.objects.filter(year=year, payment_type='from_members')
    other_types = PaymentType.objects.filter(year=year, payment_type='other')
    
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Process "From Members" payment types - aggregate all members
    from_members_data = []
    for payment_type in from_members_types:
        monthly_totals = []
        for month in range(1, 13):  # January to December
            # CHECK IF CAR WASH TYPE
            if payment_type.is_car_wash:
                # Count all car wash entries for this month (all members)
                count = PaymentEntry.objects.filter(
                    payment_type=payment_type,
                    month=month,
                    is_car_wash_record=True,
                    is_penalty=False
                ).count()
                monthly_totals.append(count if count > 0 else None)
            else:
                # Sum amounts for regular payments
                total = PaymentEntry.objects.filter(
                    payment_type=payment_type,
                    month=month
                ).aggregate(total=Sum('amount_paid'))['total']
                monthly_totals.append(total if total is not None else None)
        
        from_members_data.append({
            'payment_type': payment_type,
            'monthly_totals': monthly_totals,
            'is_car_wash': payment_type.is_car_wash,  # Flag for template
        })
    
    # Process "Other" payment types - aggregate all entries
    other_data = []
    for payment_type in other_types:
        monthly_totals = []
        for month in range(1, 13):  # January to December
            # Sum all payments for this payment type and month
            total = PaymentEntry.objects.filter(
                payment_type=payment_type,
                month=month
            ).aggregate(total=Sum('amount_paid'))['total']
            monthly_totals.append(total if total is not None else None)
        other_data.append({
            'payment_type': payment_type,
            'monthly_totals': monthly_totals,
        })

    return render(request, 'payments/year_detail.html', {
        'year': year,
        'from_members_data': from_members_data,
        'other_data': other_data,
        'months': months,
    })

@login_required
def add_payment_type(request, year_id):
    year = get_object_or_404(PaymentYear, pk=year_id)
    if request.method == 'POST':
        form = PaymentTypeForm(request.POST)
        if form.is_valid():
            payment_type = form.save(commit=False)
            payment_type.year = year
            payment_type.save()

            if payment_type.payment_type == 'from_members':
                members = Member.objects.all()
                for member in members:
                    for month in range(1, 13):  # January to December
                        PaymentEntry.objects.create(
                            payment_type=payment_type,
                            member=member,
                            month=month,
                            amount_paid=0.00,  # Default to 0
                        )

            return redirect('payment_year_detail', year_id=year.id)

    else:
        form = PaymentTypeForm()
    return render(request, 'payments/add_payment_type.html', {'form': form, 'year': year})


@login_required
def add_payment_entry(request, year_id, member_id=None):
    year = get_object_or_404(PaymentYear, pk=year_id)
    member = None
    if member_id:
        member = get_object_or_404(Member, pk=member_id)
    
    if request.method == 'POST':
        form = PaymentEntryForm(request.POST)
        # Filter payment types for the current year
        form.fields['payment_type'].queryset = PaymentType.objects.filter(year=year)
        
        # If member is pre-selected, force it in the form and disable the field
        if member:
            form.fields['member'].disabled = True
            form.fields['member'].widget.attrs['class'] = 'form-control'
        
        if form.is_valid():
            payment_entry = form.save(commit=False)
            # If member was pre-selected, ensure it's set (since disabled fields don't POST)
            if member:
                payment_entry.member = member
            if not payment_entry.member:  # Ensure the member is set
                messages.error(request, "Please select a member for the payment entry.")
                return render(request, 'payments/add_payment_entry.html', {'form': form, 'year': year, 'member': member})
            payment_entry.recorded_by = request.user
            payment_entry.save()
            messages.success(request, "Payment entry added successfully.")
            # Redirect to the specific member's payment table
            return redirect('member_payment_list', year_id=year.id, member_id=payment_entry.member.id)
        else:
            messages.error(request, "There was an error adding the payment entry.")
    else:
        # Pre-populate form with member if provided
        initial_data = {}
        if member:
            initial_data['member'] = member
        form = PaymentEntryForm(initial=initial_data)
        # Filter payment types for the current year
        form.fields['payment_type'].queryset = PaymentType.objects.filter(year=year)
        
        # If member is pre-selected, disable the field and style it as grayed out
        if member:
            form.fields['member'].disabled = True
            form.fields['member'].widget.attrs['class'] = 'form-control'
            form.fields['member'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'
    
    return render(request, 'payments/add_payment_entry.html', {'form': form, 'year': year, 'member': member})


@login_required
def add_other_payment_entry(request, year_id):
    """
    Add payment entry specifically for 'Other' payment types.
    Only shows payment types with payment_type='other'.
    """
    year = get_object_or_404(PaymentYear, pk=year_id)
    
    if request.method == 'POST':
        form = PaymentEntryForm(request.POST)
        
        if form.is_valid():
            payment_entry = form.save(commit=False)
            payment_entry.recorded_by = request.user
            payment_entry.save()
            messages.success(request, "Other payment entry added successfully.")
            return redirect('other_payments_view', year_id=year.id)
        else:
            messages.error(request, "There was an error adding the payment entry.")
    else:
        form = PaymentEntryForm()
    
    # Filter to only show "Other" payment types for the current year
    other_payment_types = PaymentType.objects.filter(year=year, payment_type='other')
    
    return render(request, 'payments/add_other_payment_entry.html', {
        'form': form,
        'year': year,
        'other_payment_types': other_payment_types
    })


from .forms import PaymentYearForm

@login_required
def add_payment_year(request):
    if request.method == 'POST':
        form = PaymentYearForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payment_year_list')
    else:
        form = PaymentYearForm()
    return render(request, 'payments/add_payment_year.html', {'form': form})

from .models import PaymentYear, PaymentType, PaymentEntry, Member
from .forms import PaymentEntryForm

@login_required
def member_payment_list(request, year_id, member_id):
    year = get_object_or_404(PaymentYear, pk=year_id)
    member = get_object_or_404(Member, pk=member_id)
    
    # Separate payment types by category
    from_members_types = PaymentType.objects.filter(year=year, payment_type='from_members')
    other_types = PaymentType.objects.filter(year=year, payment_type='other')

    # Prepare data for the template
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Process "From Members" payment types
    from_members_data = []
    for payment_type in from_members_types:
        monthly_totals = []
        for month in range(1, 13):  # January to December
            # CHECK IF CAR WASH TYPE
            if payment_type.is_car_wash:
                # For car wash: COUNT entries instead of sum
                count = member.payment_entries.filter(
                    payment_type=payment_type,
                    month=month,
                    is_car_wash_record=True,
                    is_penalty=False
                ).count()
                monthly_totals.append(count if count > 0 else None)
            else:
                # For regular payments: SUM amounts
                entries = member.payment_entries.filter(
                    payment_type=payment_type,
                    month=month
                )
                total = entries.aggregate(total=Sum('amount_paid'))['total']
                monthly_totals.append(total if total is not None else None)
        
        from_members_data.append({
            'payment_type': payment_type,
            'monthly_totals': monthly_totals,
            'is_car_wash': payment_type.is_car_wash,  # Flag for template
        })
    
    # Process "Other" payment types
    other_data = []
    for payment_type in other_types:
        monthly_totals = []
        for month in range(1, 13):  # January to December
            entries = member.payment_entries.filter(
                payment_type=payment_type,
                month=month
            )
            total = entries.aggregate(total=Sum('amount_paid'))['total']
            monthly_totals.append(total if total is not None else None)
        other_data.append({
            'payment_type': payment_type,
            'monthly_totals': monthly_totals,
        })

    # Initialize the PaymentEntryForm
    form = PaymentEntryForm(initial={'member': member})

    context = {
        'year': year,
        'member': member,
        'from_members_data': from_members_data,
        'other_data': other_data,
        'months': months,
        'form': form,
    }
    return render(request, 'payments/member_payment_list.html', context)


# ==== Renewal Details View ====
from datetime import datetime as dt

@staff_member_required
def renewal_details(request, date):
    """
    Shows all members with document renewals on a specific date.
    Groups members by urgency status (urgent/upcoming).
    Provides action buttons to send reminders or mark as renewed.
    """
    try:
        # Parse the date from URL (format: YYYY-MM-DD)
        target_date = dt.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect('home')
    
    today = timezone.localtime(timezone.now()).date()
    
    # Initialize lists for different urgency levels
    urgent_renewals = []
    upcoming_renewals = []
    normal_renewals = []
    
    # Get all members with their vehicles and documents
    members = Member.objects.select_related('user_account', 'batch').prefetch_related(
        'vehicles__document__entries'
    ).all().order_by('full_name')
    
    for member in members:
        for vehicle in member.vehicles.all():
            plate = getattr(vehicle, 'plate_number', 'N/A')
            
            # Get latest approved document entry
            latest_entry = DocumentEntry.objects.filter(
                document__vehicle=vehicle
            ).filter(
                Q(status="approved") | Q(uploaded_by__isnull=True)
            ).order_by('-renewal_date').first()
            
            if latest_entry and latest_entry.renewal_date:
                candidate = latest_entry.renewal_date
                
                # Convert to date if datetime
                if hasattr(candidate, "date"):
                    candidate = candidate.date()
                
                # Normalize expiry date to future
                attempts = 0
                while candidate < today and attempts < 5:
                    candidate = _add_years_safe(candidate, 1)
                    attempts += 1
                
                # Check if this renewal matches our target date
                if candidate == target_date:
                    days_left = (candidate - today).days
                    
                    # Determine status
                    status = 'normal'
                    status_class = 'secondary'
                    if 0 <= days_left <= 29:
                        status = 'urgent'
                        status_class = 'danger'
                    elif 30 <= days_left <= 60:
                        status = 'upcoming'
                        status_class = 'warning'
                    
                    renewal_info = {
                        'member': member,
                        'vehicle': vehicle,
                        'plate': plate,
                        'expiry_date': candidate,
                        'days_left': days_left,
                        'status': status,
                        'status_class': status_class,
                        'document_entry': latest_entry,
                    }
                    
                    # Categorize by status
                    if status == 'urgent':
                        urgent_renewals.append(renewal_info)
                    elif status == 'upcoming':
                        upcoming_renewals.append(renewal_info)
                    else:
                        normal_renewals.append(renewal_info)
    
    # Count totals
    total_renewals = len(urgent_renewals) + len(upcoming_renewals) + len(normal_renewals)
    
    context = {
        'target_date': target_date,
        'urgent_renewals': urgent_renewals,
        'upcoming_renewals': upcoming_renewals,
        'normal_renewals': normal_renewals,
        'total_renewals': total_renewals,
        'today': today,
    }
    
    return render(request, 'renewal_details.html', context)


def send_renewal_reminder_email(member, vehicle, document_entry, request):
    """
    Send renewal reminder email to member with vehicle details.
    Returns (success: bool, message: str) tuple.
    """
    # Check if member has email
    if not member.user_account or not member.user_account.email:
        return False, "No email address found for member"
    
    email = member.user_account.email
    
    # Calculate days left
    today = timezone.localtime(timezone.now()).date()
    expiry_date = document_entry.renewal_date
    days_left = (expiry_date - today).days
    
    # Determine urgency
    is_urgent = days_left <= 29
    
    # Build portal URL
    portal_url = request.build_absolute_uri('/user-documents/')
    
    # Email context
    context = {
        'member_name': member.full_name,
        'plate_number': vehicle.plate_number,
        'document_type': 'Vehicle Registration',  # Default document type
        'expiry_date': expiry_date.strftime('%B %d, %Y'),
        'days_left': days_left,
        'is_urgent': is_urgent,
        'batch_number': member.batch.number if member.batch else 'N/A',
        'portal_url': portal_url,
    }
    
    # Render email templates
    try:
        html_content = render_to_string('emails/renewal_reminder.html', context)
        text_content = render_to_string('emails/renewal_reminder.txt', context)
    except Exception as e:
        return False, f"Failed to render email template: {str(e)}"
    
    # Email subject
    if days_left <= 0:
        subject = f'⚠️ URGENT: Vehicle {vehicle.plate_number} Registration EXPIRED'
    elif days_left <= 7:
        subject = f'⚠️ URGENT: Vehicle {vehicle.plate_number} Expires in {days_left} Days'
    elif days_left <= 29:
        subject = f'⚠️ Reminder: Vehicle {vehicle.plate_number} Registration Expires Soon'
    else:
        subject = f'Reminder: Vehicle {vehicle.plate_number} Registration Due for Renewal'
    
    try:
        # Create email with both HTML and plain text
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send(fail_silently=False)
        
        return True, f"Email sent successfully to {email}"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


# ===== RENEWALS HUB =====
from .models import Member, Vehicle, Document, DocumentEntry, Batch

@staff_member_required
def renewals_hub(request):
    """
    Central Renewals Hub - Main landing page for renewal management.
    Shows overview cards, filters, and comprehensive table of all renewals.
    """
    today = timezone.localtime(timezone.now()).date()
    
    # Get filter parameters
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '')
    batch_filter = request.GET.get('batch', '')
    status_filter = request.GET.get('status', '')
    
    # Calculate date ranges based on filter
    start_date = None
    end_date = None
    
    if filter_type == 'today':
        start_date = end_date = today
    elif filter_type == 'this_week':
        start_date = today
        end_date = today + timedelta(days=7)
    elif filter_type == 'this_month':
        start_date = today
        end_date = today + timedelta(days=30)
    elif filter_type == 'next_60':
        start_date = today
        end_date = today + timedelta(days=60)
    elif filter_type == 'urgent':
        start_date = today
        end_date = today + timedelta(days=29)
    elif filter_type == 'upcoming':
        start_date = today + timedelta(days=30)
        end_date = today + timedelta(days=60)
    elif filter_type == 'overdue':
        start_date = today - timedelta(days=365)
        end_date = today - timedelta(days=1)
    
    # Get all members with their vehicles and documents
    members_query = Member.objects.select_related('user_account', 'batch').prefetch_related(
        'vehicles__document__entries'
    ).all()
    
    # Apply batch filter
    if batch_filter:
        members_query = members_query.filter(batch_id=batch_filter)
    
    # Apply search filter
    if search_query:
        members_query = members_query.filter(
            Q(full_name__icontains=search_query) |
            Q(vehicles__plate_number__icontains=search_query) |
            Q(vehicles__document__tin__icontains=search_query)
        ).distinct()
    
    # Collect all renewals
    all_renewals = []
    urgent_count = 0
    upcoming_count = 0
    this_month_count = 0
    overdue_count = 0
    
    for member in members_query:
        for vehicle in member.vehicles.all():
            # Get latest approved document entry
            latest_entry = DocumentEntry.objects.filter(
                document__vehicle=vehicle
            ).filter(
                Q(status="approved") | Q(uploaded_by__isnull=True)
            ).order_by('-renewal_date').first()
            
            if latest_entry and latest_entry.renewal_date:
                candidate = latest_entry.renewal_date
                
                # Convert to date if datetime
                if hasattr(candidate, "date"):
                    candidate = candidate.date()
                
                # Normalize expiry date to future
                attempts = 0
                while candidate < today and attempts < 5:
                    candidate = _add_years_safe(candidate, 1)
                    attempts += 1
                
                days_left = (candidate - today).days
                
                # Determine status
                status = 'normal'
                status_class = 'secondary'
                if days_left < 0:
                    status = 'overdue'
                    status_class = 'dark'
                    overdue_count += 1
                elif 0 <= days_left <= 29:
                    status = 'urgent'
                    status_class = 'danger'
                    urgent_count += 1
                elif 30 <= days_left <= 60:
                    status = 'upcoming'
                    status_class = 'warning'
                    upcoming_count += 1
                
                # Count this month
                if 0 <= days_left <= 30:
                    this_month_count += 1
                
                # Apply status filter
                if status_filter and status != status_filter:
                    continue
                
                # Apply date range filter
                if start_date and end_date:
                    if not (start_date <= candidate <= end_date):
                        continue
                
                renewal_info = {
                    'id': latest_entry.id,
                    'member': member,
                    'vehicle': vehicle,
                    'plate': vehicle.plate_number,
                    'tin': getattr(vehicle.document, 'tin', 'N/A') if hasattr(vehicle, 'document') else 'N/A',
                    'expiry_date': candidate,
                    'days_left': days_left,
                    'days_until_overdue': abs(days_left) if days_left < 0 else 0,
                    'status': status,
                    'status_class': status_class,
                    'document_entry': latest_entry,
                }
                
                all_renewals.append(renewal_info)
    
    # Sort by days left (ascending)
    all_renewals.sort(key=lambda x: x['days_left'])
    
    # Get all batches for filter dropdown
    batches = Batch.objects.all().order_by('number')
    
    context = {
        'renewals': all_renewals,
        'urgent_count': urgent_count,
        'upcoming_count': upcoming_count,
        'this_month_count': this_month_count,
        'overdue_count': overdue_count,
        'batches': batches,
        'filter_type': filter_type,
        'today': today,
    }
    
    return render(request, 'renewals/renewal_list.html', context)


@staff_member_required
@require_POST
def send_bulk_renewal_reminders(request):
    """
    Send renewal reminders in bulk based on filter criteria.
    Supports: batch, this_week, this_month, next_60, all
    """
    filter_type = request.POST.get('filter_type', 'all')
    batch_id = request.POST.get('batch_id', '')
    
    today = timezone.localtime(timezone.now()).date()
    
    # Calculate date ranges based on filter
    start_date = None
    end_date = None
    
    if filter_type == 'this_week':
        start_date = today
        end_date = today + timedelta(days=7)
    elif filter_type == 'this_month':
        start_date = today
        end_date = today + timedelta(days=30)
    elif filter_type == 'next_60':
        start_date = today
        end_date = today + timedelta(days=60)
    elif filter_type == 'all':
        start_date = today
        end_date = today + timedelta(days=365)
    
    # Get members based on filters
    members_query = Member.objects.select_related('user_account', 'batch').prefetch_related(
        'vehicles__document__entries'
    ).all()
    
    # Apply batch filter
    if batch_id:
        members_query = members_query.filter(batch_id=batch_id)
    
    # Collect renewals to send
    reminders_sent = 0
    reminders_failed = 0
    
    for member in members_query:
        for vehicle in member.vehicles.all():
            # Get latest approved document entry
            latest_entry = DocumentEntry.objects.filter(
                document__vehicle=vehicle
            ).filter(
                Q(status="approved") | Q(uploaded_by__isnull=True)
            ).order_by('-renewal_date').first()
            
            if latest_entry and latest_entry.renewal_date:
                candidate = latest_entry.renewal_date
                
                # Convert to date if datetime
                if hasattr(candidate, "date"):
                    candidate = candidate.date()
                
                # Normalize expiry date to future
                attempts = 0
                while candidate < today and attempts < 5:
                    candidate = _add_years_safe(candidate, 1)
                    attempts += 1
                
                # Apply date range filter
                if start_date and end_date:
                    if start_date <= candidate <= end_date:
                        # Send reminder
                        try:
                            success, message = send_renewal_reminder_email(member, vehicle, latest_entry, request)
                            if success:
                                reminders_sent += 1
                            else:
                                reminders_failed += 1
                        except Exception as e:
                            reminders_failed += 1
    
    # Display summary message
    if reminders_sent > 0:
        messages.success(request, f"✅ Successfully sent {reminders_sent} renewal reminder(s)!")
    
    if reminders_failed > 0:
        messages.warning(request, f"⚠️ Failed to send {reminders_failed} reminder(s).")
    
    if reminders_sent == 0 and reminders_failed == 0:
        messages.info(request, "No renewals found matching the selected criteria.")
    
    return redirect('renewals_hub')


@staff_member_required
@require_POST
def send_renewal_reminder(request, member_id, vehicle_id):
    """
    Send a renewal reminder to a member for a specific vehicle via email.
    """
    member = get_object_or_404(Member, pk=member_id)
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    
    # Get the vehicle's document and latest entry
    try:
        document = vehicle.document
        latest_entry = document.entries.filter(
            models.Q(uploaded_by__isnull=True) | models.Q(status="approved")
        ).order_by('-renewal_date').first()
        
        if not latest_entry:
            messages.error(request, f"No approved document entry found for vehicle {vehicle.plate_number}")
            date = request.POST.get('date')
            if date:
                return redirect('renewal_details', date=date)
            return redirect('home')
        
        # Send email
        success, message = send_renewal_reminder_email(member, vehicle, latest_entry, request)
        
        if success:
            messages.success(request, f"✅ {message}")
            
            # Create in-app notification
            from .notifications import create_notification
            if member.user_account:
                today = timezone.now().date()
                days_left = (latest_entry.renewal_date - today).days
                create_notification(
                    recipient=member.user_account,
                    title="🔔 Vehicle Renewal Reminder",
                    message=f"Your vehicle {vehicle.plate_number} renewal expires on {latest_entry.renewal_date.strftime('%B %d, %Y')} ({days_left} days).",
                    category='renewal_reminder',
                    priority='urgent',
                    action_url='/user/documents/upload/',
                    action_text='Submit Documents',
                    related_object_type='vehicle',
                    related_object_id=vehicle.id,
                    created_by=request.user
                )
        else:
            messages.error(request, f"❌ {message}")
            
    except Document.DoesNotExist:
        messages.error(request, f"No document found for vehicle {vehicle.plate_number}")
    except Exception as e:
        messages.error(request, f"Error sending reminder: {str(e)}")
    
    # Redirect back to the appropriate page
    from_hub = request.POST.get('from_hub')
    if from_hub:
        return redirect('renewals_hub')
    
    date = request.POST.get('date')
    if date:
        return redirect('renewal_details', date=date)
    return redirect('home')


@staff_member_required
@require_POST
def mark_as_renewed(request, member_id, vehicle_id):
    """
    Mark a vehicle's documents as renewed (create new document entry).
    """
    member = get_object_or_404(Member, pk=member_id)
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    
    # Get or create document for this vehicle
    document, created = Document.objects.get_or_create(
        vehicle=vehicle,
        defaults={'document_type': 'Registration'}
    )
    
    # Create new renewal entry
    new_renewal_date = timezone.now().date()
    next_year = _add_years_safe(new_renewal_date, 1)
    
    DocumentEntry.objects.create(
        document=document,
        renewal_date=next_year,
        status='approved',
        uploaded_by=None,  # Manager created
        approved_by=request.user,
        approved_at=timezone.now(),
        manager_notes='Marked as renewed from calendar view'
    )
    
    messages.success(
        request,
        f"Vehicle {vehicle.plate_number} marked as renewed. Next renewal: {next_year}"
    )
    
    # Redirect back to the renewal details page
    date = request.POST.get('date')
    if date:
        return redirect('renewal_details', date=date)
    return redirect('home')


# ==== Password Reset ====
from .models import PasswordResetToken
from .forms import PasswordResetRequestForm, PasswordResetVerifyForm, PasswordResetConfirmForm
from django.contrib.auth.hashers import make_password

def password_reset_request(request):
    """
    Step 1: User enters email to request password reset.
    Sends 6-digit verification code to email.
    """
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            User = get_user_model()
            user = User.objects.get(email=email)
            
            # Generate verification code
            reset_token = PasswordResetToken.create_code_for_user(user)
            
            # Send verification code via email
            try:
                from django.core.mail import send_mail
                subject = 'POTMPC - Password Reset Verification Code'
                message = f"""
                Hello {user.full_name},

                You have requested to reset your password for your POTMPC account.

                Your verification code is: {reset_token.code}

                This code will expire in 15 minutes.

                If you did not request this password reset, please ignore this email.

                ---
                Palawan Operative Transportation Multi-Purpose Cooperative
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                # Store email in session for next step
                request.session['reset_email'] = email
                messages.success(request, f'✅ Verification code sent to {email}. Please check your inbox.')
                return redirect('password_reset_verify')
                
            except Exception as e:
                messages.error(request, f'❌ Failed to send verification email: {str(e)}')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'registration/password_reset_request.html', {'form': form})


def password_reset_verify(request):
    """
    Step 2: User enters 6-digit verification code.
    Validates code and proceeds to password change.
    """
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            User = get_user_model()
            
            try:
                user = User.objects.get(email=email)
                # Find valid token with this code
                reset_token = PasswordResetToken.objects.filter(
                    user=user,
                    code=code,
                    is_used=False
                ).first()
                
                if reset_token and reset_token.is_valid():
                    # Store token ID in session for final step
                    request.session['reset_token_id'] = reset_token.id
                    messages.success(request, '✅ Code verified! Now set your new password.')
                    return redirect('password_reset_confirm')
                else:
                    messages.error(request, '❌ Invalid or expired verification code.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = PasswordResetVerifyForm()

    return render(request, 'registration/password_reset_verify.html', {
        'form': form,
        'email': email
    })


def password_reset_confirm(request):
    """
    Step 3: User sets new password.
    Updates password in database and marks token as used.
    """
    token_id = request.session.get('reset_token_id')
    email = request.session.get('reset_email')
    
    if not token_id or not email:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('password_reset_request')
    
    try:
        reset_token = PasswordResetToken.objects.get(id=token_id, is_used=False)
        if not reset_token.is_valid():
            messages.error(request, 'Verification code expired. Please start again.')
            return redirect('password_reset_request')
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid token. Please start again.')
        return redirect('password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            
            # Update user password
            user = reset_token.user
            user.password = make_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            # Clear session data
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'reset_token_id' in request.session:
                del request.session['reset_token_id']
            
            messages.success(request, '✅ Password successfully reset! You can now login with your new password.')
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()
    
    return render(request, 'registration/password_reset_confirm.html', {
        'form': form,
        'email': email
    })


# ==== PDF Export Views ====
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import datetime

@login_required
def export_year_pdf(request, year_id, report_type):
    """
    Export payment report for a year.
    report_type: 'all', 'from_members', or 'others'
    """
    year = get_object_or_404(PaymentYear, pk=year_id)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    filename = f'Payment_Report_{year.year}_{report_type}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create the PDF object
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1F3E27'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#5C3A21'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Title
    title_text = f"POTMPC Payment Report - {year.year}"
    if report_type == 'from_members':
        title_text += " (From Members)"
    elif report_type == 'others':
        title_text += " (Other Payments)"
    else:
        title_text += " (All Payments)"
    
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Get payment data
    payment_types = PaymentType.objects.filter(year=year).order_by('payment_type', 'name')
    
    # Filter by report type
    if report_type == 'from_members':
        payment_types = payment_types.filter(payment_type='from_members')
    elif report_type == 'others':
        payment_types = payment_types.filter(payment_type='other')
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    if report_type == 'all':
        # Separate sections for From Members and Others
        from_members_types = payment_types.filter(payment_type='from_members')
        other_types = payment_types.filter(payment_type='other')
        
        if from_members_types.exists():
            elements.append(Paragraph("<b>FROM MEMBERS</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], textColor=colors.HexColor('#1F3E27'))))
            elements.append(Spacer(1, 0.1*inch))
            table_data = _build_payment_table_data(from_members_types, months)
            elements.append(_create_payment_table(table_data))
            elements.append(Spacer(1, 0.3*inch))
        
        if other_types.exists():
            elements.append(Paragraph("<b>OTHER PAYMENTS</b>", ParagraphStyle('SectionHeader', parent=styles['Heading2'], textColor=colors.HexColor('#C99E35'))))
            elements.append(Spacer(1, 0.1*inch))
            table_data = _build_payment_table_data(other_types, months)
            elements.append(_create_payment_table(table_data))
    else:
        table_data = _build_payment_table_data(payment_types, months)
        elements.append(_create_payment_table(table_data))
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


def _build_payment_table_data(payment_types, months):
    """Helper function to build table data for payment report"""
    # Header row
    data = [['Payment Type'] + months]
    
    for payment_type in payment_types:
        row = [payment_type.name]
        for month_num in range(1, 13):
            total = payment_type.entries.filter(month=month_num).aggregate(total=Sum('amount_paid'))['total']
            row.append(f"₱{total:,.2f}" if total else "-")
        data.append(row)
    
    return data


def _create_payment_table(data):
    """Helper function to create styled payment table"""
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F3E27')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2F2F2F')),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (-1, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F6F4ED')]),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D4D0C7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    return table


@login_required
def export_member_pdf(request, year_id, member_id):
    """
    Export individual member payment report for a year.
    """
    year = get_object_or_404(PaymentYear, pk=year_id)
    member = get_object_or_404(Member, pk=member_id)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    filename = f'Payment_Report_{year.year}_{member.full_name.replace(" ", "_")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create the PDF object
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1F3E27'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Title
    elements.append(Paragraph(f"POTMPC Payment Report - {year.year}", title_style))
    elements.append(Paragraph(f"<b>Member:</b> {member.full_name}", ParagraphStyle('MemberName', parent=styles['Normal'], fontSize=14, spaceAfter=6, alignment=TA_CENTER)))
    if member.batch:
        elements.append(Paragraph(f"<b>Batch:</b> {member.batch.number}", ParagraphStyle('Batch', parent=styles['Normal'], fontSize=12, spaceAfter=20, alignment=TA_CENTER)))
    elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ParagraphStyle('Date', parent=styles['Normal'], fontSize=10, spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#5C3A21'))))
    elements.append(Spacer(1, 0.2*inch))
    
    # Get payment data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # From Members payments
    from_members_types = PaymentType.objects.filter(year=year, payment_type='from_members').order_by('name')
    if from_members_types.exists():
        elements.append(Paragraph("<b>FROM MEMBERS</b>", ParagraphStyle('SectionHeader', parent=styles['Heading3'], textColor=colors.HexColor('#1F3E27'), spaceAfter=10)))
        
        fm_data = [['Payment Type'] + months]
        for payment_type in from_members_types:
            row = [payment_type.name]
            for month_num in range(1, 13):
                total = payment_type.entries.filter(month=month_num, member=member).aggregate(total=Sum('amount_paid'))['total']
                row.append(f"₱{total:,.2f}" if total else "-")
            fm_data.append(row)
        
        elements.append(_create_payment_table(fm_data))
        elements.append(Spacer(1, 0.3*inch))
    
    # Other payments
    other_types = PaymentType.objects.filter(year=year, payment_type='other').order_by('name')
    if other_types.exists():
        elements.append(Paragraph("<b>OTHER PAYMENTS</b>", ParagraphStyle('SectionHeader', parent=styles['Heading3'], textColor=colors.HexColor('#C99E35'), spaceAfter=10)))
        
        other_data = [['Payment Type'] + months]
        for payment_type in other_types:
            row = [payment_type.name]
            has_payments = False
            for month_num in range(1, 13):
                total = payment_type.entries.filter(month=month_num, member=member).aggregate(total=Sum('amount_paid'))['total']
                row.append(f"₱{total:,.2f}" if total else "-")
                if total:
                    has_payments = True
            if has_payments:  # Only show payment types with logged amounts
                other_data.append(row)
        
        if len(other_data) > 1:  # Has data beyond header
            elements.append(_create_payment_table(other_data))
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
@require_POST
def email_member_report(request, year_id, member_id):
    """
    Email payment report PDF to member with validations.
    """
    try:
        year = get_object_or_404(PaymentYear, pk=year_id)
        member = get_object_or_404(Member, pk=member_id)
        
        # Validation 1: Check if member has linked user account
        if not member.user_account:
            return JsonResponse({
                'success': False,
                'error': 'Member does not have a linked user account.'
            }, status=400)
        
        # Validation 2: Check if user account has email
        if not member.user_account.email:
            return JsonResponse({
                'success': False,
                'error': 'Member account does not have an email address.'
            }, status=400)
        
        email = member.user_account.email
        
        # Validation 3: Check if member has any payment records
        has_payments = PaymentEntry.objects.filter(
            payment_type__year=year,
            member=member
        ).exists()
        
        if not has_payments:
            return JsonResponse({
                'success': False,
                'error': 'No payment records found for this member.'
            }, status=400)
        
        # Generate PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1F3E27'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Build PDF content
        elements.append(Paragraph(f"POTMPC Payment Report - {year.year}", title_style))
        elements.append(Paragraph(f"<b>Member:</b> {member.full_name}", ParagraphStyle('MemberName', parent=styles['Normal'], fontSize=14, spaceAfter=6, alignment=TA_CENTER)))
        if member.batch:
            elements.append(Paragraph(f"<b>Batch:</b> {member.batch.number}", ParagraphStyle('Batch', parent=styles['Normal'], fontSize=12, spaceAfter=20, alignment=TA_CENTER)))
        elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ParagraphStyle('Date', parent=styles['Normal'], fontSize=10, spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#5C3A21'))))
        elements.append(Spacer(1, 0.2*inch))
        
        # Get payment data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # From Members payments
        from_members_types = PaymentType.objects.filter(year=year, payment_type='from_members').order_by('name')
        if from_members_types.exists():
            elements.append(Paragraph("<b>FROM MEMBERS</b>", ParagraphStyle('SectionHeader', parent=styles['Heading3'], textColor=colors.HexColor('#1F3E27'), spaceAfter=10)))
            
            fm_data = [['Payment Type'] + months]
            for payment_type in from_members_types:
                row = [payment_type.name]
                for month_num in range(1, 13):
                    total = payment_type.entries.filter(month=month_num, member=member).aggregate(total=Sum('amount_paid'))['total']
                    row.append(f"₱{total:,.2f}" if total else "-")
                fm_data.append(row)
            
            elements.append(_create_payment_table(fm_data))
            elements.append(Spacer(1, 0.3*inch))
        
        # Other payments
        other_types = PaymentType.objects.filter(year=year, payment_type='other').order_by('name')
        if other_types.exists():
            elements.append(Paragraph("<b>OTHER PAYMENTS</b>", ParagraphStyle('SectionHeader', parent=styles['Heading3'], textColor=colors.HexColor('#C99E35'), spaceAfter=10)))
            
            other_data = [['Payment Type'] + months]
            for payment_type in other_types:
                row = [payment_type.name]
                has_payments = False
                for month_num in range(1, 13):
                    total = payment_type.entries.filter(month=month_num, member=member).aggregate(total=Sum('amount_paid'))['total']
                    row.append(f"₱{total:,.2f}" if total else "-")
                    if total:
                        has_payments = True
                if has_payments:
                    other_data.append(row)
            
            if len(other_data) > 1:
                elements.append(_create_payment_table(other_data))
        
        # Build PDF
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Send email with PDF attachment
        subject = f'POTMPC Payment Report - {year.year}'
        message = f"""
Dear {member.full_name},

Please find attached your payment report for {year.year}.

This report contains all payment records logged in the POTMPC system for the specified year.

If you have any questions or concerns about your payment records, please contact the cooperative office.

Best regards,
POTMPC Management
"""
        
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        
        # Attach PDF
        filename = f'Payment_Report_{year.year}_{member.full_name.replace(" ", "_")}.pdf'
        email_message.attach(filename, pdf_data, 'application/pdf')
        
        # Send email
        email_message.send(fail_silently=False)
        
        return JsonResponse({
            'success': True,
            'message': f'Payment report sent successfully to {email}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==== CAR WASH VIEWS ====

@staff_member_required
def manage_carwash_compliance(request, year_id):
    """
    Manage global car wash compliance settings for a specific year.
    Handles GET (display settings) and POST (update settings).
    """
    from .models import CarWashCompliance
    from .forms import CarWashComplianceForm
    
    year = get_object_or_404(PaymentYear, pk=year_id)
    
    # Get or create compliance settings for this year
    compliance, created = CarWashCompliance.objects.get_or_create(
        year=year,
        defaults={
            'monthly_threshold': 4,
            'penalty_amount': 0,
            'updated_by': request.user
        }
    )
    
    if request.method == 'POST':
        form = CarWashComplianceForm(request.POST, instance=compliance)
        if form.is_valid():
            compliance = form.save(commit=False)
            compliance.updated_by = request.user
            compliance.save()
            messages.success(request, 'Car wash compliance settings updated successfully.')
            return redirect('coop:carwash_year_detail', year_id=year_id)
    else:
        form = CarWashComplianceForm(instance=compliance)
    
    context = {
        'year': year,
        'form': form,
        'compliance': compliance,
        'page_title': f'Car Wash Compliance Settings - {year.year}'
    }
    return render(request, 'payments/manage_carwash_compliance.html', context)

@staff_member_required
def carwash_year_detail(request, year_id):
    """
    Display car wash records for a specific year.
    Shows COUNTS (not amounts) in a member × month grid.
    Tracks both member and public customers, with service type breakdown.
    """
    from .models import CarWashCompliance
    
    year = get_object_or_404(PaymentYear, pk=year_id)
    
    # Get global compliance settings
    try:
        compliance = CarWashCompliance.objects.get(year=year)
    except CarWashCompliance.DoesNotExist:
        compliance = None
    
    # Get car wash service types
    carwash_types = PaymentType.objects.filter(
        year=year,
        is_car_wash=True
    ).order_by('name')
    
    if not carwash_types.exists():
        # Empty state - no service types configured yet
        return render(request, 'payments/carwash_year_detail.html', {
            'year': year,
            'compliance': compliance,
            'carwash_types': None,
            'members_carwash_data': [],
            'public_customer_data': [],
            'service_type_breakdown': []
        })
    
    # Get all members with vehicles
    members_with_vehicles = Member.objects.filter(
        vehicles__isnull=False
    ).distinct().prefetch_related('vehicles')
    
    members_carwash_data = []
    
    for member in members_with_vehicles:
        # Get all vehicles for this member
        vehicles = member.vehicles.all()
        
        # Count car wash records per month (aggregated across all vehicles)
        monthly_counts = []
        total_count = 0
        
        for month_num in range(1, 13):
            # Count entries for this member in this month (all vehicles combined)
            count = PaymentEntry.objects.filter(
                member=member,
                payment_type__in=carwash_types,
                month=month_num,
                is_car_wash_record=True,
                is_public_customer=False,  # Only member records
                is_penalty=False
            ).count()
            
            monthly_counts.append(count)
            total_count += count
        
        # Check compliance using global threshold
        if compliance:
            # Monthly threshold applies per month
            monthly_threshold = compliance.monthly_threshold
            non_compliant_months = sum(1 for count in monthly_counts if count < monthly_threshold)
            is_compliant = non_compliant_months == 0
        else:
            # No compliance settings configured
            monthly_threshold = 0
            non_compliant_months = 0
            is_compliant = True
        
        members_carwash_data.append({
            'member': member,
            'vehicles': vehicles,
            'monthly_counts': monthly_counts,
            'total_count': total_count,
            'is_compliant': is_compliant,
            'non_compliant_months': non_compliant_months,
            'monthly_threshold': monthly_threshold
        })
    
    # Get public customer statistics (monthly breakdown)
    public_customer_data = []
    public_total = 0
    
    for month_num in range(1, 13):
        count = PaymentEntry.objects.filter(
            payment_type__in=carwash_types,
            month=month_num,
            is_car_wash_record=True,
            is_public_customer=True,
            is_penalty=False
        ).count()
        
        public_customer_data.append(count)
        public_total += count
    
    # Get individual public customer records with names
    public_customer_records = PaymentEntry.objects.filter(
        payment_type__in=carwash_types,
        is_car_wash_record=True,
        is_public_customer=True,
        is_penalty=False
    ).select_related('payment_type').order_by('customer_name', 'month')
    
    # Service type breakdown (how many times each service was used)
    service_type_breakdown = []
    for service_type in carwash_types:
        member_count = PaymentEntry.objects.filter(
            payment_type=service_type,
            is_car_wash_record=True,
            is_public_customer=False,
            is_penalty=False
        ).count()
        
        public_count = PaymentEntry.objects.filter(
            payment_type=service_type,
            is_car_wash_record=True,
            is_public_customer=True,
            is_penalty=False
        ).count()
        
        service_type_breakdown.append({
            'name': service_type.name,
            'member_count': member_count,
            'public_count': public_count,
            'total_count': member_count + public_count
        })
    
    context = {
        'year': year,
        'compliance': compliance,
        'carwash_types': carwash_types,
        'members_carwash_data': members_carwash_data,
        'public_customer_data': public_customer_data,
        'public_total': public_total,
        'public_customer_records': public_customer_records,
        'service_type_breakdown': service_type_breakdown,
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    }
    
    return render(request, 'payments/carwash_year_detail.html', context)


@staff_member_required
def add_carwash_type(request, year_id):
    """
    Create a new car wash service type for the year (e.g., Basic, Premium, Deluxe).
    This is used to track which type of service was provided, not for compliance settings.
    Compliance settings are managed globally via manage_carwash_compliance view.
    """
    year = get_object_or_404(PaymentYear, pk=year_id)
    
    if request.method == 'POST':
        from .forms import CarWashTypeForm
        form = CarWashTypeForm(request.POST)
        
        if form.is_valid():
            carwash_type = form.save(commit=False)
            carwash_type.year = year
            carwash_type.payment_type = 'from_members'
            # is_car_wash is set to True automatically in the form's save() method
            carwash_type.save()
            
            messages.success(request, f'Car wash service type "{carwash_type.name}" created successfully!')
            return redirect('carwash_year_detail', year_id=year.id)
    else:
        from .forms import CarWashTypeForm
        form = CarWashTypeForm()
    
    return render(request, 'payments/add_carwash_type.html', {
        'form': form,
        'year': year
    })


@staff_member_required
def edit_carwash_type(request, year_id, type_id):
    """
    Edit an existing car wash service type (e.g., rename Basic to Standard).
    Only the name can be edited. Compliance settings are managed globally.
    """
    year = get_object_or_404(PaymentYear, pk=year_id)
    carwash_type = get_object_or_404(PaymentType, pk=type_id, year=year, is_car_wash=True)
    
    if request.method == 'POST':
        from .forms import CarWashTypeForm
        form = CarWashTypeForm(request.POST, instance=carwash_type)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Car wash service type "{carwash_type.name}" updated successfully!')
            return redirect('carwash_year_detail', year_id=year.id)
    else:
        from .forms import CarWashTypeForm
        form = CarWashTypeForm(instance=carwash_type)
    
    return render(request, 'payments/edit_carwash_type.html', {
        'form': form,
        'year': year,
        'carwash_type': carwash_type
    })


@staff_member_required
def add_carwash_record(request, year_id):
    """
    Log a car wash record for either a member's vehicle or a public customer.
    Supports both member and public customer tracking with service type selection.
    Amount is automatically set from the payment type's car_wash_amount.
    """
    year = get_object_or_404(PaymentYear, pk=year_id)
    
    # Check if car wash service types exist
    carwash_types = PaymentType.objects.filter(year=year, is_car_wash=True)
    if not carwash_types.exists():
        messages.error(request, 'No car wash service types configured for this year. Please add a service type first.')
        return redirect('add_carwash_type', year_id=year.id)
    
    if request.method == 'POST':
        from .forms import CarWashRecordForm
        form = CarWashRecordForm(request.POST, year_id=year_id)
        
        if form.is_valid():
            entry = form.save(commit=False)
            
            # Set car wash flags explicitly (cleaned_data values don't auto-transfer to model)
            customer_type = form.cleaned_data.get('customer_type')
            entry.is_car_wash_record = True
            entry.is_public_customer = (customer_type == 'public')
            
            # Set amount from payment type (critical: amount_paid is NOT NULL in DB)
            payment_type = form.cleaned_data.get('payment_type')
            if payment_type and payment_type.car_wash_amount:
                entry.amount_paid = payment_type.car_wash_amount
            else:
                entry.amount_paid = 0  # Fallback to 0 if no amount set
            
            entry.is_penalty = False
            entry.recorded_by = request.user
            entry.save()
            
            # Success message based on customer type
            if entry.is_public_customer:
                messages.success(request, f'Car wash record added for public customer: {entry.customer_name} (₱{entry.amount_paid})')
            else:
                messages.success(request, f'Car wash record added for {entry.member.full_name} - {entry.vehicle.plate_number} (₱{entry.amount_paid})')
            
            return redirect('carwash_year_detail', year_id=year.id)
    else:
        from .forms import CarWashRecordForm
        form = CarWashRecordForm(year_id=year_id)
    
    return render(request, 'payments/add_carwash_record.html', {
        'form': form,
        'year': year,
        'carwash_types': carwash_types
    })


# ============================================================================
# NOTIFICATION SYSTEM VIEWS
# ============================================================================

@login_required
def notification_count_api(request):
    """Get unread notification count (API endpoint)"""
    from .notifications import get_unread_count
    count = get_unread_count(request.user)
    return JsonResponse({'count': count})


@login_required
@require_POST
def notification_mark_read(request, notification_id):
    """Mark single notification as read"""
    from .models import Notification
    notification = get_object_or_404(
        Notification, 
        pk=notification_id, 
        recipient=request.user
    )
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.META.get('HTTP_REFERER', 'notifications_center'))


@login_required
@require_POST
def notifications_mark_all_read(request):
    """Mark all notifications as read"""
    from .notifications import mark_all_as_read
    count = mark_all_as_read(request.user)
    messages.success(request, f"Marked {count} notification{'s' if count != 1 else ''} as read.")
    return redirect('notifications_center')


@login_required
@require_POST
def notifications_delete_read(request):
    """Delete all read notifications"""
    from .models import Notification
    count, _ = Notification.objects.filter(
        recipient=request.user,
        is_read=True
    ).delete()
    messages.success(request, f"Deleted {count} read notification{'s' if count != 1 else ''}.")
    return redirect('notifications_center')


@login_required
def notifications_center(request):
    """Notification center page with filters and pagination"""
    from .models import Notification
    from django.core.paginator import Paginator
    
    filter_type = request.GET.get('filter', 'all')
    
    notifications_qs = Notification.objects.filter(
        recipient=request.user
    )
    
    if filter_type == 'unread':
        notifications_qs = notifications_qs.filter(is_read=False)
    elif filter_type == 'urgent':
        notifications_qs = notifications_qs.filter(priority='urgent')
    elif filter_type == 'high':
        notifications_qs = notifications_qs.filter(priority='high')
    
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Pagination
    paginator = Paginator(notifications_qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filter': filter_type,
        'unread_count': unread_count,
    }
    
    # Use different template based on user role
    if hasattr(request.user, 'role') and request.user.role == 'client':
        template_name = 'notifications/user_notifications_center.html'
    else:
        template_name = 'notifications/notifications_center.html'
    
    return render(request, template_name, context)

