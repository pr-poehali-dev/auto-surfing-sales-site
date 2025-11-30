#!/usr/bin/env python3
"""
Aviso Multi-Account Auto-Surf Bot
Программа для автоматического сёрфинга с несколькими аккаунтами одновременно
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


class AvisoBot:
    def __init__(self, account_name):
        self.account_name = account_name
        self.driver = None
        self.is_running = False
        self.stats = {
            'sites_visited': 0,
            'earnings': 0.0,
            'start_time': None
        }
        
    def init_driver(self):
        """Инициализация браузера Chrome"""
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def login(self, username, password):
        """Авторизация на Aviso"""
        try:
            self.driver.get('https://aviso.bz/')
            time.sleep(2)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(3)
            
            if "logout" in self.driver.page_source.lower():
                return True, "Авторизация успешна!"
            else:
                return False, "Ошибка авторизации. Проверьте логин и пароль."
                
        except Exception as e:
            return False, f"Ошибка при входе: {str(e)}"
    
    def start_surfing(self, log_callback):
        """Основной цикл сёрфинга"""
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        try:
            self.driver.get('https://aviso.bz/surf')
            time.sleep(2)
            
            while self.is_running:
                try:
                    start_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-surf-start, .start-surf, button.btn-primary"))
                    )
                    start_button.click()
                    log_callback(f"[{self.account_name}] ▶ Начат просмотр сайта...")
                    
                    time.sleep(2)
                    
                    try:
                        timer = self.driver.find_element(By.CSS_SELECTOR, ".timer, #timer, .countdown")
                        wait_time = 15
                        
                        for i in range(wait_time):
                            if not self.is_running:
                                break
                            time.sleep(1)
                    except NoSuchElementException:
                        time.sleep(15)
                    
                    try:
                        confirm_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-confirm, .confirm-surf, button.btn-success"))
                        )
                        confirm_button.click()
                        
                        self.stats['sites_visited'] += 1
                        self.stats['earnings'] += 0.05
                        log_callback(f"[{self.account_name}] ✅ Сайт #{self.stats['sites_visited']} просмотрен! Заработано: {self.stats['earnings']:.2f}₽")
                        
                    except TimeoutException:
                        log_callback(f"[{self.account_name}] ⚠ Не найдена кнопка подтверждения")
                    
                    time.sleep(3)
                    self.driver.get('https://aviso.bz/surf')
                    time.sleep(2)
                    
                except TimeoutException:
                    log_callback(f"[{self.account_name}] ⚠ Нет доступных сайтов. Ожидание...")
                    time.sleep(30)
                except Exception as e:
                    log_callback(f"[{self.account_name}] ❌ Ошибка: {str(e)}")
                    time.sleep(5)
                    
        except Exception as e:
            log_callback(f"[{self.account_name}] ❌ Критическая ошибка: {str(e)}")
        finally:
            self.is_running = False
            log_callback(f"[{self.account_name}] ⏹ Сёрфинг остановлен")
    
    def stop(self):
        """Остановка бота"""
        self.is_running = False
        if self.driver:
            self.driver.quit()
            self.driver = None


class MultiAccountGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Aviso Multi-Account Bot 🚀")
        self.root.geometry("900x700")
        
        self.accounts = []
        self.bots = {}
        self.config_file = 'accounts_config.json'
        
        self.setup_ui()
        self.load_accounts()
    
    def setup_ui(self):
        """Создание интерфейса"""
        # Заголовок
        header = tk.Frame(self.root, bg='#6366f1', height=70)
        header.pack(fill=tk.X)
        
        title_label = tk.Label(header, text="🚀 Aviso Multi-Account Bot", 
                               font=('Arial', 18, 'bold'), 
                               bg='#6366f1', fg='white')
        title_label.pack(pady=15)
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - управление аккаунтами
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Форма добавления аккаунта
        add_frame = tk.LabelFrame(left_frame, text="Добавить аккаунт", 
                                  font=('Arial', 11, 'bold'), padx=10, pady=10)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(add_frame, text="Название:", font=('Arial', 9)).grid(row=0, column=0, sticky='w', pady=3)
        self.name_entry = tk.Entry(add_frame, width=25, font=('Arial', 9))
        self.name_entry.grid(row=0, column=1, pady=3, padx=5)
        
        tk.Label(add_frame, text="Логин:", font=('Arial', 9)).grid(row=1, column=0, sticky='w', pady=3)
        self.username_entry = tk.Entry(add_frame, width=25, font=('Arial', 9))
        self.username_entry.grid(row=1, column=1, pady=3, padx=5)
        
        tk.Label(add_frame, text="Пароль:", font=('Arial', 9)).grid(row=2, column=0, sticky='w', pady=3)
        self.password_entry = tk.Entry(add_frame, width=25, font=('Arial', 9), show='*')
        self.password_entry.grid(row=2, column=1, pady=3, padx=5)
        
        tk.Button(add_frame, text="➕ Добавить аккаунт", 
                 command=self.add_account, bg='#10b981', fg='white',
                 font=('Arial', 9, 'bold'), cursor='hand2').grid(row=3, column=0, columnspan=2, pady=10)
        
        # Список аккаунтов
        accounts_frame = tk.LabelFrame(left_frame, text="Аккаунты", 
                                       font=('Arial', 11, 'bold'), padx=10, pady=10)
        accounts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar для списка
        scroll = tk.Scrollbar(accounts_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.accounts_listbox = tk.Listbox(accounts_frame, font=('Arial', 9), 
                                           yscrollcommand=scroll.set, height=8)
        self.accounts_listbox.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.accounts_listbox.yview)
        
        # Кнопки управления аккаунтами
        btn_frame = tk.Frame(accounts_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(btn_frame, text="▶ Запустить выбранный", 
                 command=self.start_selected, bg='#3b82f6', fg='white',
                 font=('Arial', 9, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="⏹ Остановить выбранный", 
                 command=self.stop_selected, bg='#ef4444', fg='white',
                 font=('Arial', 9, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="🗑 Удалить", 
                 command=self.delete_selected, bg='#6b7280', fg='white',
                 font=('Arial', 9, 'bold'), cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        # Кнопки массового управления
        mass_frame = tk.Frame(left_frame)
        mass_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(mass_frame, text="▶▶ ЗАПУСТИТЬ ВСЕ", 
                 command=self.start_all, bg='#059669', fg='white',
                 font=('Arial', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        tk.Button(mass_frame, text="⏹⏹ ОСТАНОВИТЬ ВСЕ", 
                 command=self.stop_all, bg='#dc2626', fg='white',
                 font=('Arial', 10, 'bold'), cursor='hand2').pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Правая панель - логи и статистика
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right_frame.pack_propagate(False)
        
        # Общая статистика
        stats_frame = tk.LabelFrame(right_frame, text="Общая статистика", 
                                    font=('Arial', 11, 'bold'), padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.total_stats_label = tk.Label(stats_frame, text="Активных: 0 | Всего просмотров: 0 | Заработано: 0.00₽", 
                                          font=('Arial', 9), fg='#059669')
        self.total_stats_label.pack()
        
        # Логи
        log_frame = tk.LabelFrame(right_frame, text="Логи", 
                                  font=('Arial', 11, 'bold'), padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, font=('Consolas', 8), 
                                                   bg='#1e293b', fg='#e2e8f0', wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        tk.Button(log_frame, text="🗑 Очистить логи", 
                 command=lambda: self.log_text.delete(1.0, tk.END),
                 font=('Arial', 8), cursor='hand2').pack(pady=(5, 0))
        
        # Запуск обновления статистики
        self.update_stats()
    
    def add_account(self):
        """Добавление нового аккаунта"""
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not name or not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        if any(acc['name'] == name for acc in self.accounts):
            messagebox.showerror("Ошибка", f"Аккаунт '{name}' уже существует!")
            return
        
        account = {
            'name': name,
            'username': username,
            'password': password,
            'status': 'stopped'
        }
        
        self.accounts.append(account)
        self.save_accounts()
        self.refresh_accounts_list()
        
        self.name_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        
        self.log(f"✅ Аккаунт '{name}' добавлен")
    
    def delete_selected(self):
        """Удаление выбранного аккаунта"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите аккаунт для удаления!")
            return
        
        idx = selection[0]
        account = self.accounts[idx]
        
        if account['name'] in self.bots and self.bots[account['name']].is_running:
            messagebox.showerror("Ошибка", "Сначала остановите аккаунт!")
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить аккаунт '{account['name']}'?"):
            self.accounts.pop(idx)
            self.save_accounts()
            self.refresh_accounts_list()
            self.log(f"🗑 Аккаунт '{account['name']}' удалён")
    
    def start_selected(self):
        """Запуск выбранного аккаунта"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите аккаунт для запуска!")
            return
        
        idx = selection[0]
        account = self.accounts[idx]
        self.start_account(account)
    
    def stop_selected(self):
        """Остановка выбранного аккаунта"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите аккаунт для остановки!")
            return
        
        idx = selection[0]
        account = self.accounts[idx]
        self.stop_account(account)
    
    def start_all(self):
        """Запуск всех аккаунтов"""
        if not self.accounts:
            messagebox.showwarning("Внимание", "Добавьте хотя бы один аккаунт!")
            return
        
        for account in self.accounts:
            if account['status'] == 'stopped':
                self.start_account(account)
                time.sleep(2)
    
    def stop_all(self):
        """Остановка всех аккаунтов"""
        for account in self.accounts:
            if account['status'] == 'running':
                self.stop_account(account)
    
    def start_account(self, account):
        """Запуск конкретного аккаунта"""
        if account['status'] == 'running':
            messagebox.showinfo("Инфо", f"Аккаунт '{account['name']}' уже работает!")
            return
        
        def run():
            bot = AvisoBot(account['name'])
            self.bots[account['name']] = bot
            
            self.log(f"[{account['name']}] 🚀 Инициализация браузера...")
            bot.init_driver()
            
            self.log(f"[{account['name']}] 🔐 Авторизация...")
            success, message = bot.login(account['username'], account['password'])
            
            if success:
                self.log(f"[{account['name']}] ✅ {message}")
                account['status'] = 'running'
                self.refresh_accounts_list()
                bot.start_surfing(self.log)
            else:
                self.log(f"[{account['name']}] ❌ {message}")
                bot.driver.quit()
            
            account['status'] = 'stopped'
            self.refresh_accounts_list()
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop_account(self, account):
        """Остановка конкретного аккаунта"""
        if account['name'] in self.bots:
            bot = self.bots[account['name']]
            bot.stop()
            self.log(f"[{account['name']}] ⏹ Остановка...")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def refresh_accounts_list(self):
        """Обновление списка аккаунтов"""
        self.accounts_listbox.delete(0, tk.END)
        for account in self.accounts:
            status_icon = "🟢" if account['status'] == 'running' else "⚪"
            self.accounts_listbox.insert(tk.END, f"{status_icon} {account['name']} ({account['username']})")
    
    def update_stats(self):
        """Обновление статистики"""
        active = sum(1 for acc in self.accounts if acc['status'] == 'running')
        total_visits = sum(bot.stats['sites_visited'] for bot in self.bots.values())
        total_earnings = sum(bot.stats['earnings'] for bot in self.bots.values())
        
        self.total_stats_label.config(
            text=f"Активных: {active} | Всего просмотров: {total_visits} | Заработано: {total_earnings:.2f}₽"
        )
        
        self.root.after(1000, self.update_stats)
    
    def save_accounts(self):
        """Сохранение аккаунтов в файл"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, ensure_ascii=False, indent=2)
    
    def load_accounts(self):
        """Загрузка аккаунтов из файла"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.accounts = json.load(f)
                for acc in self.accounts:
                    acc['status'] = 'stopped'
                self.refresh_accounts_list()


if __name__ == "__main__":
    root = tk.Tk()
    app = MultiAccountGUI(root)
    root.mainloop()
