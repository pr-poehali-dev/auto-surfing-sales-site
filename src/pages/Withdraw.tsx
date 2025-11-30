import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import Icon from '@/components/ui/icon';

const WITHDRAWALS_API = 'https://functions.poehali.dev/c3d3ef57-3cb0-4ed9-a0b6-41ecbde6c6e9';

interface User {
  id: number;
  balance: number;
  username: string;
}

interface WithdrawalRequest {
  id: number;
  amount: number;
  payment_method: string;
  payment_details: string;
  status: string;
  created_at: string;
  admin_comment?: string;
}

export default function Withdraw() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');
  const [paymentDetails, setPaymentDetails] = useState('');
  const [loading, setLoading] = useState(false);
  const [requests, setRequests] = useState<WithdrawalRequest[]>([]);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      navigate('/login');
      return;
    }
    setUser(JSON.parse(userStr));
    fetchRequests();
  }, [navigate]);

  const fetchRequests = async () => {
    const userStr = localStorage.getItem('user');
    if (!userStr) return;
    
    const userData = JSON.parse(userStr);
    
    try {
      const response = await fetch(WITHDRAWALS_API, {
        headers: {
          'X-User-Id': userData.id.toString(),
        },
      });

      const data = await response.json();
      if (response.ok) {
        setRequests(data.requests);
      }
    } catch (error) {
      console.error('Error fetching requests:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    const amountNum = parseFloat(amount);
    if (amountNum <= 0 || amountNum > user.balance) {
      toast({
        variant: 'destructive',
        title: 'Ошибка',
        description: 'Некорректная сумма',
      });
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(WITHDRAWALS_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': user.id.toString(),
        },
        body: JSON.stringify({
          amount: amountNum,
          payment_method: paymentMethod,
          payment_details: paymentDetails,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        toast({
          title: 'Заявка создана!',
          description: 'Ваша заявка на вывод отправлена на рассмотрение',
        });
        setAmount('');
        setPaymentMethod('');
        setPaymentDetails('');
        fetchRequests();
      } else {
        toast({
          variant: 'destructive',
          title: 'Ошибка',
          description: data.error || 'Не удалось создать заявку',
        });
      }
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Ошибка',
        description: 'Проблема с подключением',
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
    };
    
    const labels = {
      pending: 'На рассмотрении',
      approved: 'Одобрено',
      completed: 'Выполнено',
      rejected: 'Отклонено',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto p-4 max-w-4xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Вывод средств</h1>
          <Button onClick={() => navigate('/dashboard')} variant="outline">
            <Icon name="ArrowLeft" className="mr-2" size={16} />
            Назад
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Создать заявку</CardTitle>
              <CardDescription>Доступно: {user.balance.toFixed(2)} ₽</CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="amount">Сумма вывода</Label>
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    placeholder="Введите сумму"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="method">Способ вывода</Label>
                  <Select value={paymentMethod} onValueChange={setPaymentMethod} required>
                    <SelectTrigger>
                      <SelectValue placeholder="Выберите способ" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="card">Банковская карта</SelectItem>
                      <SelectItem value="qiwi">QIWI кошелёк</SelectItem>
                      <SelectItem value="yoomoney">ЮMoney</SelectItem>
                      <SelectItem value="paypal">PayPal</SelectItem>
                      <SelectItem value="crypto">Криптовалюта</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="details">Реквизиты</Label>
                  <Input
                    id="details"
                    placeholder="Номер карты / кошелька / адрес"
                    value={paymentDetails}
                    onChange={(e) => setPaymentDetails(e.target.value)}
                    required
                  />
                </div>

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? (
                    <>
                      <Icon name="Loader2" className="mr-2 animate-spin" size={16} />
                      Создание...
                    </>
                  ) : (
                    <>
                      <Icon name="Send" className="mr-2" size={16} />
                      Создать заявку
                    </>
                  )}
                </Button>
              </CardContent>
            </form>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>История заявок</CardTitle>
              <CardDescription>Ваши запросы на вывод средств</CardDescription>
            </CardHeader>
            <CardContent>
              {requests.length === 0 ? (
                <p className="text-center text-gray-500 py-8">Заявок пока нет</p>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {requests.map((req) => (
                    <div key={req.id} className="border rounded-lg p-3 space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold text-lg">{req.amount.toFixed(2)} ₽</div>
                          <div className="text-sm text-gray-600">{req.payment_method}</div>
                        </div>
                        {getStatusBadge(req.status)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(req.created_at).toLocaleString('ru-RU')}
                      </div>
                      {req.admin_comment && (
                        <div className="text-sm bg-gray-50 p-2 rounded">
                          <strong>Комментарий:</strong> {req.admin_comment}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
