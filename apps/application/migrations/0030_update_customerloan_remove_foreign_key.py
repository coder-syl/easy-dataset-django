# Generated manually to update CustomerLoan and Customer models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0029_merge_20250722_0851'),
    ]

    operations = [
        # 添加身份证号字段到Customer
        migrations.AddField(
            model_name='customer',
            name='cert_id',
            field=models.CharField(max_length=18, null=True),
        ),
        
        # 删除CustomerLoan的外键
        migrations.RemoveField(
            model_name='customerloan',
            name='customer',
        ),
    ] 