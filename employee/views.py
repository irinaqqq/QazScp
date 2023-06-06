import csv
import io
import codecs
import base64
from django.shortcuts import render, redirect
from django.http import HttpResponse
from cryptography.fernet import Fernet
from .models import Employee
from .forms import EmployeeForm
from django.views.decorators.csrf import csrf_exempt

def home(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = EmployeeForm()

    employees = Employee.objects.all()

    context = {
        'form': form,
        'employees': employees,
    }

    return render(request, 'home.html', context)



@csrf_exempt
def download(request):
    employees = Employee.objects.all()

    # Generate CSV data
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(['Full Name', 'Phone Number', 'Address'])
    for employee in employees:
        writer.writerow([employee.full_name, employee.phone_number, employee.address])
    csv_string = csv_data.getvalue()

    # Encrypt CSV data
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(csv_string.encode())
    encrypted_csv = codecs.encode(cipher_text, 'base64').decode()

    # Save key to session
    request.session['key'] = key.decode()

    # Create HTTP response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'

    # Write encrypted CSV data with key as the first row
    writer = csv.writer(response)
    writer.writerow([key.decode()])
    writer.writerow([encrypted_csv])

    # Return response
    return response

    


def decrypt(request):
    if request.method == 'POST':
        # Get key and encrypted CSV file from request
        key_row = request.FILES['file'].readline().decode().strip()
        key = key_row.encode()
        file = request.FILES['file'].read().decode()

        # Decrypt CSV file
        cipher_suite = Fernet(key)
        cipher_text = codecs.decode(file.encode(), 'base64')
        plain_text = cipher_suite.decrypt(cipher_text).decode()

        # Parse CSV data
        csv_data = io.StringIO(plain_text)
        reader = csv.reader(csv_data)
        next(reader)  # Skip header row
        employees = []
        for row in reader:
            employee = Employee(full_name=row[0], phone_number=row[1], address=row[2])
            employees.append(employee)

        context = {
            'employees': employees,
        }

        return render(request, 'decrypt.html', context)

    else:
        return render(request, 'decrypt.html')

def main(request):
    return render(request, 'main.html')