import os 
import hashlib
import request
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exampt
from zxcvbn import zxcvbn
from dotenv import load_dotenv
import 