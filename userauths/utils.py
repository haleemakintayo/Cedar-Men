from django.shortcuts import redirect 
from functools import wraps
import datetime
import random
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def staff_required(view_func):
  @wraps(view_func)
  def wrapper(request, *args, **kwargs):
    if not request.user.is_authenticated: 
      return redirect('login-admin') # Redirect to login if not logged in
    if not request.user.is_staff:
      return redirect('login-admin') # Redirect to home if not staff
    return view_func(request, *args, **kwargs)
  return wrapper

def generate_invoice_number():
  year = datetime.datetime.now().year
  month = datetime.datetime.now().month
  day = datetime.datetime.now().day
  random_num = random.randint(1000, 9999)
  return f"INV-{year}{month:02d}{day:02d}-{random_num}" 

def render_to_pdf(template_src, context_dict={}):
  template = get_template(template_src)
  html = template(context_dict)
  result = BytesIO()
  pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
  if not pdf.err: 
    return HttpResponse(result.getvalue(), content_type='application/pdf')
  return None
