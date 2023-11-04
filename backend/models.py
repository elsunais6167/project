from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.mail import send_mail
from django.forms import ValidationError
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from .tokens import account_activation_token
from django.utils.translation import gettext_lazy as _
from embed_video.fields import EmbedVideoField

def validate_image_size(value):
    file_size = value.size
    max_size = 2 * 1024 * 1024  # 2 MB (you can adjust this as needed)

    if file_size > max_size:
        raise ValidationError(_("The uploaded image is too large. The maximum file size is 2MB."))
        
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('Super Admin', 'Super Admin'),
        ('Admin', 'Admin'),
        ('Organisation', 'Organisation'),
        ('Activist', 'Activist'),
    ]
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30, blank=True)
    role = models.CharField(choices=ROLE_CHOICES, max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def send_verification_email(self, request):
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = account_activation_token.make_token(self)

        mail_subject = 'Activate your account'
        message = render_to_string('account/verify.html', {
            'user': self,
            'domain': request.get_host(),
            'uid': uid,
            'token': token,
        })

        send_mail(mail_subject, message, 'no-reply@mhinnov8.com.ng', [self.email], html_message=message)

    def __str__(self):
        return self.email

class Profile(models.Model):
    ROLE_CHOICES = [
        ('event', 'Event Manager'),
        ('cop', 'COP Desk Officer'),
        ('registrar', 'Registrar'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    designation = models.CharField(max_length=200)
    role = models.CharField(choices=ROLE_CHOICES, max_length=50)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name

class Organisation(models.Model):
    ORG_TYPE_CHOICES = [
        ('GO/MDAs', 'GO/MDAs'),
        ('NGO/iNGO', 'NGO/iNGO'),
        ('Women/YouthLead', 'Women/YouthLead'),
        ('Private', 'Private'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Decline', 'Decline'),
        ('Approved', 'Approved'),
    ]
    FOCUS = [
    ('Agriculture', 'Agriculture'),
    ('Clean Energy', 'Clean Energy'),
    ('Climate Finance', 'Climate Finance'),
    ('Transportation', 'Transportation'),
    ('Afforestation', 'Afforestation'),
    ('Media/Journalism', 'Media/Journalism'),
    ('Renewable Energy', 'Renewable Energy'),
    ('Environmental Policy', 'Environmental Policy'),
    ('Sustainable Urban Development', 'Sustainable Urban Development'),
    ('Biodiversity Conservation', 'Biodiversity Conservation'),
    ('Climate Adaptation', 'Climate Adaptation'),
    ('Ocean Conservation', 'Ocean Conservation'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='organisation_user')
    organisation_type = models.CharField(choices=ORG_TYPE_CHOICES, max_length=50)
    contact_number = models.IntegerField()
    address_line = models.CharField(max_length=250)
    STATES = [
    ('Abia', 'Abia'),
    ('Adamawa', 'Adamawa'),
    ('Akwa Ibom', 'Akwa Ibom'),
    ('Anambra', 'Anambra'),
    ('Bauchi', 'Bauchi'),
    ('Bayelsa', 'Bayelsa'),
    ('Benue', 'Benue'),
    ('Borno', 'Borno'),
    ('Cross River', 'Cross River'),
    ('Delta', 'Delta'),
    ('Ebonyi', 'Ebonyi'),
    ('Edo', 'Edo'),
    ('Ekiti', 'Ekiti'),
    ('Enugu', 'Enugu'),
    ('F.C.T', 'F.C.T'),
    ('Gombe', 'Gombe'),
    ('Imo', 'Imo'),
    ('Jigawa', 'Jigawa'),
    ('Kaduna', 'Kaduna'),
    ('Kano', 'Kano'),
    ('Katsina', 'Katsina'),
    ('Kebbi', 'Kebbi'),
    ('Kogi', 'Kogi'),
    ('Kwara', 'Kwara'),
    ('Lagos', 'Lagos'),
    ('Nasarawa', 'Nasarawa'),
    ('Niger', 'Niger'),
    ('Ogun', 'Ogun'),
    ('Ondo', 'Ondo'),
    ('Osun', 'Osun'),
    ('Oyo', 'Oyo'),
    ('Plateau', 'Plateau'),
    ('Rivers', 'Rivers'),
    ('Sokoto', 'Sokoto'),
    ('Taraba', 'Taraba'),
    ('Yobe', 'Yobe'),
    ('Zamfara', 'Zamfara'),
    ]
    state = models.CharField(max_length=50, choices=STATES)
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    focus_area = models.CharField(max_length=50, choices=FOCUS, null=True) 
    description = models.TextField(max_length=2500)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, validators=[validate_image_size])
    certificate = models.FileField(upload_to='certificates/', blank=True, null=True, validators=[validate_image_size])
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='Pending')
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name='approval_officer')
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name

class Activist(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Decline', 'Decline'),
        ('Approved', 'Approved'),
    ]

    FOCUS = [
    ('Agriculture', 'Agriculture'),
    ('Clean Energy', 'Clean Energy'),
    ('Climate Finance', 'Climate Finance'),
    ('Transportation', 'Transportation'),
    ('Afforestation', 'Afforestation'),
    ('Media/Journalism', 'Media/Journalism'),
    ('Renewable Energy', 'Renewable Energy'),
    ('Environmental Policy', 'Environmental Policy'),
    ('Sustainable Urban Development', 'Sustainable Urban Development'),
    ('Biodiversity Conservation', 'Biodiversity Conservation'),
    ('Climate Adaptation', 'Climate Adaptation'),
    ('Ocean Conservation', 'Ocean Conservation'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='activist_user')
    organisation = models.ForeignKey(Organisation, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=200)
    contact_number = models.IntegerField()
    email = models.EmailField(unique=True)
    address_line = models.CharField(max_length=250)
    
    STATES = [
    ('Abia', 'Abia'),
    ('Adamawa', 'Adamawa'),
    ('Akwa Ibom', 'Akwa Ibom'),
    ('Anambra', 'Anambra'),
    ('Bauchi', 'Bauchi'),
    ('Bayelsa', 'Bayelsa'),
    ('Benue', 'Benue'),
    ('Borno', 'Borno'),
    ('Cross River', 'Cross River'),
    ('Delta', 'Delta'),
    ('Ebonyi', 'Ebonyi'),
    ('Edo', 'Edo'),
    ('Ekiti', 'Ekiti'),
    ('Enugu', 'Enugu'),
    ('F.C.T', 'F.C.T'),
    ('Gombe', 'Gombe'),
    ('Imo', 'Imo'),
    ('Jigawa', 'Jigawa'),
    ('Kaduna', 'Kaduna'),
    ('Kano', 'Kano'),
    ('Katsina', 'Katsina'),
    ('Kebbi', 'Kebbi'),
    ('Kogi', 'Kogi'),
    ('Kwara', 'Kwara'),
    ('Lagos', 'Lagos'),
    ('Nasarawa', 'Nasarawa'),
    ('Niger', 'Niger'),
    ('Ogun', 'Ogun'),
    ('Ondo', 'Ondo'),
    ('Osun', 'Osun'),
    ('Oyo', 'Oyo'),
    ('Plateau', 'Plateau'),
    ('Rivers', 'Rivers'),
    ('Sokoto', 'Sokoto'),
    ('Taraba', 'Taraba'),
    ('Yobe', 'Yobe'),
    ('Zamfara', 'Zamfara'),
    ]
    state = models.CharField(max_length=50, choices=STATES)
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    focus_area = models.CharField(max_length=50, choices=FOCUS) 
    description = models.TextField(max_length=2500)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, blank=True, null=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='approved_org')
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.name

class Event(models.Model):
    TYPE_CHOICES = [
        ('Tree Planting', 'Tree Planting'),
        ('Sensitization', 'Sensitization'),
        ('Stakeholders Engagement', 'Stakeholders Engagement'),
        ('Research', 'Research'),
        ('Summit', 'Summit'),
        ('Others', 'Others'),
    ]
    name = models.CharField(max_length=200)
    event_type = models.CharField(choices=TYPE_CHOICES, max_length=50)
    others_description = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(max_length=2500)
    date = models.DateTimeField()
    address_line = models.CharField(max_length=250)
    lga = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    ENG_CHOICES = [
        ('Partner', 'Partner'),
        ('Participant', 'Participant'),
        ('Organiser', 'Organiser'),
        ('Sponsor', 'Sponsor'),
    ]
    engagement_type = models.CharField(choices=ENG_CHOICES, max_length=50)
    video = models.URLField(blank=True, null=True) 
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EventVideo(models.Model):
    video_url = models.URLField()
    event = models.ForeignKey('Event', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.event.name

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(max_length=2500)
    image = models.ImageField(upload_to='announcement_images/', blank=True, validators=[validate_image_size])
    video = EmbedVideoField(blank=True, null=True)
    posted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class AnnouncementImage(models.Model):
    image = models.ImageField(upload_to='announcement_images/', blank=True, null=True)
    announcement = models.ForeignKey('Announcement', on_delete=models.CASCADE)

    def __str__(self):
        return self.announcement.title

class COPParticipant(models.Model):
    ACCREDITATION_CHOICES = [
        ('Party', 'Party'),
        ('Party Overflow', 'Party Overflow'),
        ('Observer', 'Observer'),
        ('Media/Journalist', 'Media/Journalist'),
        ('Volunteer', 'Volunteer')
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='participant_user', blank=True)
    accreditation_type = models.CharField(choices=ACCREDITATION_CHOICES, max_length=50)
    accreditation_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    organization = models.ForeignKey(Organisation, on_delete=models.CASCADE, null=True, blank=True)
    not_listed = models.CharField(max_length=250, null=True, blank=True)
    accredited_by = models.CharField(max_length=500, default='NCCC')
    cop_year = models.DateField(auto_now_add=True)

    def send_verification(self, request):
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = account_activation_token.make_token(self)

        mail_subject = 'Activate your Account'
        message = render_to_string('account/verify2.html', {
            'user': self,
            'domain': request.get_host(),
            'uid': uid,
            'token': token,
        })

        send_mail(mail_subject, message, 'no-reply@mhinnov8.com.ng', [self.email])

    def __str__(self):
        return self.name

class COPEventApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Declined', 'Declined')
    ]
    org = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    proposed_title = models.CharField(max_length=200)
    type = [
        ('Panels', 'Panels'),
        ('Presentations', 'Presentations'),
        ('Panel/Presentations', 'Panel/Presentations')
    ]
    event_type = models.CharField(max_length=50, choices=type, null=True)
    number_of_speakers = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='Pending')
    description = models.TextField(max_length=5000, blank=True, null=True)
    flier = models.ImageField(upload_to='fliers/', blank=True, null=True, validators=[validate_image_size])
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.proposed_title
    
    @property
    def Duration(self):
        start = self.start_time
        end = self.end_time
        time = end - start

        return time

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue')
    ]
    application = models.ForeignKey(COPEventApplication, on_delete=models.CASCADE)
    CURRENCY_CHOICES = [
        ('NGN', 'NGN'),
        ('USD', 'USD'),
        ('AED', 'AED'),
    ]
    currency = models.CharField(choices=CURRENCY_CHOICES, max_length=20)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date_paid = models.DateTimeField(blank=True, null=True)
    payment_status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='Unpaid')
    proof = models.ImageField(upload_to='reciepts/', blank=True, null=True, validators=[validate_image_size])
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.application.proposed_title


class COPEventAnnouncement(models.Model):
    subject = models.CharField(max_length=500)
    message = models.TextField()
    sender = models.CharField(max_length=50)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject
    
    
class PostEventReport(models.Model):
    event = models.ForeignKey(COPEventApplication, on_delete=models.CASCADE)
    description = models.TextField(max_length=5000, null=True)
    image_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    date_created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.event.proposed_title
