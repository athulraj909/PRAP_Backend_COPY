from django.db import migrations, models


def migrate_both_courses_to_non_it(apps, schema_editor):
    Course = apps.get_model('api', 'Course')
    Course.objects.filter(applicable_to='BOTH').update(applicable_to='NON_IT')


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_studentprofile_passout_year_and_more'),
    ]

    operations = [
        migrations.RunPython(
            migrate_both_courses_to_non_it,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='course',
            name='applicable_to',
            field=models.CharField(
                choices=[('IT', 'IT'), ('NON_IT', 'NON_IT')],
                default='IT',
                max_length=20,
            ),
        ),
    ]
