from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods

from .forms import FoundItemForm
from .models import FoundItem


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def found(request):
    if request.method == "POST":
        form = FoundItemForm(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

        item = form.save()
        return JsonResponse(
            {
                "id": item.pk,
                "item_name": item.item_name,
                "category": item.category,
                "photo": request.build_absolute_uri(item.photo.url),
                "message": "Found item submitted.",
            },
            status=201,
        )

    try:
        page_number = int(request.GET.get("page", "1"))
        if page_number < 1:
            raise ValueError
    except ValueError:
        return JsonResponse({"error": "Page must be a positive integer."}, status=400)

    paginator = Paginator(FoundItem.objects.order_by("-created_at"), 20)
    try:
        page = paginator.page(page_number)
    except EmptyPage:
        return JsonResponse({"error": "Page does not exist."}, status=404)

    return JsonResponse(
        {
            "results": [
                {
                    "id": item.pk,
                    "item_name": item.item_name,
                    "category": item.category,
                    "description": item.description,
                    "photo": request.build_absolute_uri(item.photo.url),
                    "location_found": item.location_found,
                    "date_found": item.date_found.isoformat(),
                    "security_question": item.security_question,
                }
                for item in page.object_list
            ],
            "page": page.number,
            "pages": paginator.num_pages,
        }
    )


@require_POST
def verify_found_item(request, item_id):
    item = FoundItem.objects.filter(pk=item_id).first()
    if item is None:
        return JsonResponse({"error": "Found item not found."}, status=404)

    rate_limit_key = f"found-item-verification:{item_id}:{request.META.get('REMOTE_ADDR', 'unknown')}"
    failed_attempts = cache.get(rate_limit_key, 0)
    if failed_attempts >= 5:
        return JsonResponse(
            {"error": "Too many incorrect answers. Try again later."},
            status=429,
        )

    answer = request.POST.get("answer", "")
    if item.verify_security_answer(answer):
        cache.delete(rate_limit_key)
        return JsonResponse({"verified": True})

    cache.set(rate_limit_key, failed_attempts + 1, timeout=900)
    return JsonResponse({"verified": False}, status=400)


def home(request):
    return render(request, "index.html")


def checkout(request):
    return render(request, "checkout.html")


def services(request):
    return render(request, "services.html")


def about(request):
    return render(request, "about.html")
