from django.conf import settings
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from oioioi.base.main_page import register_main_page_view
from oioioi.base.navbar_links import navbar_links_registry
from oioioi.contests.controllers import submission_template_context
from oioioi.contests.models import Contest, Submission
from oioioi.contests.processors import recent_contests
from oioioi.contests.utils import visible_contests_queryset_old
from oioioi.problems.utils import filter_my_all_visible_submissions

# navbar_links_registry.register(
#     name='courses',
#     text=_("Kursy"),
#     url_generator=lambda request: 'https://kursy.szkopul.edu.pl',
#     order=400,
# )

navbar_links_registry.register(
    name="courses",
    text=_("Kursy"),
    url_generator=lambda request: "https://kursy.szkopul.edu.pl",
    order=400,
)

# TODO Add Portals main page to the menu:
# navbar_links_registry.register(
#     name='portals',
#     text=_("Portals"),
#     ...
# )


@register_main_page_view(order=100)
def main_page_view(request):
    to_show = getattr(settings, "NUM_RECENT_CONTESTS", 7)
    rcontests = recent_contests(request)
    # this is unsalvageable
    contests = list(set(Contest.objects.filter(visible_contests_queryset_old(request)).distinct()[:to_show]).difference(rcontests))
    contests.sort(key=lambda x: x.creation_date, reverse=True)
    contests = (rcontests + contests)[:to_show]

    submissions = []
    show_scores = False
    if request.user.is_authenticated:
        queryset = Submission.objects.filter(user=request.user).order_by("-date")
        to_show = getattr(settings, "NUM_PANEL_SUBMISSIONS", 7)

        # limit queryset size, because filtering all submissions is slow
        queryset = queryset[:to_show]
        limit_queryset_ids = [submission.id for submission in queryset]
        queryset = Submission.objects.filter(id__in=limit_queryset_ids).select_related(
            "user",
            "problem_instance",
            "problem_instance__contest",
            "problem_instance__round",
            "problem_instance__problem",
        )

        submissions_list = filter_my_all_visible_submissions(request, queryset).order_by("-date")
        submissions = [submission_template_context(request, s) for s in submissions_list]
        show_scores = any(s["can_see_score"] for s in submissions)

    context = {
        "contests": contests,
        "submissions": submissions,
        "show_scores": show_scores,
    }

    return TemplateResponse(request, "main-page.html", context)
