from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    Team, Player, Match, GameSet, PlayerMatchStats,
    TeamMatchStats, GroupStanding, DreamTeamEntry,
    MVPSelection, MatchHighlight, GalleryPhoto, GalleryVideo,
    ScheduleEvent,
)
from .services import preview_csv_import, confirm_csv_import


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    fields = ('first_name', 'last_name', 'jersey_number', 'position', 'photo_path')


class GameSetInline(admin.TabularInline):
    model = GameSet
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'league_level', 'status', 'checked_in', 'cap_name', 'cap_surname', 'payment_status', 'blik_number', 'group_name', 'created_at')
    list_filter = ('league_level', 'payment_status', 'status', 'checked_in', 'created_at', 'group_name')
    search_fields = ('name', 'cap_name', 'cap_surname', 'cap_email', 'cap_phone')
    inlines = [PlayerInline]
    actions = ['mark_as_accepted', 'mark_as_waiting']
    
    fieldsets = (
        ('Team Details', {
            'fields': ('name', 'league_level', 'logo_path', 'group_name')
        }),
        ('Captain Contact', {
            'fields': ('cap_name', 'cap_surname', 'cap_email', 'cap_phone')
        }),
        ('Payment & Status', {
            'fields': ('payment_status', 'blik_number', 'status', 'checked_in')
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
    list_display = ('first_name', 'last_name', 'team', 'jersey_number', 'position', 'photo_preview')
    search_fields = ('first_name', 'last_name', 'team__name')
    list_filter = ('team__league_level', 'team')

    @admin.display(description="Photo")
    def photo_preview(self, obj):
        if obj.photo_path:
            return format_html('<img src="/static/{}" style="height:32px;border-radius:50%">', obj.photo_path)
        return "-"


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'match_number', 'stage', 'team_a', 'placeholder_a',
        'team_b', 'placeholder_b',
        'score_a', 'score_b', 'status', 'court',
        'start_time', 'stats_imported',
    )
    list_filter = ('stage', 'status', 'court', 'stats_imported')
    search_fields = ('team_a__name', 'team_b__name', 'placeholder_a', 'placeholder_b')
    readonly_fields = ('stats_imported_at',)
    inlines = [GameSetInline]
    actions = ['import_csv_stats']

    def import_csv_stats(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Select exactly one match.", level="error")
            return
        match = queryset.first()
        return HttpResponseRedirect(
            reverse("admin:tournament_match_csv_import", args=[match.pk])
        )
    import_csv_stats.short_description = "Import CSV stats for selected match"

    def get_urls(self):
        custom_urls = [
            path(
                "<int:match_id>/csv-import/",
                self.admin_site.admin_view(self.match_csv_import_view),
                name="tournament_match_csv_import",
            ),
        ]
        return custom_urls + super().get_urls()

    def match_csv_import_view(self, request, match_id):
        match = get_object_or_404(Match, pk=match_id)
        context = {
            **self.admin_site.each_context(request),
            "match": match,
            "errors": [],
            "warnings": [],
            "preview_rows": None,
            "imported_count": None,
        }

        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            if not csv_file:
                context["errors"] = ["No file uploaded."]
                return render(request, "tournament/admin/csv_import.html", context)

            action = request.POST.get("action", "preview")

            if action == "preview":
                result = preview_csv_import(csv_file, match_id)
                context["errors"] = result["errors"]
                context["warnings"] = result["warnings"]
                context["preview_rows"] = result["preview"] if result["can_import"] else None

            elif action == "confirm":
                try:
                    result = confirm_csv_import(csv_file, match_id)
                    context["imported_count"] = result["imported"]
                    context["warnings"] = result["warnings"]
                except ValueError as exc:
                    context["errors"] = [str(exc)]

        return render(request, "tournament/admin/csv_import.html", context)


@admin.register(PlayerMatchStats)
class PlayerMatchStatsAdmin(admin.ModelAdmin):
    list_display = (
        'player', 'team', 'match', 'position',
        'kills', 'aces', 'blocks', 'display_points_won',
    )
    list_filter = ('match', 'team', 'position')
    search_fields = ('player__first_name', 'player__last_name')

    @admin.display(description="Points Won")
    def display_points_won(self, obj):
        return obj.points_won


@admin.register(TeamMatchStats)
class TeamMatchStatsAdmin(admin.ModelAdmin):
    list_display = ('team', 'match', 'kills', 'aces', 'blocks')
    list_filter = ('match',)


@admin.register(GroupStanding)
class GroupStandingAdmin(admin.ModelAdmin):
    list_display = (
        'team', 'group', 'played', 'wins', 'losses',
        'sets_won', 'sets_lost', 'points', 'rank_in_group',
    )
    list_filter = ('group',)


@admin.register(DreamTeamEntry)
class DreamTeamEntryAdmin(admin.ModelAdmin):
    list_display = ('position', 'slot', 'player', 'team', 'metric_label', 'is_auto')


@admin.register(MVPSelection)
class MVPSelectionAdmin(admin.ModelAdmin):
    list_display = ('mvp_type', 'player', 'team', 'match', 'is_auto')
    list_filter = ('mvp_type', 'is_auto')


@admin.register(MatchHighlight)
class MatchHighlightAdmin(admin.ModelAdmin):
    list_display = ('title', 'match', 'order')
    list_editable = ('order',)


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'drive_file_id', 'order')
    list_editable = ('order',)
    search_fields = ('title',)


@admin.register(GalleryVideo)
class GalleryVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'drive_file_id', 'order')
    list_editable = ('order',)
    search_fields = ('title',)


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'title', 'start_time', 'end_time')
    list_filter = ('event_type',)
    search_fields = ('title',)
