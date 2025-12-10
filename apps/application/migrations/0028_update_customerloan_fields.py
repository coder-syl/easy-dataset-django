# Generated manually to update CustomerLoan fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0027_customer_product_interactionhistory_and_more'),
    ]

    operations = [
        # 添加新字段
        migrations.AddField(
            model_name='customerloan',
            name='customer_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='cert_id',
            field=models.CharField(max_length=18, null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='balance',
            field=models.DecimalField(decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='expir_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='total_prd',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='clear_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='leading_rate',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='interest_collection_cycle',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='business_type',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='customerloan',
            name='product_name',
            field=models.CharField(max_length=200, null=True),
        ),
        
        # 修改现有字段
        migrations.AlterField(
            model_name='customerloan',
            name='loan_amount',
            field=models.DecimalField(decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='customerloan',
            name='loan_date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='customerloan',
            name='repayment_method',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='customerloan',
            name='loan_status',
            field=models.CharField(max_length=50, null=True),
        ),
        
        # 删除旧字段
        migrations.RemoveField(
            model_name='customerloan',
            name='product_id',
        ),
        migrations.RemoveField(
            model_name='customerloan',
            name='maturity_date',
        ),
        migrations.RemoveField(
            model_name='customerloan',
            name='remaining_amount',
        ),
        migrations.RemoveField(
            model_name='customerloan',
            name='loan_purpose',
        ),
        migrations.RemoveField(
            model_name='customerloan',
            name='loan_type',
        ),
        migrations.RemoveField(
            model_name='customerloan',
            name='interest_rate',
        ),
    ] 