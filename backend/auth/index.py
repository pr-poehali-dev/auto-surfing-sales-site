"""
Business: Регистрация и авторизация пользователей с реферальной системой
Args: event - dict с httpMethod, body (email, password, username, referral_code)
Returns: HTTP response с токеном и данными пользователя
"""

import json
import os
import hashlib
import secrets
import string
from typing import Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL')

REFERRAL_LEVELS = {
    1: 0.10,
    2: 0.05,
    3: 0.03,
    4: 0.02,
    5: 0.01
}


def generate_referral_code(length=8):
    """Генерация уникального реферального кода"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_referral_chain(conn, new_user_id: int, referred_by_id: int, registration_bonus: float = 100.0):
    """Создание цепочки реферальных начислений (5 уровней)"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    current_referrer_id = referred_by_id
    level = 1
    
    while current_referrer_id and level <= 5:
        percentage = REFERRAL_LEVELS[level]
        bonus_amount = registration_bonus * percentage
        
        cursor.execute("""
            INSERT INTO referral_earnings (user_id, referred_user_id, level, amount, percentage)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_referrer_id, new_user_id, level, bonus_amount, percentage * 100))
        
        cursor.execute("""
            UPDATE users 
            SET balance = balance + %s, total_earned = total_earned + %s
            WHERE id = %s
        """, (bonus_amount, bonus_amount, current_referrer_id))
        
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (%s, 'referral', %s, %s)
        """, (current_referrer_id, bonus_amount, f'Реферальный бонус {level} уровня от нового пользователя'))
        
        cursor.execute("SELECT referred_by_id FROM users WHERE id = %s", (current_referrer_id,))
        result = cursor.fetchone()
        current_referrer_id = result['referred_by_id'] if result else None
        level += 1


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id, X-Auth-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'register':
                email = body.get('email', '').strip()
                password = body.get('password', '').strip()
                username = body.get('username', '').strip()
                referral_code_input = body.get('referral_code', '').strip()
                
                if not email or not password or not username:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Заполните все поля'}),
                        'isBase64Encoded': False
                    }
                
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Email уже зарегистрирован'}),
                        'isBase64Encoded': False
                    }
                
                referred_by_id = None
                if referral_code_input:
                    cursor.execute("SELECT id FROM users WHERE referral_code = %s", (referral_code_input,))
                    referrer = cursor.fetchone()
                    if referrer:
                        referred_by_id = referrer['id']
                
                password_hash = hash_password(password)
                new_referral_code = generate_referral_code()
                
                while True:
                    cursor.execute("SELECT id FROM users WHERE referral_code = %s", (new_referral_code,))
                    if not cursor.fetchone():
                        break
                    new_referral_code = generate_referral_code()
                
                cursor.execute("""
                    INSERT INTO users (email, password_hash, username, referral_code, referred_by_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, email, username, referral_code, balance, total_earned, is_admin
                """, (email, password_hash, username, new_referral_code, referred_by_id))
                
                user = cursor.fetchone()
                
                if referred_by_id:
                    create_referral_chain(conn, user['id'], referred_by_id)
                
                conn.commit()
                
                token = secrets.token_urlsafe(32)
                
                user_data = dict(user)
                user_data['balance'] = float(user_data['balance'])
                user_data['total_earned'] = float(user_data['total_earned'])
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'token': token,
                        'user': user_data
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'login':
                email = body.get('email', '').strip()
                password = body.get('password', '').strip()
                
                if not email or not password:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Заполните все поля'}),
                        'isBase64Encoded': False
                    }
                
                password_hash = hash_password(password)
                
                cursor.execute("""
                    SELECT id, email, username, referral_code, balance, total_earned, is_admin
                    FROM users 
                    WHERE email = %s AND password_hash = %s
                """, (email, password_hash))
                
                user = cursor.fetchone()
                
                if not user:
                    return {
                        'statusCode': 401,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Неверный email или пароль'}),
                        'isBase64Encoded': False
                    }
                
                token = secrets.token_urlsafe(32)
                
                user_data = dict(user)
                user_data['balance'] = float(user_data['balance'])
                user_data['total_earned'] = float(user_data['total_earned'])
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'token': token,
                        'user': user_data
                    }),
                    'isBase64Encoded': False
                }
            
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Неизвестное действие'}),
                    'isBase64Encoded': False
                }
        
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()