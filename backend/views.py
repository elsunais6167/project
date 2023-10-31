from datetime import timedelta
from datetime import date

from django.db.models import Q
from django.db.models import Sum
from django.db.models import Count

from django.shortcuts import render, redirect,get_object_or_404
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect

from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.encoding import force_bytes

from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

from .tokens import account_activation_token
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string

#models
from .models import CustomUser
from .models import Profile
from .models import Organisation

from .models import PostEventReport
from .models import COPEventAnnouncement
from .models import COPEventApplication
from .models import COPParticipant
from .models import Invoice

from .models import Activist
from .models import Announcement
from .models import Event

#forms
from django import forms
from .forms import OrgEventForm
from .forms import RegisterForm
from .forms import InvoiceForm
from .forms import PaidForm
from .forms import CustomPasswordResetForm
from .forms import CustomSetPasswordForm
from .forms import CustomPasswordChangeForm
from .forms import OrganisationForm
from .forms import StatusForm
from .forms import DelegateForm
from .forms import EventForm
from .forms import ReportForm
from .forms import AnnouncementForm

# Create your views here.
handler404 = TemplateView.as_view(template_name="404.html")


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        print(f"Decoded UID: {uid}")

        user = CustomUser.objects.get(pk=uid)

        print(f"Fetched user with email: {user.email}")
    except (TypeError, ValueError, OverflowError) as e:
        print(f"Error while decoding UID: {e}")
        user = None
    except CustomUser.DoesNotExist:
        print(f"No user found with UID: {uid}")
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_verified = True
        user.save()
        return redirect(reverse('login'))
    else:
        return HttpResponse('Activation link is invalid!')


def index(request):
    event = COPEventApplication.objects.all()
    delegates = COPParticipant.objects.count()
    organisations = Organisation.objects.count()
    side_events = COPEventApplication.objects.filter(status='Approved').count()
    
    report = PostEventReport.objects.filter(event__isnull=False).order_by('-id')[:3]
    total_speakers = COPEventApplication.objects.filter(posteventreport__isnull=False).aggregate(Sum('number_of_speakers'))['number_of_speakers__sum'] or 0
    host = COPEventApplication.objects.filter(posteventreport__isnull=False).values('org').annotate(Count('org')).count()
    session = PostEventReport.objects.filter(event__isnull=False).count()
    
    total_duration = timedelta()
    for event in COPEventApplication.objects.filter(posteventreport__isnull=False):
        total_duration += event.end_time - event.start_time
    total_duration = total_duration.total_seconds() / 3600
    total_duration = int(total_duration)

    today = date.today()

    events_today = COPEventApplication.objects.filter(
        Q(start_time__date=today)
    )

    context = {
        'report': report,
        'session': session,
        'total_speakers': total_speakers,
        'total_duration': total_duration,
        'host': host,
        'delegates': delegates,
        'organisations': organisations,
        'side_events': side_events,
        'events_today': events_today,
    }

    return render(request, 'home.html', context)


def signin(request):
    context = {}

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_verified: 
                login(request, user)

                try:
                    user_role = user.role 
                    if user_role == 'Super Admin':
                        return redirect('super-dash')
                    elif user_role == 'Admin':
                        return redirect('admin-cop')
                    elif user_role == 'Organisation':
                        if Organisation.objects.filter(user=user).exists():
                            return redirect('org_dashbord')
                        else:
                            return redirect('org_profile')
                    elif user_role == 'Activist':
                        return redirect('activist')
                    else:
                        context['error_message'] = 'Contact the administrator for a designated role.'
                except Profile.DoesNotExist: 
                    context['error_message'] = 'Profile information is missing. Contact the administrator.'
            else:
                context['login_error'] = 'Account is not verified. Please check your emails and verify your account first.'
        else:
            context['login_error'] = 'Invalid credentials.'

    return render(request, 'account/login.html', context)

def loggingout(request):
    logout(request)
    return HttpResponseRedirect('/login/')

def Register(request):
    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            register = form.save()

            try:
                register.send_verification_email(request)
                messages.success(
                    request, 'A verification email has been sent to your email address.')
                return redirect('home')

                # Handle error (could log it, notify admins, or inform the user)
            except Exception as e:
                messages.error(
                    request, f'There was an error sending the verification email: {e}')

    context = {
        'form': form,
    }
    return render(request, 'account/register.html', context)


def custom_password_reset(request):
    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
       
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_link = request.build_absolute_uri(
                    reverse_lazy('password_reset_confirm', kwargs={
                        'uidb64': uid, 'token': token})
                )
                user_name = user.name
                user_email = user.email

                # Load the HTML email template
                html_message = render_to_string('account/password_reset_email.html', {'reset_link': reset_link, 'user_name': user_name, 'user_email': user_email})
                subject = 'Password Reset'
                from_email = 'no-reply@mhinnov8.com.ng'
                recipient_list = [email]

                # Sending the email with the custom template
                send_mail(subject, '', from_email, recipient_list, html_message=html_message)

                messages.success(request, 'A reset link has been sent to your email.')
                return redirect('login')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User details not found, please register.')
                return redirect('register')
    else:
        form = CustomPasswordResetForm()
   
    return render(request, 'account/password_reset.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except CustomUser.DoesNotExist:
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('login')
        else:
            form = CustomSetPasswordForm(user)
        return render(request, 'account/password_reset_confirm.html', {'form': form})


# @login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important, to update the session and keep the user authenticated
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Your password was successfully updated! Please Login Again')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'account/update_password.html', {'form': form})

@login_required
def cop_admin(request):
    event = COPEventApplication.objects.all()
    delegates = COPParticipant.objects.count()
    organisations = Organisation.objects.count()
    side_events = COPEventApplication.objects.filter(status='Approved').count()
    
    report = PostEventReport.objects.filter(event__isnull=False).order_by('-id')[:3]
    total_speakers = COPEventApplication.objects.filter(posteventreport__isnull=False).aggregate(Sum('number_of_speakers'))['number_of_speakers__sum'] or 0
    host = COPEventApplication.objects.filter(posteventreport__isnull=False).values('org').annotate(Count('org')).count()
    session = PostEventReport.objects.filter(event__isnull=False).count()
    
    total_duration = timedelta()
    for event in COPEventApplication.objects.filter(posteventreport__isnull=False):
        total_duration += event.end_time - event.start_time
    total_duration = total_duration.total_seconds() / 3600

    today = date.today()

    events_today = COPEventApplication.objects.filter(
        Q(start_time__date=today)
    )

    context = {
        'report': report,
        'session': session,
        'total_speakers': total_speakers,
        'total_duration': total_duration,
        'host': host,
        'delegates': delegates,
        'organisations': organisations,
        'side_events': side_events,
        'events_today': events_today,
    }

    return render(request, 'cop/dashboard.html', context)


@login_required
def org(request):
    members = Organisation.objects.all()

    mda = Organisation.objects.filter(organisation_type='GO/MDAs').count()
    ngo = Organisation.objects.filter(organisation_type='NGO/iNGO').count()
    private = Organisation.objects.filter(organisation_type='private').count()
    youth = Organisation.objects.filter(organisation_type='Women/YouthLead').count()

    context = {
        'members' : members,
        'mda': mda,
        'ngo': ngo,
        'youth': youth,
        'private': private
    }

    return render(request, 'cop/organisations.html', context)

@login_required
def org_prof(request, pk):
    member_id = get_object_or_404(Organisation, pk=pk)
    instance = Organisation.objects.get(pk=pk)

    if request.method == 'POST':
        form = StatusForm(request.POST, instance=instance)
        if form.is_valid():
            user = request.user
            form = form.save(commit=False)
            form.approved_by = user
            form.save()
            #url = reverse('org_prof', kwargs={'pk': member_id.pk})
            return redirect('organisations')
    else:
        form = StatusForm(instance=instance)
    context = {
        'member_id': member_id,
        'form': form,
        
    }

    return render(request, 'cop/org_profile.html', context)

@login_required
def accreditation(request):
    delegates = COPParticipant.objects.all()
    nccc = COPParticipant.objects.filter(accredited_by='NCCC').count()
    val = COPParticipant.objects.count()
    others = val - nccc

    form = DelegateForm(request.POST)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']  # Get the email from the form

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # User with the provided email doesn't exist, create a new user
            name = form.cleaned_data['name']
            password = "Nccc@COP28"
            role= "Activist"
            user = CustomUser.objects.create_user(email=email, password=password, name=name, role=role)
            user.send_verification_email(request)

        form.instance.user = user  # Assign the user to the form
        form.save()
        return redirect('accreditation')
        
    context = {
        'delegates': delegates,
        'nccc': nccc,
        'others': others,
        'form': form
    }

    return render(request, 'cop/accreditation.html', context)

@login_required
def side_event(request):
    events = COPEventApplication.objects.all()
    application = COPEventApplication.objects.count()
    approve = COPEventApplication.objects.filter(status='Approved').count()
    hosted = PostEventReport.objects.count()

    form = EventForm()
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('side_event')
    
    else:
        form = EventForm()

    context = {
        'events': events,
        'form': form,
        'application': application,
        'approve': approve,
        'hosted': hosted,
    }

    return render(request, 'cop/side_event.html', context)



@login_required
def event_profile(request, pk):
    event_id = get_object_or_404(COPEventApplication, pk=pk)
    event = event_id.id
    report = PostEventReport.objects.filter(event_id=event)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event_id)
        form2 = ReportForm(request.POST)
        form3 = InvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            url = reverse('event', kwargs={'pk': event_id.pk})
            return redirect(url)
        elif form2.is_valid():
            report_form, created = PostEventReport.objects.get_or_create(event_id=event_id.id, defaults=form2.cleaned_data)
            if not created:
                report_form.__dict__.update(form2.cleaned_data)
                report_form.save()
            url = reverse('event', kwargs={'pk': event_id.pk})
            messages.success(request, "Event has been successfully reported!")
            return redirect(url)
        if form3.is_valid():
            form3 = form3.save(commit=False)
            form3.application_id = event_id.id
            form3.save()
            url = reverse('event', kwargs={'pk': event_id.pk})
            return redirect(url)

    else:
        form = EventForm(instance=event_id)
        form2 = ReportForm()
        form3 = InvoiceForm()
    
    context = {
        'event_id': event_id,
        'form': form,
        'form2': form2,
        'form3': form3,
        'report': report.last(),
    }

    return render(request, 'cop/event_profile.html', context)

@login_required
def announcement(request):
    users = CustomUser.objects.all()
    email_list = [user.email for user in users]

    announcement = COPEventAnnouncement.objects.all()

    form = AnnouncementForm()
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            #sender = form.cleaned_data['sender']

            from_email = 'no-reply@mhinnov8.com.ng'
            recipient_list = email_list
            send_mail(subject, message, from_email,  recipient_list)

            form.save()
            return redirect('announcement')
    else:
        form = AnnouncementForm()

    context = {
        'form': form,
        'announcement': announcement,
    }

    return render(request, 'cop/announcement.html', context)


def event_list(request):
    today = date.today()

    # Filter events with a start_time in the future
    event_list = COPEventApplication.objects.filter(start_time__date__gte=today)

    # Sort events by start_time
    event_list = event_list.order_by('start_time')

    context = {
        'event_list': event_list,
    }

    return render(request, 'event_list.html', context)

def event_view(request, pk):
    event_id = get_object_or_404(COPEventApplication, pk=pk)
    
    context = {
        'event_id': event_id,
    }
    return render(request, 'event.html', context)

def report_list(request):
    report_list = PostEventReport.objects.order_by('-date_created')

    context = {
        'report_list': report_list
    }
    return render(request, 'report_list.html', context)

def report_view(request, pk):
    report_id = get_object_or_404(PostEventReport, pk=pk)
    
    context = {
        'report_id': report_id,
    }
    return render(request, 'report.html', context)

@login_required
def org_dashboard(request):
    user = request.user

    try:
        org = Organisation.objects.get(user=user)
    except Organisation.DoesNotExist:
        org = None

    approve = 0

    if org:
        events = COPEventApplication.objects.filter(org=org)
        approve = events.filter(status='Approved').count()
        hosted = PostEventReport.objects.filter(event__in=events, event__isnull=False).count()
        report = PostEventReport.objects.filter(event__in=events, event__isnull=False).order_by('-id')[:3]
        total_speakers = events.filter(posteventreport__isnull=False).aggregate(Sum('number_of_speakers'))['number_of_speakers__sum'] or 0
        host = 1
        session = PostEventReport.objects.filter(event__in=events, event__isnull=False).count()
        
        total_duration = timedelta()
        for event in COPEventApplication.objects.filter(posteventreport__isnull=False):
            total_duration += event.end_time - event.start_time
        total_duration = total_duration.total_seconds() / 3600
        total_duration = int(total_duration)

        today = date.today()

        events_today = COPEventApplication.objects.filter(
            Q(start_time__date=today)
        )
    else:
        hosted = 0

    context = {
        'approve': approve,
        'hosted': hosted,
        'report': report,
        'session': session,
        'total_speakers': total_speakers,
        'total_duration': total_duration,
        'host': host,
        'events_today': events,
    }


    return render(request, 'organisation/dashboard.html', context)

@login_required
def org_register(request):
    user = request.user  # Get the current user
    if request.method == 'POST':
        form = OrganisationForm(request.POST, request.FILES)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.user = user
            form_instance.save()
            return redirect('org_dashbord')
    else:
        form = OrganisationForm()

    context = {
        'form': form,
    }

    return render(request, 'organisation/register.html', context)

@login_required
def org_update(request):
    user = request.user  # Get the current user
    member_id = Organisation.objects.get(user=user)

    try:
        existing_data = Organisation.objects.get(user=user)
    except Organisation.DoesNotExist:
        existing_data = None

    if request.method == 'POST':
        form = OrganisationForm(request.POST, request.FILES)

        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.user = user  # Set the user
            form_instance.id = existing_data.id 
            form_instance.date_created = existing_data.date_created
            form_instance.save()
            return redirect('org_update')
    else:
        form = OrganisationForm(instance=existing_data)  # Populate the form with existing data
    context = {
        'form': form,
        'member_id': member_id,
    }

    return render(request, 'organisation/profile.html', context)

@login_required
def org_event(request):
    user = request.user

    try:
        org = Organisation.objects.get(user=user)
    except Organisation.DoesNotExist:
        org = None

    application = 0
    approve = 0

    if org:
        events = COPEventApplication.objects.filter(org=org)
        application = events.count()
        approve = events.filter(status='Approved').count()
        hosted = PostEventReport.objects.filter(event__in=events).count()
    else:
        hosted = 0

    form = OrgEventForm()
    
    if request.method == 'POST':
        form = OrgEventForm(request.POST, request.FILES)
        if form.is_valid():
            form = form.save(commit=False)
            form.org = org
            form.save()
            return redirect('org_event')
    
    else:
        form = OrgEventForm()

    context = {
        'events': events,
        'form': form,
        'application': application,
        'approve': approve,
        'hosted': hosted,
    }

    return render(request, 'organisation/side_event.html', context)

@login_required
def org_event_profile(request, pk):
    event_id = get_object_or_404(COPEventApplication, pk=pk)
    try:
        invoice = Invoice.objects.get(application_id=event_id)
    except Invoice.DoesNotExist:
        invoice = None

    if request.method == 'POST':
        form = OrgEventForm(request.POST, request.FILES, instance=event_id)
        form2 = PaidForm(request.POST, request.FILES, instance=invoice)
        
        if form.is_valid():
            form.save()
            url = reverse('org_event_profile', kwargs={'pk': event_id.pk})
            return redirect(url)
        elif form2.is_valid():
            form2.save()
            url = reverse('org_event_profile', kwargs={'pk': event_id.pk})
            return redirect(url)
    else:
        form = OrgEventForm(instance=event_id)
        # Get the associated invoice
        try:
            invoice = Invoice.objects.get(application_id=event_id)
        except Invoice.DoesNotExist:
            invoice = None

        form2 = PaidForm(instance=invoice)
    
    context = {
        'event_id': event_id,
        'form': form,
        'form2': form2,
        'invoice': invoice,
    }

    return render(request, 'organisation/event_profile.html', context)

@login_required
def activist_dashboard(request):

    context = {

    }

    return render(request, 'activist/dashboard.html', context)