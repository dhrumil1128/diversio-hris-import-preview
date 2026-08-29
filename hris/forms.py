"""
Forms for the HRIS import preview application.
"""
from django import forms


class UploadForm(forms.Form):
    """Form for uploading a CSV file."""
    csv_file = forms.FileField(
        label='HRIS CSV file',
        help_text='Upload a CSV file exported from the HRIS.',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.csv,text/csv',
        }),
    )

    def clean_csv_file(self):
        """Validate that the uploaded file has a .csv extension."""
        csv_file = self.cleaned_data.get('csv_file')
        if not csv_file:
            raise forms.ValidationError('Please select a CSV file to upload.')

        # Server-side extension validation
        if not csv_file.name.lower().endswith('.csv'):
            raise forms.ValidationError(
                'Please upload a CSV file. Only .csv files are supported.'
            )

        return csv_file