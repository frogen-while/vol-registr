"""Forms for the custom admin panel."""

import re

from django import forms
from django.db.models import Max
from django.forms import inlineformset_factory

from .constants import STAGE_GROUP
from .models import GameSet, GalleryPhoto, GalleryVideo, Match, Player, ScheduleEvent, Team


class AdminTeamForm(forms.ModelForm):
    logo_upload = forms.FileField(
        required=False,
        label="Upload logo",
        help_text="JPG / PNG from your computer",
    )
    logo_url = forms.URLField(
        required=False,
        label="Logo URL",
        help_text="Or paste any direct image link",
    )

    class Meta:
        model = Team
        fields = [
            "name",
            "logo_path",
            "league_level",
            "group_name",
            "cap_name",
            "cap_surname",
            "cap_email",
            "cap_phone",
            "payment_status",
            "blik_number",
            "status",
            "checked_in",
            "roster_code",
        ]
        widgets = {
            "logo_path": forms.TextInput(attrs={"readonly": "readonly", "style": "opacity:.6"}),
        }

    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get("logo_upload")
        url = cleaned.get("logo_url")
        if upload and url:
            raise forms.ValidationError("Provide either a file or a URL, not both.")
        return cleaned


class AdminPlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ["first_name", "last_name", "jersey_number", "position"]
        widgets = {}


PlayerInlineFormSet = inlineformset_factory(
    Team,
    Player,
    form=AdminPlayerForm,
    extra=1,
    can_delete=True,
)


class AdminMatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            "match_number",
            "stage",
            "group",
            "court",
            "start_time",
            "team_a",
            "placeholder_a",
            "team_b",
            "placeholder_b",
            "score_a",
            "score_b",
            "status",
        ]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["team_a"].required = False
        self.fields["team_b"].required = False
        self.fields["group"].required = False
        self.fields["match_number"].help_text = "Leave blank for auto-assign"
        self.fields["match_number"].required = False

    def clean(self):
        cleaned = super().clean()
        team_a = cleaned.get("team_a")
        team_b = cleaned.get("team_b")
        stage = cleaned.get("stage")
        group = cleaned.get("group")

        # team_a ≠ team_b
        if team_a and team_b and team_a == team_b:
            raise forms.ValidationError("Team A and Team B must be different.")

        # group required only for GROUP stage
        if stage == STAGE_GROUP and not group:
            self.add_error("group", "Group is required for Group Stage matches.")

        # court/time conflict check
        court = cleaned.get("court")
        start_time = cleaned.get("start_time")
        if court and start_time:
            conflict = Match.objects.filter(court=court, start_time=start_time)
            if self.instance.pk:
                conflict = conflict.exclude(pk=self.instance.pk)
            if conflict.exists():
                raise forms.ValidationError(
                    f"Court {court} is already booked at {start_time:%d %b %H:%M}."
                )

        # auto-assign match_number
        match_number = cleaned.get("match_number")
        if not match_number:
            max_num = Match.objects.order_by("-match_number").values_list(
                "match_number", flat=True
            ).first() or 0
            cleaned["match_number"] = max_num + 1

        return cleaned


class AdminGameSetForm(forms.ModelForm):
    class Meta:
        model = GameSet
        fields = ["set_number", "score_a", "score_b"]
        widgets = {
            "set_number": forms.NumberInput(attrs={"style": "width:60px"}),
            "score_a": forms.NumberInput(attrs={"style": "width:60px"}),
            "score_b": forms.NumberInput(attrs={"style": "width:60px"}),
        }


GameSetInlineFormSet = inlineformset_factory(
    Match,
    GameSet,
    form=AdminGameSetForm,
    extra=3,
    can_delete=True,
)


class AdminScheduleEventForm(forms.ModelForm):
    class Meta:
        model = ScheduleEvent
        fields = ["event_type", "title", "start_time", "end_time", "description"]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            self.add_error("end_time", "End time must be after start time.")
        return cleaned


# ── Google Drive helpers ─────────────────────────────────

_DRIVE_FILE_ID_RE = re.compile(
    r"(?:/d/|id=|open\?id=)([a-zA-Z0-9_-]{10,})"
)


def _parse_drive_file_id(url: str) -> str | None:
    """Extract the Google Drive file-id from various URL formats."""
    m = _DRIVE_FILE_ID_RE.search(url)
    return m.group(1) if m else None


def _drive_thumbnail(file_id: str) -> str:
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"


def _drive_view_url(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view"


# ── Gallery forms ────────────────────────────────────────


class GalleryPhotoForm(forms.ModelForm):
    class Meta:
        model = GalleryPhoto
        fields = ["title", "drive_url"]

    def clean_drive_url(self):
        url = self.cleaned_data["drive_url"]
        file_id = _parse_drive_file_id(url)
        if not file_id:
            raise forms.ValidationError(
                "Cannot extract file ID. Paste a Google Drive share link."
            )
        # store parsed id for save()
        self._drive_file_id = file_id
        return url

    def save(self, commit=True):
        obj = super().save(commit=False)
        file_id = self._drive_file_id
        obj.drive_file_id = file_id
        obj.thumbnail_url = _drive_thumbnail(file_id)
        obj.drive_url = _drive_view_url(file_id)
        if not obj.order:
            max_order = (
                GalleryPhoto.objects.aggregate(m=Max("order"))["m"] or 0
            )
            obj.order = max_order + 1
        if commit:
            obj.save()
        return obj


class GalleryBulkForm(forms.Form):
    urls = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Paste Google Drive URLs, one per line"}),
        help_text="One Google Drive link per line.",
    )


class GalleryVideoForm(forms.ModelForm):
    class Meta:
        model = GalleryVideo
        fields = ["title", "drive_url", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_drive_url(self):
        url = self.cleaned_data["drive_url"]
        file_id = _parse_drive_file_id(url)
        if not file_id:
            raise forms.ValidationError(
                "Cannot extract file ID. Paste a Google Drive share link."
            )
        self._drive_file_id = file_id
        return url

    def save(self, commit=True):
        obj = super().save(commit=False)
        file_id = self._drive_file_id
        obj.drive_file_id = file_id
        obj.thumbnail_url = _drive_thumbnail(file_id)
        obj.drive_url = _drive_view_url(file_id)
        if not obj.order:
            max_order = (
                GalleryVideo.objects.aggregate(m=Max("order"))["m"] or 0
            )
            obj.order = max_order + 1
        if commit:
            obj.save()
        return obj


# ── Highlight form ───────────────────────────────────────


class MatchHighlightForm(forms.ModelForm):
    class Meta:
        from .models import MatchHighlight

        model = MatchHighlight
        fields = ["title", "description", "match", "media_url", "thumbnail_url", "is_featured", "order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
