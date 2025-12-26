from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('llm', '0002_seed_providers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modelconfig',
            name='project',
        ),
    ]


