# ==== Imports ====
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.forms import inlineformset_factory

from .models import Member, Vehicle
from .forms import MemberForm, VehicleForm

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
        # Validate member form first
        if member_form.is_valid():
            member = member_form.save()
            # Assign selected vehicle to this member if chosen
            vehicle = member_form.cleaned_data.get('vehicle')
            if vehicle:
                vehicle.member = member
                vehicle.save()
            # Handle new vehicle creation via formset
            formset = VehicleFormSet(request.POST, instance=member)
            if formset.is_valid():
                formset.save()
                return redirect("member-list")
        else:
            # If member form is invalid, still bind formset for error display
            formset = VehicleFormSet(request.POST)
    else:
        # GET request: show empty forms
        member_form = MemberForm()
        formset = VehicleFormSet()
    return render(request, "member_add.html", {"form": member_form, "formset": formset})

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
            # Assign selected vehicle to this member if chosen
            vehicle = member_form.cleaned_data.get('vehicle')
            if vehicle:
                vehicle.member = member
                vehicle.save()
            formset.save()
            return redirect("member-list")
    else:
        # GET request: show forms pre-filled with member and their vehicles
        member_form = MemberForm(instance=member)
        formset = VehicleFormSet(instance=member)
    return render(request, "member_add.html", {"form": member_form, "formset": formset})

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
        # Filter queryset based on search query
        queryset = super().get_queryset()
        q = self.request.GET.get("q", "")
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(gmail__icontains=q) |
                Q(batch__number__icontains=q) |
                Q(file_number__icontains=q) |
                Q(renewal_date__icontains=q) |
                Q(vehicle__plate_number__icontains=q)
            )
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
    success_url = reverse_lazy("vehicle-list")

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
    success_url = reverse_lazy("vehicle-list")

@method_decorator(login_required, name='dispatch')
class VehicleDeleteView(DeleteView):
    """
    Handles deletion of a Vehicle.
    - Shows confirmation page.
    - Redirects to vehicle list after deletion.
    """
    model = Vehicle
    template_name = "vehicle_confirm_delete.html"
    success_url = reverse_lazy("vehicle-list")

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
