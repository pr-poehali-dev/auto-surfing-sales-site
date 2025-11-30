"""
Business: Получение реферальной статистики пользователя (5 уровней)
Args: event - dict с httpMethod, headers (X-User-Id)
Returns: HTTP response со статистикой рефералов по уровням
"""

import json
import os
from typing import Dict, Any
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
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'GET':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        headers = event.get('headers', {})
        user_id = headers.get('X-User-Id') or headers.get('x-user-id')
        
        if not user_id:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Требуется авторизация'}),
                'isBase64Encoded': False
            }
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, email, username, referral_code, balance, total_earned
            FROM users WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Пользователь не найден'}),
                'isBase64Encoded': False
            }
        
        cursor.execute("""
            SELECT 
                level,
                COUNT(DISTINCT referred_user_id) as count,
                SUM(amount) as total_earned
            FROM referral_earnings
            WHERE user_id = %s
            GROUP BY level
            ORDER BY level
        """, (user_id,))
        
        levels_data = cursor.fetchall()
        
        cursor.execute("""
            SELECT COUNT(DISTINCT referred_user_id) as total_referrals,
                   SUM(amount) as total_referral_earnings
            FROM referral_earnings
            WHERE user_id = %s
        """, (user_id,))
        
        totals = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                u.id,
                u.username,
                u.email,
                re.level,
                re.amount,
                re.created_at
            FROM referral_earnings re
            JOIN users u ON re.referred_user_id = u.id
            WHERE re.user_id = %s
            ORDER BY re.created_at DESC
            LIMIT 50
        """, (user_id,))
        
        recent_referrals = cursor.fetchall()
        
        levels = {}
        for i in range(1, 6):
            levels[f'level_{i}'] = {
                'count': 0,
                'earned': 0.0,
                'percentage': [10, 5, 3, 2, 1][i-1]
            }
        
        for level_data in levels_data:
            level_num = level_data['level']
            levels[f'level_{level_num}'] = {
                'count': level_data['count'],
                'earned': float(level_data['total_earned'] or 0),
                'percentage': [10, 5, 3, 2, 1][level_num-1]
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'user': dict(user),
                'total_referrals': totals['total_referrals'] or 0,
                'total_referral_earnings': float(totals['total_referral_earnings'] or 0),
                'levels': levels,
                'recent_referrals': [dict(r) for r in recent_referrals]
            }, default=str),
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
