from django import forms
from .models import Profile,Feedback

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'age_limit']



class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'p-2 bg-gray-500 rounded-sm text-gray-200 outline-none block w-full'}),
            'message': forms.Textarea(attrs={'class': 'p-2 bg-gray-500 rounded-sm text-gray-200 outline-none block w-full', 'rows': 5}),
        }
