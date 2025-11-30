#!/usr/bin/env python3
"""
Aviso Auto-Surf Bot
Программа для автоматического сёрфинга на буксе Aviso.ru
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
from selenium.webdriver.chrome.service import Service


class AvisoBot:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.stats = {
            'sites_visited': 0,
            'earnings': 0.0,
            'start_time': None
        }
        self.config_file = 'config.json'
        
    def load_config(self):
        """Загрузка конфигурации"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_config(self, username, password):
        """Сохранение конфигурации"""
        config = {'username': username, 'password': password}
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
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
            
            # Ищем поля логина
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Нажимаем кнопку входа
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(3)
            
            # Проверяем успешность входа
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
            # Переход на страницу сёрфинга
            self.driver.get('https://aviso.bz/surf')
            time.sleep(2)
            
            while self.is_running:
                try:
                    # Ищем кнопку начала просмотра сайта
                    start_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-surf-start, .start-surf, button.btn-primary"))
                    )
                    start_button.click()
                    log_callback("▶ Начат просмотр сайта...")
                    
                    # Ждём таймер (обычно 10-30 секунд)
                    time.sleep(2)
                    
                    # Ищем таймер и ждём его окончания
                    try:
                        timer = self.driver.find_element(By.CSS_SELECTOR, ".timer, #timer, .countdown")
                        wait_time = 15  # Примерное время ожидания
                        
                        for i in range(wait_time):
                            if not self.is_running:
                                break
                            log_callback(f"⏳ Ожидание: {wait_time - i} сек...")
                            time.sleep(1)
                    except NoSuchElementException:
                        time.sleep(15)
                    
                    # Ищем кнопку подтверждения просмотра
                    try:
                        confirm_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-confirm, .confirm-surf, button.btn-success"))
                        )
                        confirm_button.click()
                        
                        self.stats['sites_visited'] += 1
                        self.stats['earnings'] += 0.05  # Примерная стоимость за просмотр
                        log_callback(f"✅ Сайт #{self.stats['sites_visited']} просмотрен! Заработано: {self.stats['earnings']:.2f}₽")
                        
                    except TimeoutException:
                        log_callback("⚠ Не найдена кнопка подтверждения")
                    
                    # Пауза между просмотрами
                    time.sleep(3)
                    
                    # Возврат на страницу сёрфинга
                    self.driver.get('https://aviso.bz/surf')
                    time.sleep(2)
                    
                except TimeoutException:
                    log_callback("⚠ Нет доступных сайтов для просмотра. Ожидание...")
                    time.sleep(30)
                except Exception as e:
                    log_callback(f"❌ Ошибка: {str(e)}")
                    time.sleep(5)
                    
        except Exception as e:
            log_callback(f"❌ Критическая ошибка: {str(e)}")
        finally:
            self.is_running = False
            log_callback("⏹ Сёрфинг остановлен")
    
    def stop(self):
        """Остановка бота"""
        self.is_running = False
        if self.driver:
            self.driver.quit()
            self.driver = None


class AvisoBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Aviso Auto-Surf Bot 🚀")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        self.bot = AvisoBot()
        self.setup_ui()
        
        # Загрузка сохранённых данных
        config = self.bot.load_config()
        if config:
            self.username_entry.insert(0, config.get('username', ''))
            self.password_entry.insert(0, config.get('password', ''))
    
    def setup_ui(self):
        """Создание интерфейса"""
        # Заголовок
        header = tk.Frame(self.root, bg='#6366f1', height=80)
        header.pack(fill=tk.X)
        
        title_label = tk.Label(header, text="🚀 Aviso Auto-Surf Bot", 
                               font=('Arial', 20, 'bold'), 
                               bg='#6366f1', fg='white')
        title_label.pack(pady=20)
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Форма входа
        login_frame = tk.LabelFrame(main_frame, text="Данные для входа", 
                                    font=('Arial', 12, 'bold'), padx=10, pady=10)
        login_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(login_frame, text="Логин:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.username_entry = tk.Entry(login_frame, width=40, font=('Arial', 10))
        self.username_entry.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(login_frame, text="Пароль:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.password_entry = tk.Entry(login_frame, width=40, font=('Arial', 10), show='*')
        self.password_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Кнопки управления
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = tk.Button(control_frame, text="▶ ЗАПУСТИТЬ", 
                                      command=self.start_bot,
                                      bg='#10b981', fg='white', 
                                      font=('Arial', 12, 'bold'),
                                      width=20, height=2)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(control_frame, text="⏹ ОСТАНОВИТЬ", 
                                     command=self.stop_bot,
                                     bg='#ef4444', fg='white', 
                                     font=('Arial', 12, 'bold'),
                                     width=20, height=2,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Статистика
        stats_frame = tk.LabelFrame(main_frame, text="Статистика", 
                                    font=('Arial', 12, 'bold'), padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.sites_label = tk.Label(stats_frame, text="Просмотрено сайтов: 0", 
                                    font=('Arial', 11))
        self.sites_label.pack(anchor='w', pady=2)
        
        self.earnings_label = tk.Label(stats_frame, text="Заработано: 0.00₽", 
                                       font=('Arial', 11))
        self.earnings_label.pack(anchor='w', pady=2)
        
        self.time_label = tk.Label(stats_frame, text="Время работы: 00:00:00", 
                                   font=('Arial', 11))
        self.time_label.pack(anchor='w', pady=2)
        
        # Лог
        log_frame = tk.LabelFrame(main_frame, text="Лог работы", 
                                  font=('Arial', 12, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  font=('Consolas', 9),
                                                  bg='#1e1e1e', fg='#00ff00')
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log("Программа запущена. Введите данные и нажмите ЗАПУСТИТЬ.")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_stats(self):
        """Обновление статистики"""
        if self.bot.is_running:
            self.sites_label.config(text=f"Просмотрено сайтов: {self.bot.stats['sites_visited']}")
            self.earnings_label.config(text=f"Заработано: {self.bot.stats['earnings']:.2f}₽")
            
            if self.bot.stats['start_time']:
                elapsed = datetime.now() - self.bot.stats['start_time']
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.time_label.config(text=f"Время работы: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            self.root.after(1000, self.update_stats)
    
    def start_bot(self):
        """Запуск бота"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните логин и пароль!")
            return
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log("Запуск бота...")
        
        # Сохранение данных
        self.bot.save_config(username, password)
        
        def run():
            try:
                self.log("Инициализация браузера...")
                self.bot.init_driver()
                
                self.log("Авторизация на Aviso...")
                success, message = self.bot.login(username, password)
                self.log(message)
                
                if success:
                    self.log("Начинаем сёрфинг!")
                    self.update_stats()
                    self.bot.start_surfing(self.log)
                else:
                    self.stop_button.config(state=tk.DISABLED)
                    self.start_button.config(state=tk.NORMAL)
                    self.bot.stop()
                    
            except Exception as e:
                self.log(f"❌ Ошибка: {str(e)}")
                self.stop_button.config(state=tk.DISABLED)
                self.start_button.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop_bot(self):
        """Остановка бота"""
        self.log("Остановка бота...")
        self.bot.stop()
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
    
    def on_closing(self):
        """Обработка закрытия окна"""
        if self.bot.is_running:
            if messagebox.askokcancel("Выход", "Бот работает. Остановить и выйти?"):
                self.bot.stop()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = AvisoBotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
