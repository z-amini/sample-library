from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from library.books.models import Tag, Book, Borrow, DelayPenalty


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Tag.objects.all()
    )
    type_verbose = serializers.CharField(read_only=True)

    class Meta:
        model = Book
        fields = "__all__"


class BorrowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrow
        fields = "__all__"

    @staticmethod
    def validate_duration(duration):
        if not duration:
            raise ValidationError(_("Duration is required"))
        return duration

    def save(self, **kwargs):
        try:
            if not self.instance:
                Borrow(**self.validated_data, **kwargs).clean()
            return super(BorrowSerializer, self).save(**kwargs)
        except Exception as e:
            raise ValidationError(e)


class DelayPenaltySerializer(serializers.ModelSerializer):
    class Meta:
        model = DelayPenalty
        fields = "__all__"
