from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Team Name")
    logo_path = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="City / Club")
    division = models.CharField(max_length=50, choices=[
        ('pro_men', "Pro Men's"),
        ('pro_women', "Pro Women's"),
        ('amateur', "Amateur / Mixed")
    ], default='pro_men')
    group_name = models.CharField(max_length=10, blank=True, null=True)
    
    cap_name = models.CharField(max_length=50, verbose_name="Captain Name")
    cap_surname = models.CharField(max_length=50, verbose_name="Captain Surname")
    cap_email = models.EmailField(max_length=100, unique=True)
    cap_phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    PAYMENT_STATUS_CHOICES = [
        (0, 'Waiting'),
        (1, 'Accepted'),
        (2, 'Refund'),
    ]
    payment_status = models.IntegerField(choices=PAYMENT_STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Teams'
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def __str__(self):
        return f"{self.name} ({self.get_payment_status_display()})"

class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    jersey_number = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'Players'
