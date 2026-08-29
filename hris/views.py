"""
Views for the HRIS import preview application.
"""
from django.shortcuts import render

from hris.forms import UploadForm
from hris.services import run_import_pipeline
from hris.domain.errors import CSVStructureError


def upload_view(request):
    """Render the CSV upload form and handle POST."""
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                import_result = run_import_pipeline(csv_file)
                return render(request, 'hris/results.html', {
                    'analysis': import_result.analysis,
                    'employee_names': import_result.employee_name_lookup,
                })
            except CSVStructureError as e:
                form.add_error('csv_file', str(e))
    else:
        form = UploadForm()
    return render(request, 'hris/upload.html', {'form': form})