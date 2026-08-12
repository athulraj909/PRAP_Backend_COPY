import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prap_backend.settings')
django.setup()

from api.models import Question, AssessmentCategory
from api.serializers import QuestionSerializer, AssessmentCategorySerializer

print('Questions:', Question.objects.count())
print('Active Questions:', Question.objects.filter(status='Active').count())
print('Categories:', AssessmentCategory.objects.count())
print('Active Categories:', AssessmentCategory.objects.filter(status='Active').count())

if Question.objects.exists():
    print('\nSample Question API Response:')
    q = Question.objects.first()
    serializer = QuestionSerializer(q)
    print(json.dumps(serializer.data, indent=2))

if AssessmentCategory.objects.exists():
    print('\nCategory API Response:')
    cat = AssessmentCategory.objects.first()
    serializer = AssessmentCategorySerializer(cat)
    print(json.dumps(serializer.data, indent=2))
