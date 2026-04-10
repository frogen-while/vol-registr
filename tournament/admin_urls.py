from django.urls import path

from .panel.audit_views import audit_view, cmd_search
from .panel.auth_views import panel_login, panel_logout
from .panel.checkin_views import checkin_search, checkin_toggle, checkin_view
from .panel.dashboard_views import dashboard_view

from .panel.rankings_views import rankings_recalculate_view, rankings_view
from .panel.match_views import (
    event_create_view,
    event_delete_view,
    event_edit_view,
    match_conflict_check,
    match_create_view,
    match_delete_view,
    match_detail_view,
    match_edit_view,
    match_panel_view,
    match_score_update,
    match_sets_inline_update,
    match_status_change,
    schedule_csv_import_view,
    schedule_list_view,
)

from .panel.media_views import (
    gallery_add_view,
    gallery_bulk_add_view,
    gallery_bulk_link_view,
    gallery_delete_view,
    gallery_list_view,
    gallery_photo_edit_view,
    gallery_reorder_view,
    gallery_state_change_view,
    gallery_upload_view,
    video_add_view,
    video_bulk_link_view,
    video_delete_view,
    video_edit_view,
    video_reorder_view,
    video_upload_view,
)
from .panel.stats_views import (
    stats_detail_view,
    stats_edit_view,
    stats_import_view,
    stats_list_view,
    stats_manual_create_view,
)
from .panel.team_views import (
    generate_roster_code,
    team_batch_action,
    team_create_view,
    team_delete_view,
    team_detail_view,
    team_drawer_view,
    team_edit_view,
    team_pipeline_move,
    team_status_action,
    teams_list_view,
    teams_pipeline_view,
)
from .panel.player_views import (
    player_create_view,
    player_delete_view,
    player_detail_view,
    player_edit_view,
    players_list_view,
)
from .panel.export_views import (
    export_player_stats_csv,
    export_results_csv,
    export_standings_csv,
)
from .panel.backup_views import (
    db_backup_create,
    db_backup_delete,
    db_backup_download,
    db_backup_view,
    db_download_current,
    db_restore,
)

app_name = "panel"

urlpatterns = [
    path("login/", panel_login, name="login"),
    path("logout/", panel_logout, name="logout"),
    path("", dashboard_view, name="dashboard"),
    path("teams/", teams_list_view, name="teams"),
    path("teams/pipeline/", teams_pipeline_view, name="teams_pipeline"),
    path("teams/create/", team_create_view, name="team_create"),
    path("teams/<int:pk>/", team_detail_view, name="team_detail"),
    path("teams/<int:pk>/edit/", team_edit_view, name="team_edit"),
    path("teams/<int:pk>/delete/", team_delete_view, name="team_delete"),
    path("teams/<int:pk>/status/", team_status_action, name="team_status"),
    path("teams/<int:pk>/roster-code/", generate_roster_code, name="generate_roster_code"),
    path("teams/<int:pk>/drawer/", team_drawer_view, name="team_drawer"),
    path("teams/<int:pk>/pipeline-move/", team_pipeline_move, name="team_pipeline_move"),
    path("teams/batch/", team_batch_action, name="team_batch"),
    path("checkin/", checkin_view, name="checkin"),
    path("checkin/search/", checkin_search, name="checkin_search"),
    path("checkin/<int:pk>/toggle/", checkin_toggle, name="checkin_toggle"),
    path("schedule/", schedule_list_view, name="schedule"),
    path("schedule/create/", match_create_view, name="match_create"),
    path("schedule/conflicts/", match_conflict_check, name="match_conflict_check"),
    path("schedule/<int:pk>/", match_detail_view, name="match_detail"),
    path("schedule/<int:pk>/edit/", match_edit_view, name="match_edit"),
    path("schedule/<int:pk>/delete/", match_delete_view, name="match_delete"),
    path("schedule/<int:pk>/panel/", match_panel_view, name="match_panel"),
    path("schedule/<int:pk>/status/", match_status_change, name="match_status_change"),
    path("schedule/<int:pk>/score/", match_score_update, name="match_score_update"),
    path("schedule/<int:pk>/sets-inline/", match_sets_inline_update, name="match_sets_inline"),
    path("schedule/import-csv/", schedule_csv_import_view, name="schedule_csv_import"),
    path("schedule/events/create/", event_create_view, name="event_create"),
    path("schedule/events/<int:pk>/edit/", event_edit_view, name="event_edit"),
    path("schedule/events/<int:pk>/delete/", event_delete_view, name="event_delete"),
    path("stats/", stats_list_view, name="stats"),
    path("players/", players_list_view, name="players"),
    path("players/create/", player_create_view, name="player_create"),
    path("players/<int:pk>/", player_detail_view, name="player_detail"),
    path("players/<int:pk>/edit/", player_edit_view, name="player_edit"),
    path("players/<int:pk>/delete/", player_delete_view, name="player_delete"),
    path("stats/<int:pk>/import/", stats_import_view, name="stats_import"),
    path("stats/<int:pk>/", stats_detail_view, name="stats_detail"),
    path("stats/<int:pk>/edit/", stats_edit_view, name="stats_edit"),
    path("stats/<int:pk>/manual-create/", stats_manual_create_view, name="stats_manual_create"),
    path("gallery/", gallery_list_view, name="gallery"),
    path("gallery/add/", gallery_add_view, name="gallery_add"),
    path("gallery/bulk-add/", gallery_bulk_add_view, name="gallery_bulk_add"),
    path("gallery/<int:pk>/delete/", gallery_delete_view, name="gallery_delete"),
    path("gallery/<int:pk>/edit/", gallery_photo_edit_view, name="gallery_photo_edit"),
    path("gallery/reorder/", gallery_reorder_view, name="gallery_reorder"),
    path("gallery/bulk-link/", gallery_bulk_link_view, name="gallery_bulk_link"),
    path("gallery/<int:pk>/state/", gallery_state_change_view, name="gallery_state_change"),
    path("gallery/upload/", gallery_upload_view, name="gallery_upload"),
    path("gallery/videos/add/", video_add_view, name="video_add"),
    path("gallery/videos/upload/", video_upload_view, name="video_upload"),
    path("gallery/videos/<int:pk>/edit/", video_edit_view, name="video_edit"),
    path("gallery/videos/<int:pk>/delete/", video_delete_view, name="video_delete"),
    path("gallery/videos/reorder/", video_reorder_view, name="video_reorder"),
    path("gallery/videos/bulk-link/", video_bulk_link_view, name="video_bulk_link"),

    path("rankings/", rankings_view, name="rankings"),
    path("rankings/recalculate/", rankings_recalculate_view, name="rankings_recalculate"),

    path("audit/", audit_view, name="audit"),
    path("cmd-search/", cmd_search, name="cmd_search"),

    # ── CSV Export ──
    path("export/standings/", export_standings_csv, name="export_standings"),
    path("export/player-stats/", export_player_stats_csv, name="export_player_stats"),
    path("export/results/", export_results_csv, name="export_results"),

    # ── DB Backup / Restore ──
    path("backup/", db_backup_view, name="db_backup"),
    path("backup/create/", db_backup_create, name="db_backup_create"),
    path("backup/download/<str:filename>/", db_backup_download, name="db_backup_download"),
    path("backup/download-current/", db_download_current, name="db_download_current"),
    path("backup/restore/", db_restore, name="db_restore"),
    path("backup/<str:filename>/delete/", db_backup_delete, name="db_backup_delete"),
]
