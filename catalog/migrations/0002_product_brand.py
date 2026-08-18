from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Brand, vendor, or manufacturer name',
                max_length=255,
                null=True,
            ),
        ),
    ]
