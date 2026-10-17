"""Activities controller: volunteers (and admins) browse the activity catalogue.

Thin by design (Controller in MVC): read the query string, call BrowseService,
pick a template. The filter form is a GET form, so its values live in the URL
and a page can be bookmarked or shared; `BrowseFilterSchema.from_query` turns
them into typed filters and quietly drops anything invalid (FR-4).
Both routes accept any logged-in role (FR-2); anonymous visitors are sent to
the login page by the app-wide gate in `create_app`.
"""

from __future__ import annotations

from flask import Blueprint, render_template, request
from flask.typing import ResponseReturnValue
from flask_login import current_user

from app.auth.roles import role_required
from app.models import RoleName
from app.schemas.browse import BrowseFilterSchema
from app.services.browse_service import BrowseService

activities_bp = Blueprint("activities", __name__, url_prefix="/activities")


@activities_bp.get("")  # the empty rule means exactly "/activities" (no trailing slash)
@role_required(RoleName.VOLUNTEER, RoleName.ADMIN)
def list_activities() -> ResponseReturnValue:
    """GET /activities?keyword=&location_id=&activity_date=&page= : one page of OPEN activities."""
    service = BrowseService.build()
    filters = BrowseFilterSchema.from_query(request.args)
    page = service.list_open(current_user, filters)
    # The <select> macro wants (value, label) pairs.
    location_options = [
        (loc.id, loc.location_name) for loc in service.locations_for_filter(current_user)
    ]
    return render_template(
        "volunteer/activities/list.html",
        page=page,
        filters=filters,
        location_options=location_options,
    )


@activities_bp.get("/<int:activity_id>")
@role_required(RoleName.VOLUNTEER, RoleName.ADMIN)
def detail(activity_id: int) -> ResponseReturnValue:
    """GET /activities/<id> : everything about one activity, or the 404 page."""
    activity, location = BrowseService.build().get_activity(current_user, activity_id)
    return render_template("volunteer/activities/detail.html", activity=activity, location=location)
