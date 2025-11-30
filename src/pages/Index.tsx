import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import Icon from '@/components/ui/icon';

const Index = () => {
  const [onlineCount, setOnlineCount] = useState(247);
  const [buyersCount, setBuyersCount] = useState(1342);
  const [showExitPopup, setShowExitPopup] = useState(false);
  const [promoCode, setPromoCode] = useState('');
  const [discountApplied, setDiscountApplied] = useState(false);
  const [formBuyersCount, setFormBuyersCount] = useState(89);

  useEffect(() => {
    const onlineInterval = setInterval(() => {
      setOnlineCount(prev => prev + Math.floor(Math.random() * 3) - 1);
    }, 5000);

    const buyersInterval = setInterval(() => {
      setBuyersCount(prev => prev + 1);
      setFormBuyersCount(prev => prev + 1);
    }, 12000);

    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY <= 0) {
        setShowExitPopup(true);
      }
    };

    document.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      clearInterval(onlineInterval);
      clearInterval(buyersInterval);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  const handlePromoCode = () => {
    if (promoCode.toUpperCase() === 'PROMO50') {
      setDiscountApplied(true);
    }
  };

  const finalPrice = discountApplied ? 345 : 690;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="fixed top-4 right-4 z-50 flex gap-3">
        <Badge className="bg-secondary text-white px-4 py-2 text-sm font-body animate-pulse">
          <Icon name="Users" size={16} className="mr-2" />
          Онлайн: {onlineCount}
        </Badge>
        <Badge className="bg-accent text-white px-4 py-2 text-sm font-body animate-pulse">
          <Icon name="ShoppingCart" size={16} className="mr-2" />
          Купили: {buyersCount}
        </Badge>
      </div>

      <div className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-center mb-8">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary via-secondary to-accent flex items-center justify-center animate-pulse">
              <Icon name="Rocket" size={48} className="text-white" />
            </div>
            <div className="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <Icon name="Zap" size={16} className="text-white" />
            </div>
          </div>
        </div>

        <div className="text-center mb-16 animate-fade-in">
          <h1 className="font-heading text-5xl md:text-7xl font-black text-white mb-4 leading-tight">
            АВТОБОТ ДЛЯ AVISO
            <br />
            <span className="bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
              ЗАРАБАТЫВАЙ НА АВТОПИЛОТЕ
            </span>
          </h1>
          <p className="font-body text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Автоматический заработок на автосёрфинге Aviso без вашего участия. Бот работает 24/7!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              size="lg" 
              className="bg-primary hover:bg-primary/90 text-white text-xl px-12 py-8 rounded-full font-heading font-bold shadow-2xl animate-pulse transition-transform hover:scale-105"
              onClick={() => document.getElementById('buy-section')?.scrollIntoView({ behavior: 'smooth' })}
            >
              <Icon name="Zap" size={24} className="mr-2" />
              ПОЛУЧИТЬ ДОСТУП СЕЙЧАС
            </Button>
            <Badge className="bg-red-600 text-white px-6 py-3 text-lg font-heading animate-bounce">
              <Icon name="Clock" size={20} className="mr-2" />
              Осталось 7 мест по акции!
            </Badge>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {[
            { icon: 'TrendingUp', title: '1500-3000₽/день', desc: 'Все зависит от вашего компьютера' },
            { icon: 'Clock', title: '24/7 работа', desc: 'Без вашего участия' },
            { icon: 'Shield', title: 'Безопасно', desc: 'Защита аккаунта' }
          ].map((item, idx) => (
            <Card key={idx} className="bg-white/10 backdrop-blur-lg border-2 border-white/20 p-6 text-center transition-transform hover:scale-105 animate-fade-in">
              <div className="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center mx-auto mb-4">
                <Icon name={item.icon as any} size={32} className="text-white" />
              </div>
              <h3 className="font-heading text-2xl font-bold text-white mb-2">{item.title}</h3>
              <p className="font-body text-gray-300">{item.desc}</p>
            </Card>
          ))}
        </div>

        <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 md:p-12 mb-16 border-2 border-white/20">
          <h2 className="font-heading text-4xl font-black text-white mb-8 text-center">
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              КАК ЭТО РАБОТАЕТ?
            </span>
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { num: '1', icon: 'Download', title: 'Получаешь бота', desc: 'После оплаты получаешь доступ в Telegram' },
              { num: '2', icon: 'Settings', title: 'Настраиваешь', desc: 'Вводишь данные от Aviso за 2 минуты' },
              { num: '3', icon: 'Play', title: 'Запускаешь', desc: 'Бот начинает работать автоматически' },
              { num: '4', icon: 'DollarSign', title: 'Получаешь деньги', desc: 'Средства поступают на твой счет' }
            ].map((step, idx) => (
              <div key={idx} className="relative animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
                <div className="bg-gradient-to-br from-accent to-primary rounded-2xl p-6 text-center h-full">
                  <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mx-auto mb-4 font-heading text-2xl font-black text-primary">
                    {step.num}
                  </div>
                  <Icon name={step.icon as any} size={40} className="text-white mx-auto mb-4" />
                  <h4 className="font-heading text-xl font-bold text-white mb-2">{step.title}</h4>
                  <p className="font-body text-sm text-white/90">{step.desc}</p>
                </div>
                {idx < 3 && (
                  <Icon name="ArrowRight" size={32} className="hidden md:block absolute top-1/2 -right-4 text-primary" />
                )}
              </div>
            ))}
          </div>
        </div>

        <div id="buy-section" className="bg-gradient-to-br from-primary via-secondary to-accent rounded-3xl p-8 md:p-12 mb-16 shadow-2xl animate-scale-in">
          <div className="text-center mb-8">
            <Badge className="bg-white text-primary px-6 py-3 text-lg font-heading mb-4 animate-bounce">
              <Icon name="Flame" size={20} className="mr-2" />
              Сегодня купили: {formBuyersCount} человек
            </Badge>
            <h2 className="font-heading text-4xl md:text-5xl font-black text-white mb-4">
              ПОЛУЧИ ДОСТУП К БОТУ
            </h2>
            <div className="flex items-center justify-center gap-4 mb-4">
              <span className="font-heading text-3xl text-white line-through opacity-70">690₽</span>
              <span className="font-heading text-6xl font-black text-white">{finalPrice}₽</span>
            </div>
            <p className="font-body text-xl text-white/90">Разовый платеж. Без подписок!</p>
          </div>

          <div className="max-w-md mx-auto bg-white/20 backdrop-blur-lg rounded-2xl p-6 mb-6">
            <label className="font-body text-white mb-2 block font-bold">Есть промокод?</label>
            <div className="flex gap-2">
              <Input 
                placeholder="Введи промокод" 
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
                className="bg-white/90 border-0 font-body"
              />
              <Button 
                onClick={handlePromoCode}
                className="bg-white text-primary hover:bg-white/90 font-heading font-bold"
              >
                Применить
              </Button>
            </div>
            {discountApplied && (
              <Badge className="bg-green-500 text-white mt-2 px-4 py-2 font-body">
                <Icon name="CheckCircle" size={16} className="mr-2" />
                Скидка 50% активирована!
              </Badge>
            )}
          </div>

          <div className="flex flex-col gap-4 max-w-md mx-auto">
            <Button 
              size="lg"
              className="bg-white text-primary hover:bg-white/90 text-2xl px-12 py-8 rounded-full font-heading font-black shadow-2xl transition-transform hover:scale-105 w-full"
              onClick={() => window.open('https://t.me/Progasoft_bot?start=item_8487', '_blank')}
            >
              <Icon name="ShoppingCart" size={28} className="mr-3" />
              КУПИТЬ ЗА {finalPrice}₽
            </Button>
            <Button 
              size="lg"
              variant="outline"
              className="bg-white/20 border-2 border-white text-white hover:bg-white hover:text-primary text-xl px-8 py-6 rounded-full font-heading font-bold w-full"
              onClick={() => window.open(`https://t.me/Progasoft_bot?start=promo_Promo50`, '_blank')}
            >
              <Icon name="Gift" size={24} className="mr-2" />
              С ПРОМОКОДОМ PROMO50
            </Button>
          </div>
        </div>

        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-lg px-6 py-3 rounded-full">
            <Icon name="Lock" size={20} className="text-green-400" />
            <span className="font-body text-white">Безопасная оплата через Telegram</span>
          </div>
        </div>
      </div>

      <Dialog open={showExitPopup} onOpenChange={setShowExitPopup}>
        <DialogContent className="bg-gradient-to-br from-red-600 to-orange-600 border-4 border-yellow-400 max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-heading text-4xl font-black text-white text-center mb-4">
              <Icon name="AlertCircle" size={48} className="mx-auto mb-2 text-yellow-400 animate-bounce" />
              СТОЙ! НЕ УХОДИ!
            </DialogTitle>
            <DialogDescription className="text-white text-center space-y-4">
              <p className="font-body text-2xl font-bold">
                Специально для тебя скидка 50%!
              </p>
              <div className="bg-white/20 backdrop-blur-lg rounded-xl p-6">
                <div className="flex items-center justify-center gap-4 mb-4">
                  <span className="font-heading text-3xl text-white line-through opacity-70">690₽</span>
                  <span className="font-heading text-6xl font-black text-yellow-400">345₽</span>
                </div>
                <p className="font-body text-lg text-white mb-4">
                  Используй промокод: <strong className="text-yellow-400 text-2xl">PROMO50</strong>
                </p>
              </div>
              <Button 
                size="lg"
                className="bg-yellow-400 text-gray-900 hover:bg-yellow-300 text-2xl px-12 py-8 rounded-full font-heading font-black w-full shadow-2xl animate-pulse"
                onClick={() => {
                  setShowExitPopup(false);
                  window.open('https://t.me/Progasoft_bot?start=promo_Promo50', '_blank');
                }}
              >
                <Icon name="Gift" size={28} className="mr-3" />
                ЗАБРАТЬ СКИДКУ!
              </Button>
              <p className="font-body text-sm text-white/80">
                Предложение действует только сейчас!
              </p>
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Index;