from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .models import FoundItem


class FoundItemApiTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        cache.clear()

    def tearDown(self):
        cache.clear()
        self.settings_override.disable()
        self.media_directory.cleanup()

    def make_photo(self, filename="item.png"):
        image_buffer = BytesIO()
        Image.new("RGB", (10, 10), color="blue").save(image_buffer, format="PNG")
        return SimpleUploadedFile(filename, image_buffer.getvalue(), content_type="image/png")

    def found_item_data(self, **overrides):
        data = {
            "item_name": "Blue water bottle",
            "category": "Other",
            "description": "A blue bottle with a sticker.",
            "photo": self.make_photo(),
            "location_found": "Library",
            "date_found": date.today().isoformat(),
            "finder_name": "Finder",
            "finder_contact": "finder@example.com",
            "security_question": "What sticker is on the bottle?",
            "security_answer": "USIU",
        }
        data.update(overrides)
        return data

    def test_submit_found_item_stores_photo_and_hashes_answer(self):
        response = self.client.post("/found/", self.found_item_data())

        self.assertEqual(response.status_code, 201)
        item = FoundItem.objects.get(pk=response.json()["id"])
        self.assertTrue(item.photo.name.startswith("found_items/"))
        self.assertNotEqual(item.security_answer_hash, "usiu")
        self.assertTrue(item.verify_security_answer(" usiu "))

    def test_submit_rejects_non_image_upload(self):
        response = self.client.post(
            "/found/",
            self.found_item_data(
                photo=SimpleUploadedFile(
                    "item.png", b"not an image", content_type="image/png"
                )
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(FoundItem.objects.exists())

    def test_found_listing_does_not_expose_finder_contact_or_answer_hash(self):
        item = FoundItem(**{
            key: value
            for key, value in self.found_item_data().items()
            if key not in {"photo", "security_answer"}
        })
        item.photo = self.make_photo()
        item.set_security_answer("USIU")
        item.save()

        response = self.client.get("/found/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        result = response.json()["results"][0]
        self.assertEqual(result["category"], item.category)
        self.assertEqual(result["security_question"], item.security_question)
        self.assertNotIn("finder_contact", result)
        self.assertNotIn("security_answer_hash", result)

    def test_security_answer_verification_and_rate_limit(self):
        response = self.client.post("/found/", self.found_item_data())
        item_id = response.json()["id"]

        wrong_response = None
        for _ in range(5):
            wrong_response = self.client.post(
                f"/found/{item_id}/verify/", {"answer": "wrong"}
            )
            self.assertEqual(wrong_response.status_code, 400)

        limited_response = self.client.post(
            f"/found/{item_id}/verify/", {"answer": "USIU"}
        )
        self.assertEqual(limited_response.status_code, 429)

        cache.clear()
        verified_response = self.client.post(
            f"/found/{item_id}/verify/", {"answer": "USIU"}
        )
        self.assertEqual(verified_response.status_code, 200)
        self.assertTrue(verified_response.json()["verified"])
