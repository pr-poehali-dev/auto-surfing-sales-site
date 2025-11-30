import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import Icon from '@/components/ui/icon';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const WITHDRAWALS_API = 'https://functions.poehali.dev/c3d3ef57-3cb0-4ed9-a0b6-41ecbde6c6e9';

interface User {
  id: number;
  is_admin: boolean;
}

interface WithdrawalRequest {
  id: number;
  user_id: number;
  username: string;
  email: string;
  amount: number;
  payment_method: string;
  payment_details: string;
  status: string;
  created_at: string;
  admin_comment?: string;
}

export default function Admin() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [requests, setRequests] = useState<WithdrawalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRequest, setSelectedRequest] = useState<WithdrawalRequest | null>(null);
  const [adminComment, setAdminComment] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      navigate('/login');
      return;
    }
    
    const userData = JSON.parse(userStr);
    if (!userData.is_admin) {
      toast({
        variant: 'destructive',
        title: 'Доступ запрещён',
        description: 'У вас нет прав администратора',
      });
      navigate('/dashboard');
      return;
    }
    
    setUser(userData);
    fetchRequests(userData.id);
  }, [navigate, toast]);

  const fetchRequests = async (userId: number) => {
    try {
      const response = await fetch(WITHDRAWALS_API, {
        headers: {
          'X-User-Id': userId.toString(),
        },
      });

      const data = await response.json();
      if (response.ok) {
        setRequests(data.requests);
      }
    } catch (error) {
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (requestId: number, newStatus: string) => {
    if (!user) return;

    setProcessing(true);

    try {
      const response = await fetch(WITHDRAWALS_API, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': user.id.toString(),
        },
        body: JSON.stringify({
          request_id: requestId,
          status: newStatus,
          admin_comment: adminComment,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        toast({
          title: 'Статус обновлён!',
          description: data.message,
        });
        fetchRequests(user.id);
        setSelectedRequest(null);
        setAdminComment('');
      } else {
        toast({
          variant: 'destructive',
          title: 'Ошибка',
          description: data.error || 'Не удалось обновить статус',
        });
      }
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Ошибка',
        description: 'Проблема с подключением',
      });
    } finally {
      setProcessing(false);
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
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status as keyof typeof styles]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Icon name="Loader2" className="animate-spin" size={40} />
      </div>
    );
  }

  if (!user) return null;

  const pendingCount = requests.filter(r => r.status === 'pending').length;
  const approvedCount = requests.filter(r => r.status === 'approved').length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto p-4 max-w-7xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Icon name="Shield" size={32} />
              Админ-панель
            </h1>
            <p className="text-gray-600">Управление заявками на вывод</p>
          </div>
          <Button onClick={() => navigate('/dashboard')} variant="outline">
            <Icon name="ArrowLeft" className="mr-2" size={16} />
            В кабинет
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-3 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">На рассмотрении</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-600">{pendingCount}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Одобрено</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{approvedCount}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Всего заявок</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">{requests.length}</div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Все заявки на вывод</CardTitle>
            <CardDescription>Обработка запросов пользователей</CardDescription>
          </CardHeader>
          <CardContent>
            {requests.length === 0 ? (
              <p className="text-center text-gray-500 py-8">Заявок пока нет</p>
            ) : (
              <div className="space-y-3">
                {requests.map((req) => (
                  <div key={req.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="font-bold text-xl text-green-600">{req.amount.toFixed(2)} ₽</div>
                          {getStatusBadge(req.status)}
                        </div>
                        <div className="text-sm space-y-1">
                          <div><strong>Пользователь:</strong> {req.username} ({req.email})</div>
                          <div><strong>Способ:</strong> {req.payment_method}</div>
                          <div><strong>Реквизиты:</strong> {req.payment_details}</div>
                          <div className="text-gray-500">
                            <strong>Создано:</strong> {new Date(req.created_at).toLocaleString('ru-RU')}
                          </div>
                        </div>
                      </div>
                      
                      {req.status === 'pending' && (
                        <div className="flex gap-2 ml-4">
                          <Button
                            size="sm"
                            variant="default"
                            onClick={() => setSelectedRequest(req)}
                          >
                            <Icon name="CheckCircle" className="mr-1" size={14} />
                            Одобрить
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => {
                              setSelectedRequest(req);
                              setAdminComment('');
                            }}
                          >
                            <Icon name="XCircle" className="mr-1" size={14} />
                            Отклонить
                          </Button>
                        </div>
                      )}
                      
                      {req.status === 'approved' && (
                        <Button
                          size="sm"
                          variant="default"
                          className="bg-green-600 hover:bg-green-700"
                          onClick={() => {
                            setSelectedRequest(req);
                            setAdminComment('Выплата завершена');
                          }}
                        >
                          <Icon name="Check" className="mr-1" size={14} />
                          Завершить
                        </Button>
                      )}
                    </div>
                    
                    {req.admin_comment && (
                      <div className="text-sm bg-gray-50 p-3 rounded mt-2">
                        <strong>Комментарий админа:</strong> {req.admin_comment}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={!!selectedRequest} onOpenChange={() => setSelectedRequest(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Обработка заявки #{selectedRequest?.id}</DialogTitle>
            <DialogDescription>
              Сумма: {selectedRequest?.amount.toFixed(2)} ₽ | Пользователь: {selectedRequest?.username}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Комментарий (необязательно)</label>
              <Textarea
                placeholder="Введите комментарий для пользователя..."
                value={adminComment}
                onChange={(e) => setAdminComment(e.target.value)}
                rows={3}
              />
            </div>
            
            <div className="flex gap-2 justify-end">
              {selectedRequest?.status === 'pending' && (
                <>
                  <Button
                    variant="default"
                    onClick={() => handleUpdateStatus(selectedRequest.id, 'approved')}
                    disabled={processing}
                  >
                    {processing ? (
                      <Icon name="Loader2" className="mr-2 animate-spin" size={16} />
                    ) : (
                      <Icon name="CheckCircle" className="mr-2" size={16} />
                    )}
                    Одобрить
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => handleUpdateStatus(selectedRequest.id, 'rejected')}
                    disabled={processing}
                  >
                    <Icon name="XCircle" className="mr-2" size={16} />
                    Отклонить
                  </Button>
                </>
              )}
              
              {selectedRequest?.status === 'approved' && (
                <Button
                  variant="default"
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => handleUpdateStatus(selectedRequest.id, 'completed')}
                  disabled={processing}
                >
                  {processing ? (
                    <Icon name="Loader2" className="mr-2 animate-spin" size={16} />
                  ) : (
                    <Icon name="Check" className="mr-2" size={16} />
                  )}
                  Завершить выплату
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
