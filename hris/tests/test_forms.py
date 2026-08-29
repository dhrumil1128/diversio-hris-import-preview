"""
Tests for the UploadForm validation.
"""
import io
import unittest
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from hris.forms import UploadForm


class TestUploadForm(unittest.TestCase):
    def test_csv_file_is_accepted(self):
        """Valid .csv file is accepted."""
        csv_content = b'employee_id,employee_name,email,manager_id,manager_email,department\nDIV-001,John,john@example.com,,,\n'
        file_obj = SimpleUploadedFile('sample.csv', csv_content, content_type='text/csv')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertTrue(form.is_valid(), form.errors)

    def test_uppercase_csv_extension_is_accepted(self):
        """Uppercase .CSV extension is accepted."""
        csv_content = b'employee_id,employee_name,email,manager_id,manager_email,department\nDIV-001,John,john@example.com,,,\n'
        file_obj = SimpleUploadedFile('sample.CSV', csv_content, content_type='text/csv')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertTrue(form.is_valid(), form.errors)

    def test_mixed_case_csv_extension_is_accepted(self):
        """Mixed case .Csv extension is accepted."""
        csv_content = b'employee_id,employee_name,email,manager_id,manager_email,department\nDIV-001,John,john@example.com,,,\n'
        file_obj = SimpleUploadedFile('sample.Csv', csv_content, content_type='text/csv')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertTrue(form.is_valid(), form.errors)

    def test_txt_file_is_rejected(self):
        """.txt file is rejected with clear error."""
        txt_content = b'employee_id,employee_name,email,manager_id,manager_email,department\nDIV-001,John,john@example.com,,,\n'
        file_obj = SimpleUploadedFile('sample.txt', txt_content, content_type='text/plain')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)
        self.assertTrue(
            any('Only .csv files are supported' in str(e) for e in form.errors['csv_file']),
            f"Expected CSV error message, got: {form.errors['csv_file']}"
        )

    def test_pdf_file_is_rejected(self):
        """.pdf file is rejected."""
        pdf_content = b'%PDF-1.4...'
        file_obj = SimpleUploadedFile('sample.pdf', pdf_content, content_type='application/pdf')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)

    def test_xlsx_file_is_rejected(self):
        """.xlsx file is rejected."""
        xlsx_content = b'PK...'
        file_obj = SimpleUploadedFile('sample.xlsx', xlsx_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)

    def test_json_file_is_rejected(self):
        """.json file is rejected."""
        json_content = b'{"data": []}'
        file_obj = SimpleUploadedFile('sample.json', json_content, content_type='application/json')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)

    def test_no_extension_file_is_rejected(self):
        """File without extension is rejected."""
        csv_content = b'employee_id,employee_name,email,manager_id,manager_email,department\nDIV-001,John,john@example.com,,,\n'
        file_obj = SimpleUploadedFile('sample', csv_content, content_type='text/csv')
        form = UploadForm(data={}, files={'csv_file': file_obj})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)

    def test_missing_file_is_rejected(self):
        """Missing file is rejected by Django's required field validation."""
        form = UploadForm(data={}, files={})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)
        self.assertTrue(
            any('required' in str(e).lower() for e in form.errors['csv_file']),
            f"Expected required field error, got: {form.errors['csv_file']}"
        )

    def test_form_has_accept_attribute(self):
        """Form widget includes accept attribute for browser file picker."""
        form = UploadForm()
        widget = form.fields['csv_file'].widget
        self.assertIn('accept', widget.attrs)
        self.assertEqual(widget.attrs['accept'], '.csv,text/csv')


if __name__ == "__main__":
    unittest.main()