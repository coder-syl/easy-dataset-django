# Generated manually for adding marketing_type field to Customer model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0027_customer_product_interactionhistory_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='marketing_type',
            field=models.CharField(max_length=50, null=True),
        ),
    ] 