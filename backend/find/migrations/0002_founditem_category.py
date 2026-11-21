from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("find", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="founditem",
            name="category",
            field=models.CharField(default="Other", max_length=40),
        ),
    ]