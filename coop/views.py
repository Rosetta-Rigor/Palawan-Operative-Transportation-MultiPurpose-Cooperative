from django.views.decorators.http import require_POST
# ==== User Approval (Admin) ====
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from .models import User, Member

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
def home(request):
    """
    Renders the home page for logged-in users.
    """
    return render(request, "home.html")

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
            # Handle new vehicle creation via formset
            formset = VehicleFormSet(request.POST, instance=member)
            if formset.is_valid():
                formset.save()
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
            member_form.save()
            formset.save()
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

@staff_member_required
def approve_documents(request):
    """
    View to list and approve user-uploaded documents.
    Placeholder: shows sample documents for now.
    """
    documents = [
        {'id': 1, 'name': 'OR 2025', 'user': 'Qiyana', 'date_uploaded': '2025-09-16', 'status': 'Pending'},
        {'id': 2, 'name': 'CR 2025', 'user': 'Qiyana', 'date_uploaded': '2025-09-16', 'status': 'Approved'},
    ]
    return render(request, "approve_documents.html", {"documents": documents})

@staff_member_required
def approve_document(request, doc_id):
    """
    POST endpoint to approve a document (placeholder logic).
    """
    # In real app, update document status in DB
    return redirect('approve_documents')

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

@method_decorator(login_required, name='dispatch')
class MemberListView(ListView):
    """
    Displays a paginated list of members.
    - Supports search via 'q' GET parameter (searches name, gmail, batch, etc.).
    - If AJAX request, returns only the table rows HTML for dynamic updates.
    """
    model = Member
    template_name = "memberlist.html"
    context_object_name = "object_list"
    paginate_by = 10

    def get_queryset(self):
        # Filter queryset based on search query, matching new Member model fields
        queryset = super().get_queryset().select_related('batch').prefetch_related('vehicles')
        q = self.request.GET.get("q", "")
        if q:
            queryset = queryset.filter(
                Q(full_name__icontains=q) |
                Q(batch__name__icontains=q) |
                Q(batch_monitoring_number__icontains=q) |
                Q(vehicles__plate_number__icontains=q)
            ).distinct()
        return queryset

    def render_to_response(self, context, **response_kwargs):
        # If AJAX request, return only table rows HTML for live search
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string("includes/member_table_rows.html", context)
            return JsonResponse({'html': html})
        # Otherwise, render full template
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
    success_url = reverse_lazy("member-list")

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
        queryset = super().get_queryset()
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
                Q(member__name__icontains=q)
            )
        return queryset

    def render_to_response(self, context, **response_kwargs):
        # If AJAX request, return only table rows HTML for live search
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                "includes/vehicle_table_rows.html", context, request=self.request
            )
            return JsonResponse({'html': html})
        # Otherwise, render full template
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

@method_decorator(login_required, name='dispatch')
class DocumentListView(ListView):
    """
    Displays a paginated list of documents.
    Shows vehicle, member, renewal date, and links to OR/CR images.
    """
    model = Document
    template_name = "documentlist.html"
    context_object_name = "object_list"
    paginate_by = 10

def get_queryset(self):
        queryset = Document.objects.all()
        q = self.request.GET.get('q')
        if q:
                queryset = queryset.filter(tin__icontains=q)
        return queryset

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

# ==== Custom Login View ====
def custom_login(request):
    # Always clear session and logout on GET
    if request.method == "GET":
        logout(request)
        request.session.flush()
        return render(request, "login.html")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
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
            messages.error(request, "Invalid username or password.")
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

def document_add(request):
    if request.method == "POST":
        doc_form = DocumentForm(request.POST)
        entry_form = DocumentEntryForm(request.POST, request.FILES)
        if doc_form.is_valid() and entry_form.is_valid():
            document = doc_form.save()
            entry = entry_form.save(commit=False)
            entry.document = document
            entry.save()
            return redirect("document_list")
    else:
        doc_form = DocumentForm()
        entry_form = DocumentEntryForm()
    return render(request, "document_add.html", {"form": doc_form, "entry_form": entry_form})

class DocumentDetailView(DetailView):
    model = Document
    template_name = "document_detail.html"
    context_object_name = "document"

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
    users = User.objects.all()
    available_members = Member.objects.filter(user_account__isnull=True)
    return render(request, 'accounts.html', {'users': users, 'available_members': available_members})

@require_POST
def deactivate_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = False
    user.save()
    return redirect('accounts_list')

@require_POST
def edit_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    member_id = request.POST.get('member_id')
    if member_id:
        member = get_object_or_404(Member, pk=member_id)
        # Remove previous member link if exists
        old_member = getattr(user, 'member_profile', None)
        if old_member:
            old_member.user_account = None
            old_member.save()
        user.member_profile = member
        member.user_account = user
        user.save()
        member.save()
    return redirect('accounts_list')

@require_POST
def activate_account(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = True
    user.save()
    return redirect('accounts_list')