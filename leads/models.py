from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail


class User(AbstractUser):
    is_organisor = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.user.username


class Lead(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    age = models.IntegerField(default=1)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    agent = models.ForeignKey("Agent", null=True, blank=True,  on_delete=models.SET_NULL)
    category = models.ForeignKey("Category" , related_name="leads", null=True, blank=True , on_delete=models.SET_NULL)
    description = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=10)
    email = models.EmailField()
    is_converted = models.BooleanField(default=False)

    @staticmethod
    @receiver(post_save, sender='leads.Lead')
    def send_lead_created_email(sender, instance, created, **kwargs):
        if created:
            subject = 'WELCOME! {} '.format(instance.first_name)
            message = 'Dear {},\n\nWelcome to our family! Thank you for your interest. As a special token of our appreciation, enjoy a 15% discount on your first order with the coupon code WELCOME15. We look forward to serving you!\n\nBest regards,\n'.format(instance.first_name)
            from_email = 'navadkarsoham191@gmail.com'
            recipient_list = [instance.email]

            send_mail(subject, message, from_email, recipient_list)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"   

    
class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.email}"  



class Category(models.Model):
    name = models.CharField(max_length=30) #new , Contacted , Converted, Unconverted
    organisation = models.ForeignKey(UserProfile , on_delete=models.CASCADE)

    def __str__(self):
        return self.name


def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(post_user_created_signal, sender=User)