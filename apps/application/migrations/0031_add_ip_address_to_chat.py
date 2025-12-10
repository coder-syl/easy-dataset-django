# Generated manually for adding IP address field to Chat model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0030_update_customerloan_remove_foreign_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True, verbose_name='访问者IP地址'),
        ),
    ] 