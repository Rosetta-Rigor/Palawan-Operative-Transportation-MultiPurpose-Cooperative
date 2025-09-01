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
VehicleFormSet = inlineformset_factory(
    Member, Vehicle, form=VehicleForm, fields="__all__", extra=1, can_delete=True
)

# ==== Function-based Views ====
@login_required
def home(request):
    return render(request, "home.html")

@login_required
def member_add(request):
    if request.method == "POST":
        member_form = MemberForm(request.POST)
        if member_form.is_valid():
            member = member_form.save()
            formset = VehicleFormSet(request.POST, instance=member)
            if formset.is_valid():
                formset.save()
                return redirect("member-list")
        else:
            formset = VehicleFormSet(request.POST)
    else:
        member_form = MemberForm()
        formset = VehicleFormSet()
    return render(request, "member_add.html", {"form": member_form, "formset": formset})

@login_required
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == "POST":
        member_form = MemberForm(request.POST, instance=member)
        formset = VehicleFormSet(request.POST, instance=member)
        if member_form.is_valid() and formset.is_valid():
            member_form.save()
            formset.save()
            return redirect("member-list")
    else:
        member_form = MemberForm(instance=member)
        formset = VehicleFormSet(instance=member)
    return render(request, "member_add.html", {"form": member_form, "formset": formset})

# ==== Class-based Views: Member ====
@method_decorator(login_required, name='dispatch')
class MemberListView(ListView):
    model = Member
    template_name = "memberlist.html"
    context_object_name = "object_list"
    paginate_by = 10

    def get_queryset(self):
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
        # This is the updated code for AJAX detection
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string("includes/member_table_rows.html", context)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)

@method_decorator(login_required, name='dispatch')
class MemberDeleteView(DeleteView):
    model = Member
    template_name = "member_confirm_delete.html"
    success_url = reverse_lazy("member-list")

# ==== Class-based Views: Vehicle ====
@method_decorator(login_required, name='dispatch')
class VehicleListView(ListView):
    model = Vehicle
    template_name = "vehiclelist.html"
    context_object_name = "object_list"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(plate_number__icontains=q) |
                Q(member__name__icontains=q)
            )
        return queryset

@method_decorator(login_required, name='dispatch')
class VehicleCreateView(CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicle_add.html"
    success_url = reverse_lazy("vehicle-list")

@method_decorator(login_required, name='dispatch')
class VehicleUpdateView(UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "vehicle_add.html"
    success_url = reverse_lazy("vehicle-list")

@method_decorator(login_required, name='dispatch')
class VehicleDeleteView(DeleteView):
    model = Vehicle
    template_name = "vehicle_confirm_delete.html"
    success_url = reverse_lazy("vehicle-list")
