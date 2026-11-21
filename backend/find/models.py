from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


def validate_image_size(image):
    max_size = 5 * 1024 * 1024
    if image.size > max_size:
        raise ValidationError("Image must be 5 MB or smaller.")


class FoundItem(models.Model):
    item_name = models.CharField(max_length=120)
    category = models.CharField(max_length=40, default="Other")
    description = models.TextField()
    photo = models.ImageField(
        upload_to="found_items/%Y/%m/",
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
    )
    location_found = models.CharField(max_length=200)
    date_found = models.DateField()
    finder_name = models.CharField(max_length=120)
    finder_contact = models.CharField(max_length=254)
    security_question = models.CharField(max_length=255)
    security_answer_hash = models.CharField(max_length=128, blank=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def set_security_answer(self, answer):
        self.security_answer_hash = make_password(answer.strip().casefold())

    def verify_security_answer(self, answer):
        if not self.security_answer_hash:
            return False
        return check_password(answer.strip().casefold(), self.security_answer_hash)

    def __str__(self):
        return self.item_name
