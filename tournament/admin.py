from django.contrib import admin
from .models import Team, Player

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'division', 'city', 'cap_name', 'payment_status', 'created_at')
    list_filter = ('division', 'payment_status', 'created_at')
    search_fields = ('name', 'cap_name', 'cap_email', 'city')
    inlines = [PlayerInline]
    actions = ['mark_as_accepted', 'mark_as_waiting']

    def mark_as_accepted(self, request, queryset):
        queryset.update(payment_status=1)
    mark_as_accepted.short_description = "Mark selected teams as Accepted"

    def mark_as_waiting(self, request, queryset):
        queryset.update(payment_status=0)
    mark_as_waiting.short_description = "Mark selected teams as Waiting"

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'team', 'jersey_number')
    search_fields = ('first_name', 'last_name', 'team__name')
    list_filter = ('team__division',)
