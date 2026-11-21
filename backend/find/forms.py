from django import forms
from django.utils import timezone

from .models import FoundItem


class FoundItemForm(forms.ModelForm):
    security_answer = forms.CharField(
        max_length=255,
        strip=True,
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = FoundItem
        fields = (
            "item_name",
            "category",
            "description",
            "photo",
            "location_found",
            "date_found",
            "finder_name",
            "finder_contact",
            "security_question",
        )

    def clean_date_found(self):
        date_found = self.cleaned_data["date_found"]
        if date_found > timezone.localdate():
            raise forms.ValidationError("Date found cannot be in the future.")
        return date_found

    def save(self, commit=True):
        item = super().save(commit=False)
        item.set_security_answer(self.cleaned_data["security_answer"])
        if commit:
            item.save()
            self.save_m2m()
        return item
