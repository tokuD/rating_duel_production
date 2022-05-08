from django import forms

from . import models


class CreateResultTableForm(forms.ModelForm):

    class Meta:
        model = models.ResultTable
        fields = ['league', ]


