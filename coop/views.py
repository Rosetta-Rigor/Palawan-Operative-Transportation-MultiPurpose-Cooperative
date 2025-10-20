from django.views.decorators.http import require_POST
# ==== User Approval (Admin) ====
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from matplotlib.style import context
from .models import Batch, User, Member
import json
from django.utils import timezone
from datetime import timedelta

from django.db import models
from django.contrib import messages
from .models import Announcement
from .forms import AnnouncementForm
from django.db.models import Q

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
    logout(request)
    request.session.flush()  # Clear all session data
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST, request.FILES)  # <-- Add request.FILES
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require admin approval
            user.save()
            request.session.cycle_key()
            return redirect('login')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'registration/register_standalone.html', {'form': form})
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
                formset.save()
                if selected_vehicle:
                    # Untie from previous member if necessary
                    if selected_vehicle.member and selected_vehicle.member != member:
                        prev = selected_vehicle.member
                        selected_vehicle.member = member
                    else:
                        selected_vehicle.member = member
                    selected_vehicle.save()
                return redirect("member_list")
        else:
            formset = VehicleFormSet(request.POST)
    else:
        member_form = MemberForm()
        formset = VehicleFormSet()
    return render(request, "member_add.html", {"form": member_form, "formset": formset})

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
    # Only show entries submitted by users and pending
    documents = DocumentEntry.objects.filter(
        status="pending",
        uploaded_by__isnull=False
    ).select_related("document", "document__vehicle", "document__vehicle__member", "uploaded_by").order_by("-id")
    return render(request, "approve_documents.html", {"documents": documents})

@staff_member_required
@require_POST
def approve_document(request, doc_id):
    entry = get_object_or_404(DocumentEntry, pk=doc_id)
    entry.status = "approved"
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.manager_notes = request.POST.get("manager_notes", "")
    entry.save()
    messages.success(request, "Document entry approved.")
    return redirect("approve_documents")

@staff_member_required
@require_POST
def reject_document(request, doc_id):
    entry = get_object_or_404(DocumentEntry, pk=doc_id)
    entry.status = "rejected"
    entry.approved_by = request.user
    entry.approved_at = timezone.now()
    entry.manager_notes = request.POST.get("manager_notes", "")
    entry.save()
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
        # In real app, save uploaded file and details
        pass
    return render(request, "user_upload_document.html")

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
    - Redirects to vehicle list after creation.
    """
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicle_add.html"
    success_url = reverse_lazy("vehicle_list")

@method_decorator(login_required, name='dispatch')
class VehicleUpdateView(UpdateView):
    """
    Handles editing of an existing Vehicle.
    - Uses VehicleForm for input.
    - Redirects to vehicle list after update.
    """
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicle_add.html"
    success_url = reverse_lazy("vehicle_list")

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
    data = {}
    if vehicle_id:
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
    # Always clear session and logout on GET
    if request.method == "GET":
        logout(request)
        request.session.flush()
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
    users = User.objects.all()
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone_number__icontains=q) |
            Q(role__icontains=q)
        )
    users = User.objects.filter(role__iexact='client')
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone_number__icontains=q)
        )
    members = Member.objects.all()
    available_members = Member.objects.filter(user_account__isnull=True)
    context = {'users': users, 'members': members, 'available_members': available_members}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('includes/account_table_rows.html', context, request=request)
        return JsonResponse({'html': html})
    return render(request, 'accounts.html', context)

@require_POST
def deactivate_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = False
    user.save()
    return redirect('accounts_list')

@login_required
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

@require_POST
def activate_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = True
    user.save()
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

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Member, Document, DocumentEntry, User

@staff_member_required
def member_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    # safely get linked user account (None if not connected)
    user_account = getattr(member, 'user_account', None)

    vehicles = list(member.vehicles.all()) if hasattr(member, 'vehicles') else []
    documents = list(Document.objects.filter(vehicle__in=vehicles)) if vehicles else []

    # build mapping of entries and attach to documents
    entries_qs = DocumentEntry.objects.filter(document__in=documents).order_by('renewal_date')
    doc_entries = {}
    for e in entries_qs:
        doc_entries.setdefault(e.document_id, []).append(e)
    # attach entries list to each document object (avoid clobbering related manager)
    for doc in documents:
        doc.entries_list = doc_entries.get(doc.id, [])

    return render(request, 'member_detail.html', {
        'member': member,
        'user_account': user_account,   # pass user object (or None) to template
        'vehicles': vehicles,
        'documents': documents,
    })


from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import Member

@require_GET
@login_required
def member_search_api(request):
    q = request.GET.get('q', '').strip()
    members = Member.objects.filter(full_name__icontains=q)[:10] if q else []
    results = [{'id': m.id, 'text': m.full_name} for m in members]
    return JsonResponse({'results': results})


@require_GET
@login_required
def user_search_api(request):
    """
    Search API for User objects used by Select2 AJAX widgets.
    Returns JSON in Select2 { results: [{id, text}, ...] } format.
    """
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    q = request.GET.get('q', '').strip()
    if not q:
        users = []
    else:
        users = UserModel.objects.filter(
            Q(username__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q)
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
    total_members = Member.objects.count()
    accounts_count = User.objects.filter(is_active=True).count()
    vehicles_count = Vehicle.objects.count()
    batch_count = Batch.objects.count()
    document_count = Document.objects.count()

    # Prepare batch cards data
    batch_cards = []
    for batch in Batch.objects.all():
        members_qs = batch.members.select_related('user_account').all().order_by('full_name')
        paginator = Paginator(members_qs, 10)
        page_number = request.GET.get(f'batch_{batch.id}_page', 1)
        page_obj = paginator.get_page(page_number)
        members_data = []
        for member in page_obj.object_list:
            # Get vehicle and document
            vehicle = member.vehicles.first()
            document = vehicle.document if vehicle and hasattr(vehicle, 'document') else None
            # Get latest renewal date from DocumentEntry
            expiry_date = None
            if document:
                latest_entry = document.entries.order_by('-renewal_date').first()
                if latest_entry and latest_entry.renewal_date:
                    expiry_date = latest_entry.renewal_date.replace(year=latest_entry.renewal_date.year + 1)
            members_data.append({
                'full_name': member.full_name,
                'expiry_date': expiry_date.strftime('%Y-%m-%d') if expiry_date else 'N/A'
            })
        batch_cards.append({
            'id': batch.id,
            'number': batch.number,
            'members': members_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_number': page_obj.number,
            'num_pages': paginator.num_pages,
        })

    context = {
        'total_members': total_members,
        'accounts_count': accounts_count,
        'vehicles_count': vehicles_count,
        'batch_count': batch_count,
        'document_count': document_count,
        'batch_cards': batch_cards,
    }
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
    """
    user = request.user
    if getattr(user, "role", None) != "client":
        messages.error(request, "Only client users can upload document entries.")
        return redirect("home")

    member = getattr(user, "member_profile", None)
    if not member:
        messages.error(request, "No member profile assigned to your account.")
        return redirect("user_home")

    document = None
    vehicle = None
    for v in member.vehicles.all():
        if getattr(v, "document", None):
            vehicle = v
            document = v.document
            break

    if not document:
        messages.error(request, "No document assigned to your vehicle. Contact your manager.")
        return redirect("user_home")

    # List user's entries for this document
    user_entries = DocumentEntry.objects.filter(document=document, uploaded_by=user).order_by('-id')

    if request.method == "POST":
        form = DocumentEntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.document = document
            entry.uploaded_by = user
            entry.status = "pending"
            entry.save()
            messages.success(request, "Document uploaded successfully and is pending manager approval.")
            return redirect("user_upload_document")
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
    })