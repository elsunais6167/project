from django import forms
from django.forms import ModelForm, ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm


from .models import *

class DateLocal(forms.DateTimeInput):
    input_type = 'datetime-local'

class RegisterForm(UserCreationForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Password'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm Password'
    )

    # Define your custom choices for the 'role' field
    CUSTOM_ROLE_CHOICES = [
        ('Organisation', 'Organisation'),
        ('Activist', 'Activist'),
    ]

    role = forms.ChoiceField(
        choices=CUSTOM_ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Register as an'
    )

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'role', 'password1', 'password2']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class CustomPasswordResetForm(DjangoPasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter your email'}
        )
    )

class CustomSetPasswordForm(DjangoSetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'New password'}
        ),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}
        ),
        label='Confirm Password'
    )

class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Old password'}
        ),
        label='Old Password'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'New password'}
        ),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}
        ),
        label='Confirm Password'
    )

class OrganisationForm(ModelForm):
    class Meta:
        model = Organisation
        fields = ['logo', 'organisation_type', 'contact_number', 'address_line',
                  'state', 'focus_area', 'description', 'twitter', 'facebook', 'instagram', 'website',
                  'certificate']
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class':'form-control'}),
            'organisation_type': forms.Select(attrs={'class': 'form-control'}),
            'contact_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'address_line': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'focus_area': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'certificate': forms.ClearableFileInput(attrs={'class':'form-control'}), 
        }
        labels = {
            'certificate': 'Your CAC Certificate or Letter of Request for (GOs/MDAs)'
        }

class StatusForm(ModelForm):
    class Meta:
        model = Organisation
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class DelegateForm(ModelForm):
    class Meta:
        model = COPParticipant
        fields = ['accreditation_type', 'accreditation_number', 'name', 'email',
                  'organization', 'not_listed']
        widgets = {
            'accreditation_type': forms.Select(attrs={'class': 'form-control'}),
            'accreditation_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}  ),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'not_listed': forms.TextInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'not_listed': 'Organisation, if not listed above',
        }

class EventForm(ModelForm):
    class Meta:
        model = COPEventApplication
        fields = ['org', 'proposed_title', 'event_type', 'number_of_speakers', 'start_time',
                  'end_time', 'status', 'description', 'flier']
        widgets = {
            'org': forms.Select(attrs={'class': 'form-control'}),
            'proposed_title': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_speakers': forms.NumberInput(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'start_time': DateLocal(attrs={'class': 'form-control'}),
            'end_time': DateLocal(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description':forms.Textarea(attrs={'class':'form-control'}),
            'flier': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }

        labels = {
            'org' : 'Organisation',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        instance = self.instance  # Assuming this is an update operation

        if start_time and end_time:
            # Check for existing events that overlap with the new event
            existing_events = COPEventApplication.objects.filter(
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            # If this is an update and the time remains the same, allow it
            if instance and instance.start_time == start_time and instance.end_time == end_time:
                return cleaned_data

            if existing_events.exists():
                raise ValidationError("This event overlaps with an existing event. Please change another time")

        return cleaned_data

class ReportForm(ModelForm):
    class Meta:
        model = PostEventReport
        fields = ['description', 'image_url', 'video_url']
        widgets = {
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'description':forms.Textarea(attrs={'class':'form-control'}),
            #'flier': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }

class AnnouncementForm(ModelForm):
    class Meta:
        model = COPEventAnnouncement
        fields = ['subject', 'message', 'sender']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'sender': forms.TextInput(attrs={'class': 'form-control'}),
            'message':forms.Textarea(attrs={'class':'form-control'}),
            #'flier': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }

class OrgEventForm(ModelForm):
    class Meta:
        model = COPEventApplication
        fields = ['proposed_title', 'event_type', 'number_of_speakers', 'start_time',
                  'end_time', 'description', 'flier']
        widgets = {
            'proposed_title': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_speakers': forms.NumberInput(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'start_time': DateLocal(attrs={'class': 'form-control'}),
            'end_time': DateLocal(attrs={'class': 'form-control'}),
            'description':forms.Textarea(attrs={'class':'form-control'}),
            'flier': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }

        labels = {
            'org' : 'Organisation',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        instance = self.instance  # Assuming this is an update operation

        if start_time and end_time:
            # Check for existing events that overlap with the new event
            existing_events = COPEventApplication.objects.filter(
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            # If this is an update and the time remains the same, allow it
            if instance and instance.start_time == start_time and instance.end_time == end_time:
                return cleaned_data

            if existing_events.exists():
                raise ValidationError("This event overlaps with an existing event. Please change another time")

        return cleaned_data

class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice
        fields = ['currency', 'amount_due',]
        widgets = {
            'amount_due': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
        }

        labels = {
                    'amount_due' : 'Price of the Event',
                    'currency' : 'Type of Currency',
                }

class PaidForm(ModelForm):
    class Meta:
        model = Invoice
        fields = ['amount_paid', 'date_paid', 'proof']
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_paid': DateLocal(attrs={'class': 'form-control'}),
            'proof': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }

        labels = {
            'proof' : 'Upload a Scanned Proof of Payment. Only PGN/JPG',
        }

class ComfirmForm(forms.Form):
    status = forms.CharField(widget=forms.Select(attrs={'class': 'form-control'}))
    payment_status = forms.CharField(widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, invoice_instance, *args, **kwargs):
        super(ComfirmForm, self).__init__(*args, **kwargs)
        self.fields['status'].initial = invoice_instance.status
        self.fields['payment_status'].initial = invoice_instance.payment_status

    def save(self, invoice_instance):
        invoice_instance.status = self.cleaned_data['status']
        invoice_instance.payment_status = self.cleaned_data['payment_status']
        invoice_instance.save()