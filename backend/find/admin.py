from django.contrib import admin

from .forms import FoundItemForm
from .models import FoundItem


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    form = FoundItemForm
    list_display = ("item_name", "location_found", "date_found", "created_at")
    search_fields = ("item_name", "description", "location_found")
    readonly_fields = ("security_answer_hash", "created_at")
