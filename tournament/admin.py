from django.contrib import admin
from .models import Team, Player

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'league_level', 'city', 'cap_name', 'cap_surname', 'payment_status', 'blik_number', 'group_name', 'created_at')
    list_filter = ('league_level', 'payment_status', 'created_at', 'group_name')
    search_fields = ('name', 'cap_name', 'cap_surname', 'cap_email', 'cap_phone', 'city', 'instagram')
    inlines = [PlayerInline]
    actions = ['mark_as_accepted', 'mark_as_waiting']
    
    fieldsets = (
        ('Team Details', {
            'fields': ('name', 'city', 'league_level', 'logo_path', 'instagram', 'group_name')
        }),
        ('Captain Contact', {
            'fields': ('cap_name', 'cap_surname', 'cap_dob', 'cap_jersey', 'cap_email', 'cap_phone')
        }),
        ('Payment & Status', {
            'fields': ('payment_status', 'blik_number')
        }),
    )

    def mark_as_accepted(self, request, queryset):
        queryset.update(payment_status=1)
    mark_as_accepted.short_description = "Mark selected teams as Accepted"

    def mark_as_waiting(self, request, queryset):
        queryset.update(payment_status=0)
    mark_as_waiting.short_description = "Mark selected teams as Waiting"

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'team', 'jersey_number', 'date_of_birth')
    search_fields = ('first_name', 'last_name', 'team__name')
    list_filter = ('team__league_level', 'team')

from .models import Sector, Match, GameSet, MatchEvent

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('name',)

class GameSetInline(admin.TabularInline):
    model = GameSet
    extra = 0

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'start_time', 'sector')
    list_filter = ('status', 'sector')
    search_fields = ('team_a__name', 'team_b__name')
    inlines = [GameSetInline]

@admin.register(GameSet)
class GameSetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'match', 'score_a', 'score_b', 'is_completed')
    list_filter = ('is_completed', 'match')

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'match', 'game_set', 'team', 'category', 'result', 'timestamp')
    list_filter = ('match', 'category', 'result')
    search_fields = ('player__first_name', 'player__last_name', 'affected_player__first_name', 'affected_player__last_name')
