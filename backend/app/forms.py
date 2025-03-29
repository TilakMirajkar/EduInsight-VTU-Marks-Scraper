# from django import forms

# class ScraperForm(forms.Form):
#     prefix_usn = forms.CharField(label="USN Prefix", max_length=7)
#     usn_range = forms.CharField(label="USN Range", max_length=20)
#     sem = forms.IntegerField(label="Semester", min_value=1, max_value=8)
#     url = forms.URLField(label="Result Page URL")
from django import forms

class ScraperForm(forms.Form):
    prefix_usn = forms.CharField(
        label="USN Prefix", 
        max_length=7,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 2AG21CS'}),
    )
    
    usn_range = forms.CharField(
        label="USN Range", 
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 1-20,45,50-100'}),
    )
    
    sem = forms.IntegerField(
        label="Semester", 
        min_value=1, 
        max_value=8,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 7'}),
    )
    
    url = forms.URLField(
        label="Result Page URL",
        widget=forms.URLInput(attrs={'placeholder': 'https://results.vtu.ac.in/...'}),
    )
    
    def clean_usn_range(self):
        """Validate USN range format"""
        usn_range = self.cleaned_data.get('usn_range')
        
        # Validate format
        parts = usn_range.split(',')
        for part in parts:
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start > end:
                        raise forms.ValidationError("In range specification, start number must be less than end number.")
                except ValueError:
                    raise forms.ValidationError("Invalid range format. Use numbers only (e.g., 001-020).")
            else:
                try:
                    int(part)
                except ValueError:
                    raise forms.ValidationError("Invalid USN number. Use numbers only.")
        
        return usn_range