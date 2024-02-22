from typing import Any
from django.shortcuts import render , redirect , reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views import generic 
from agents.mixins import OrganisorAndLoginRequiredMixin
from .models import Lead , Agent , Category
from .forms import LeadForm, LeadModelForm , CustomUserCreationForm, AssignAgentForm , LeadCategoryUpdateForm
from django.shortcuts import render
from .models import Lead
from django.db import models
from django.db.models import Count, F, ExpressionWrapper, FloatField, Q
from django.db.models.functions import TruncDay, TruncMonth



def lead_chart(request):
    # Daily lead count
    daily_lead_data = Lead.objects.values('date_added__date').annotate(lead_count=Count('id'))
    
    # Monthly lead count
    monthly_lead_data = Lead.objects.annotate(month=TruncMonth('date_added')).values('month').annotate(lead_count=Count('id'))

    daily_labels = [str(item['date_added__date']) for item in daily_lead_data]
    daily_data = [item['lead_count'] for item in daily_lead_data]

    monthly_labels = [str(item['month']) for item in monthly_lead_data]
    monthly_data = [item['lead_count'] for item in monthly_lead_data]

    context = {
        'title': 'Leads Added per Day and Month',
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
    }
    return render(request, 'leads/lead_chart.html', context)


def lead_conversion(request):
    # Daily conversion rate
    daily_conversion_data = Lead.objects.values('date_added__date').annotate(
        lead_count=Count('id'),
        converted_count=Count('id', filter=models.Q(category__name='Converted'))
    )
    daily_labels = [str(item['date_added__date']) for item in daily_conversion_data]
    total_leads = [item['lead_count'] for item in daily_conversion_data]
    converted_leads = [item['converted_count'] for item in daily_conversion_data]
    conversion_rate_data = [
        (converted / total) * 100 if total > 0 else 0
        for total, converted in zip(total_leads, converted_leads)
    ]

    # Monthly conversion rate
    monthly_conversion_data = Lead.objects.annotate(month=TruncMonth('date_added')).values('month').annotate(
        total_leads=Count('id'),
        converted_leads=Count('id', filter=Q(category__name='Converted')),
    )
    monthly_labels = [str(item['month']) for item in monthly_conversion_data]
    monthly_conversion_data = [
        (converted / total) * 100 if total > 0 else 0
        for total, converted in zip(
            [item['total_leads'] for item in monthly_conversion_data],
            [item['converted_leads'] for item in monthly_conversion_data]
        )
    ]

    context = {
        'title': 'Lead Conversion',
        'daily_labels': daily_labels,
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'conversion_rate_data': conversion_rate_data,
        'monthly_labels': monthly_labels,
        'monthly_conversion_data': monthly_conversion_data,
    }

    return render(request, 'leads/lead_conversion.html', context)



class SignupView(generic.CreateView):
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse ("leads:lead-list")


class LandingPageView(generic.TemplateView):
    template_name = "landing.html"


def landing_page(request):
    return render(request, "landing.html")


class LeadListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/lead_list.html"
    context_object_name = "leads"

    def get_queryset(self):
        user = self.request.user

        #initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile, agent__isnull=False)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation, agent__isnull=False )
            #filter for the agent that is logged in
            queryset = queryset.filter(agent__user= user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile, agent__isnull=True)
        context.update({
            "unassigned_leads": queryset
        })
        return context



def lead_list(request):
    leads = Lead.objects.all()
    context = {
        "leads":leads
    }    
    return render(request,"leads/lead_list.html", context)


class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        user = self.request.user
        
        #initial queryset of leads for the entire organisation
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            #filter for the agent that is logged in
            queryset = queryset.filter(agent__user= user)
        return queryset


def lead_detail(request, pk):
    lead = Lead.objects.get(id=pk)
    context = {
        "lead": lead
    }
    return render(request,"leads/lead_detail.html", context)


class LeadCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    template_name = "leads/lead_create.html"
    form_class = LeadModelForm 

    def get_success_url(self):
        return reverse ("leads:lead-list")
    
    def form_valid(self , form):
        lead = form.save(commit=False)
        lead.organisation = self.request.user.userprofile
        lead.save()
        send_mail(
            subject = "A lead has been created", 
            message="Go to the site to see the new lead", 
            from_email="test@test.com",
            recipient_list=["test2@test.com"]
        )
        return super(LeadCreateView, self).form_valid(form)



def lead_create(request):
    form = LeadModelForm()
    print(request.POST)
    if request.method == "POST":
        form = LeadModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/leads")
    context = {
        "form": form
    }
    return render(request, "leads/lead_create.html", context)


class LeadUpdateView(OrganisorAndLoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_update.html"
    form_class = LeadModelForm 

    def get_queryset(self):
        user = self.request.user
        #initial queryset of leads for the entire organisation
        return Lead.objects.filter(organisation=user.userprofile)

    def get_success_url(self):
        return reverse ("leads:lead-list")


def lead_update(request, pk):
    lead = Lead.objects.get(id=pk)
    form = LeadModelForm(instance=lead)
    if request.method == "POST":
        form = LeadModelForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect("/leads")
    context = {
        "form": form,
        "lead": lead
    }
    return render(request, "leads/lead_update.html", context)


class LeadDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    template_name = "leads/lead_delete.html"

    def get_success_url(self):
        return reverse ("leads:lead-list")
    
    def get_queryset(self):
        user = self.request.user
        #initial queryset of leads for the entire organisation
        return Lead.objects.filter(organisation=user.userprofile)


def lead_delete(request, pk):
    lead = Lead.objects.get(id=pk)
    lead.delete()
    return redirect("/leads")



class AssignAgentView(OrganisorAndLoginRequiredMixin, generic.FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request":self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse("leads:lead-list")
    
    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)



class CategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
        
        context.update({
            "unassigned_lead_count": queryset.filter(category__isnull=True).count()
        })
        return context


    def get_queryset(self):
        user = self.request.user
        #initial queryset of leads for entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(organisation=user.userprofile)
        else:
            queryset = Category.objects.filter(organisation=user.agent.organisation)
        return queryset


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    # def get_context_data(self, **kwargs):
    #     context = super(CategoryDetailView, self).get_context_data(**kwargs)
    #     leads = self.get_object().leads.all()
    #     context.update({
    #         "leads" : leads
    #     })
    #     return context

    def get_queryset(self):
        user = self.request.user
        #initial queryset of leads for entire organisation
        if user.is_organisor:
            queryset = Category.objects.filter(
                organisation=user.userprofile
            )
        else:
            queryset = Category.objects.filter(
                organisation=user.agent.organisation
            )
        return queryset


class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm 

    def get_queryset(self):
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=user.userprofile)
        else:
            queryset = Lead.objects.filter(organisation=user.agent.organisation)
            #filter for the agent that is logged in
            queryset = queryset.filter(agent__user= user)
        return queryset
    
    def get_success_url(self):
        return reverse ("leads:lead-detail", kwargs={"pk": self.get_object().id})









# def lead_update(request, pk):
#     lead = Lead.objects.get(id=pk)
#     form = LeadForm(request.POST)
#     if form.is_valid():
#             print("Form is Valid")
#             print(form.cleaned_data)
#             first_name = form.cleaned_data['first_name']
#             last_name = form.cleaned_data['last_name']
#             age = form.cleaned_data['age']
#             agent = Agent.objects.first()
#             lead.first_name = first_name
#             lead.last_name = last_name
#             lead.age = age
#             lead.save()
#             return redirect("/leads")
    
#     context = {
#         "form": form,
#         "lead": lead
#     }
#     return render(request, "leads/lead_update.html", context)


# def lead_create(request):
#     form = LeadForm()
#     print(request.POST)
#     if request.method == "POST":
#         print('Receiving a post request')
    #     form = LeadForm(request.POST)
    #     if form.is_valid():
    #         print("Form is Valid")
    #         print(form.cleaned_data)
    #         first_name = form.cleaned_data['first_name']
    #         last_name = form.cleaned_data['last_name']
    #         age = form.cleaned_data['age']
    #         agent = Agent.objects.first()
    #         Lead.objects.create(
    #             first_name=first_name,
    #             last_name=last_name,
    #             age=age,
    #             agent=agent
    #         )
            
    #         return redirect("/leads")
    # context = {
    #     "form": form
    # }
#     return render(request, "leads/lead_create.html", context)



