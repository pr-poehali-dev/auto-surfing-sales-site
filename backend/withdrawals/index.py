"""
Business: Управление заявками на вывод средств (создание, просмотр, обработка админом)
Args: event - dict с httpMethod, body, headers (X-User-Id для пользователя)
Returns: HTTP response со списком заявок или результатом операции
"""

import json
import os
from typing import Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL')


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id, X-Admin-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        headers = event.get('headers', {})
        user_id = headers.get('X-User-Id') or headers.get('x-user-id')
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if method == 'GET':
            if not user_id:
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Требуется авторизация'}),
                    'isBase64Encoded': False
                }
            
            cursor.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            is_admin = user and user['is_admin']
            
            if is_admin:
                cursor.execute("""
                    SELECT 
                        wr.*,
                        u.username,
                        u.email,
                        admin_user.username as processed_by_name
                    FROM withdrawal_requests wr
                    JOIN users u ON wr.user_id = u.id
                    LEFT JOIN users admin_user ON wr.processed_by = admin_user.id
                    ORDER BY 
                        CASE wr.status 
                            WHEN 'pending' THEN 1 
                            WHEN 'approved' THEN 2 
                            ELSE 3 
                        END,
                        wr.created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT * FROM withdrawal_requests
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
            
            requests = cursor.fetchall()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'requests': [dict(r) for r in requests],
                    'is_admin': is_admin
                }, default=str),
                'isBase64Encoded': False
            }
        
        elif method == 'POST':
            if not user_id:
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Требуется авторизация'}),
                    'isBase64Encoded': False
                }
            
            body = json.loads(event.get('body', '{}'))
            amount = body.get('amount')
            payment_method = body.get('payment_method', '').strip()
            payment_details = body.get('payment_details', '').strip()
            
            if not amount or not payment_method or not payment_details:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Заполните все поля'}),
                    'isBase64Encoded': False
                }
            
            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError()
            except:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Некорректная сумма'}),
                    'isBase64Encoded': False
                }
            
            cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user or user['balance'] < amount:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Недостаточно средств'}),
                    'isBase64Encoded': False
                }
            
            cursor.execute("""
                INSERT INTO withdrawal_requests (user_id, amount, payment_method, payment_details, status)
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id, created_at
            """, (user_id, amount, payment_method, payment_details))
            
            new_request = cursor.fetchone()
            conn.commit()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'request_id': new_request['id'],
                    'message': 'Заявка на вывод создана'
                }, default=str),
                'isBase64Encoded': False
            }
        
        elif method == 'PUT':
            if not user_id:
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Требуется авторизация'}),
                    'isBase64Encoded': False
                }
            
            cursor.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user or not user['is_admin']:
                return {
                    'statusCode': 403,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Доступ запрещён'}),
                    'isBase64Encoded': False
                }
            
            body = json.loads(event.get('body', '{}'))
            request_id = body.get('request_id')
            new_status = body.get('status')
            admin_comment = body.get('admin_comment', '')
            
            if not request_id or new_status not in ['approved', 'rejected', 'completed']:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Некорректные данные'}),
                    'isBase64Encoded': False
                }
            
            cursor.execute("""
                SELECT wr.*, u.balance 
                FROM withdrawal_requests wr
                JOIN users u ON wr.user_id = u.id
                WHERE wr.id = %s
            """, (request_id,))
            
            withdrawal = cursor.fetchone()
            
            if not withdrawal:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Заявка не найдена'}),
                    'isBase64Encoded': False
                }
            
            if new_status == 'completed':
                if withdrawal['status'] != 'approved':
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Заявка должна быть сначала одобрена'}),
                        'isBase64Encoded': False
                    }
                
                cursor.execute("""
                    UPDATE users 
                    SET balance = balance - %s
                    WHERE id = %s AND balance >= %s
                """, (withdrawal['amount'], withdrawal['user_id'], withdrawal['amount']))
                
                if cursor.rowcount == 0:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Недостаточно средств у пользователя'}),
                        'isBase64Encoded': False
                    }
                
                cursor.execute("""
                    INSERT INTO transactions (user_id, type, amount, description)
                    VALUES (%s, 'withdrawal', -%s, %s)
                """, (withdrawal['user_id'], withdrawal['amount'], f"Вывод средств #{request_id}"))
            
            cursor.execute("""
                UPDATE withdrawal_requests
                SET status = %s, admin_comment = %s, processed_at = %s, processed_by = %s
                WHERE id = %s
            """, (new_status, admin_comment, datetime.now(), user_id, request_id))
            
            conn.commit()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'message': f'Статус изменён на {new_status}'
                }),
                'isBase64Encoded': False
            }
        
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
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
