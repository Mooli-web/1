# users/utils.py
from kavenegar import *
from django.conf import settings

def send_otp_sms(phone_number, code):
    try:
        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        params = {
            'receptor': phone_number,
            'template': 'verify',  # نام پترنی که در پنل ساختید (مثلا verify)
            'token': code,        
            'type': 'sms',
        }
        response = api.verify_lookup(params)
        print(f"SMS Sent: {response}")
        return True
    except APIException as e:
        print(f"Kavenegar API Error: {e}")
    except HTTPException as e:
        print(f"Kavenegar HTTP Error: {e}")
    return False