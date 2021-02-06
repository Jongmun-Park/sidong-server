from django.contrib.postgres.fields import ArrayField
from django.db import models
from file.models import File
from user.models import Artist

PAINTING = 0
SCULPTURE = 1
DRAWING = 2
PRINT = 3
PAPER = 4
TEXTILE = 5
ETC = 6

CHOICES_OF_MEDIUM = [
    (PAINTING, '회화'),
    (SCULPTURE, '조각'),
    (DRAWING, '소묘'),
    (PRINT, '판화'),
    (PAPER, '종이'),
    (TEXTILE, '섬유'),
    (ETC, '기타 매체'),
]


class Theme(models.Model):
    name = models.CharField(max_length=16)
    medium = models.PositiveIntegerField(
        choices=CHOICES_OF_MEDIUM, default=PAINTING
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'medium'], name='unique_theme'),
        ]


class Style(models.Model):
    name = models.CharField(max_length=16)
    medium = models.PositiveIntegerField(
        choices=CHOICES_OF_MEDIUM, default=PAINTING
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'medium'], name='unique_style'),
        ]


class Technique(models.Model):
    name = models.CharField(max_length=16)
    medium = models.PositiveIntegerField(
        choices=CHOICES_OF_MEDIUM, default=PAINTING
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'medium'], name='unique_technique'),
        ]


class Art(models.Model):
    NOT_FOR_SALE = 0
    ON_SALE = 1
    SOLD_OUT = 2

    CHOICES_OF_SALE_STATUS = [
        (NOT_FOR_SALE, '비매품'),
        (ON_SALE, '판매품'),
        (SOLD_OUT, '판매 완료'),
    ]

    LANDSCAPE = 0
    PORTRAIT = 1
    SQUARE = 2
    ETC = 3

    CHOICES_OF_ORIENTATION = [
        (LANDSCAPE, '가로로 긴 배치'),
        (PORTRAIT, '세로가 긴 배치'),
        (SQUARE, '정사각형'),
        (ETC, '기타'),
    ]

    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'

    CHOICES_OF_SIZE = [
        (SMALL, 'small'),
        (MEDIUM, 'medium'),
        (LARGE, 'large'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    artist = models.ForeignKey(
        Artist, on_delete=models.SET_NULL, null=True, related_name='arts',
    )
    name = models.CharField(max_length=128, blank=False)
    description = models.TextField(blank=True)
    medium = models.PositiveIntegerField(
        choices=CHOICES_OF_MEDIUM, default=PAINTING)
    theme = models.ForeignKey(
        Theme, on_delete=models.SET_NULL, null=True, related_name='arts',
    )
    style = models.ForeignKey(
        Style, on_delete=models.SET_NULL, null=True, related_name='arts',
    )
    technique = models.ForeignKey(
        Technique, on_delete=models.SET_NULL, null=True, related_name='arts',
    )
    sale_status = models.PositiveIntegerField(
        choices=CHOICES_OF_SALE_STATUS, default=NOT_FOR_SALE,
    )
    is_framed = models.BooleanField(default=False)
    price = models.PositiveIntegerField(null=True, default=None)
    orientation = models.PositiveIntegerField(
        choices=CHOICES_OF_ORIENTATION, default=LANDSCAPE,
    )
    size = models.CharField(choices=CHOICES_OF_SIZE, max_length=8)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    images = ArrayField(models.PositiveIntegerField(), default=list)
