import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import Icon from '@/components/ui/icon';
import { Input } from '@/components/ui/input';

const REFERRALS_API = 'https://functions.poehali.dev/36b5a91a-1e7c-484b-9638-a160fdcb71f6';
const BASE_URL = window.location.origin;

interface User {
  id: number;
  email: string;
  username: string;
  referral_code: string;
  balance: number;
  total_earned: number;
  is_admin: boolean;
}

interface ReferralLevel {
  count: number;
  earned: number;
  percentage: number;
}

interface ReferralStats {
  total_referrals: number;
  total_referral_earnings: number;
  levels: {
    level_1: ReferralLevel;
    level_2: ReferralLevel;
    level_3: ReferralLevel;
    level_4: ReferralLevel;
    level_5: ReferralLevel;
  };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      navigate('/login');
      return;
    }
    
    const userData = JSON.parse(userStr);
    setUser(userData);
    fetchStats(userData.id);
  }, [navigate]);

  const fetchStats = async (userId: number) => {
    try {
      const response = await fetch(REFERRALS_API, {
        headers: {
          'X-User-Id': userId.toString(),
        },
      });

      const data = await response.json();
      if (response.ok) {
        setStats(data);
        setUser(data.user);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const copyReferralLink = () => {
    const link = `${BASE_URL}/register?ref=${user?.referral_code}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    toast({
      title: 'Скопировано!',
      description: 'Реферальная ссылка скопирована в буфер обмена',
    });
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Icon name="Loader2" className="animate-spin" size={40} />
      </div>
    );
  }

  if (!user || !stats) {
    return null;
  }

  const referralLink = `${BASE_URL}/register?ref=${user.referral_code}`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto p-4 max-w-6xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold">Личный кабинет</h1>
            <p className="text-gray-600">Добро пожаловать, {user.username}!</p>
          </div>
          <div className="flex gap-2">
            {user.is_admin && (
              <Button onClick={() => navigate('/admin')} variant="outline">
                <Icon name="Shield" className="mr-2" size={16} />
                Админка
              </Button>
            )}
            <Button onClick={() => navigate('/withdraw')} variant="outline">
              <Icon name="Wallet" className="mr-2" size={16} />
              Вывести
            </Button>
            <Button onClick={handleLogout} variant="outline">
              <Icon name="LogOut" className="mr-2" size={16} />
              Выход
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Баланс</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{user.balance.toFixed(2)} ₽</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Всего заработано</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{user.total_earned.toFixed(2)} ₽</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Всего рефералов</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">{stats.total_referrals}</div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon name="Link" size={20} />
              Ваша реферальная ссылка
            </CardTitle>
            <CardDescription>
              Приглашайте друзей и получайте бонусы с 5 уровней!
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input value={referralLink} readOnly className="font-mono text-sm" />
              <Button onClick={copyReferralLink}>
                <Icon name={copied ? 'Check' : 'Copy'} size={16} />
              </Button>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Icon name="TrendingUp" size={18} />
                Реферальная программа - 5 уровней
              </h4>
              <ul className="space-y-1 text-sm text-gray-700">
                <li>🥇 <strong>1 уровень:</strong> 10% от заработка приглашённого</li>
                <li>🥈 <strong>2 уровень:</strong> 5% от заработка рефералов ваших рефералов</li>
                <li>🥉 <strong>3 уровень:</strong> 3% от 3-го уровня</li>
                <li>🏅 <strong>4 уровень:</strong> 2% от 4-го уровня</li>
                <li>🎖️ <strong>5 уровень:</strong> 1% от 5-го уровня</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Статистика по уровням</CardTitle>
            <CardDescription>
              Заработок с реферальной программы: {stats.total_referral_earnings.toFixed(2)} ₽
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.levels).map(([key, level], index) => (
                <div key={key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center font-bold text-blue-600">
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-semibold">Уровень {index + 1}</div>
                      <div className="text-sm text-gray-600">{level.percentage}% от заработка</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{level.count} чел.</div>
                    <div className="text-sm text-green-600">{level.earned.toFixed(2)} ₽</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
