# smsd-gammu-daemon

> Настройка и запуск Gammu SMS Daemon на Raspberry Pi/Orange Pi с использованием модема 3G/4G от Huawei

## 📦 Содержание

- [Преамбула](#-преамбула)
- [У нас было...](#-у-нас-было)
- [Установка Gammu вручную](#-установка-gammu-вручную)
  - [Шаг 1: Подключение модема](#шаг-1-подключение-модема)
  - [Шаг 2: Установка Gammu](#шаг-2-установка-gammu)
  - [Шаг 3: Конфигурация Gammu](#шаг-3-конфигурация-gammu)
  - [Шаг 4: Запуск и тестирование](#шаг-4-запуск-и-тестирование)
- [Автоматизация с Ansible](#автоматизация-с-ansible)
  - [Шаг 1: Установка Ansible](#шаг-1-установка-ansible)
  - [Шаг 2: Настройка Ansible Playbook](#шаг-2-настройка-ansible-playbook)
  - [Шаг 3: Запуск Playbook](#шаг-3-запуск-playbook)
- [Полезные советы и рекомендации](#полезные-советы-и-рекомендации)
- [Ошибки и устранение неполадок](#ошибки-и-устранение-неполадок)
  - [udev правила](#)
- [Лицензия](#лицензия)

## 📝 Преамбула

Однажды передо мной возникла задача — получать СМС на SIM-карту, которую не хотелось бы носить с собой в мобильном устройстве. В моем случае это была SIM-карта Казахстана, а также потребность в получении пуш-уведомлений от банков. Проанализировав ситуацию и имея под рукой старый 3G-модем и недавно приобретенную `Orange Pi`, я решил настроить систему для получения СМС и пересылки их в **Telegram**.

Ключом к решению этой задачи стал Gammu SMS Daemon, который позволяет отправлять и получать сообщения на вашем устройстве. В этом руководстве я шаг за шагом покажу, как я это реализовал, а также постараюсь автоматизировать процесс с помощью **Ansible**.

## ⚙️ У нас было...

![у-нас-было](https://avatars.mds.yandex.net/get-vthumb/2455229/ec6a9a38a6eef596fa8105ce9c74b794/800x450)

Итак, представьте себе: один **одноплатный компьютер**, что-то вроде старого друга, который лежал в углу, собирая пыль. Один старый операторский модем **Мегафон Е173** — тот самый, который уже давно не использовался, но всё ещё тянет за собой какие-то воспоминания о старых временах связи. И, конечно же, великое и всепоглощающее желание **автоматизировать** процесс. Всё это вместе — готовая сцена для небольшого, но эпического приключения.


## 🚀 Установка Gammu вручную

### Шаг 0: Разблокировка

Если ваш модем операторский — как и в моем случае, его нужно научить тайному кунг-фу — читать SIM-карты других операторов. Этот процесс оказался тривиальным для моей модели, ведь под личиной **Мегафон Е173** скрывается не кто иной, как **HUAWEI E173** — древнейший 3G-свисток, который идеально подходил для моих задач. Как сменить его преданность Мегафону, можно найти [на небезызвестном форуме](https://4pda.to/forum/index.php?showtopic=256400).

### Шаг 1: Подключение модема

1. Вставьте модем Huawei в USB-порт вашего устройства.
2. Убедитесь, что модем определяется системой, используя команду:

   ```bash
   lsusb
   ```

  В ответ вы должны получить что-то наподобие:

  ```bash
  Bus 008 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
  Bus 007 Device 003: ID 12d1:1001 Huawei Technologies Co., Ltd. E161/E169/E620/E800 HSDPA Modem
  Bus 007 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
  ```

  Прекрасно модем определился - мы запомним из данного вывода manufacture id данного устройства - `12d1:1001`. `12d1` — это код поставщика для Huawei, а строка, идущая за этим кодом (в моём случае — `1001`) — это ID продукта.
  Если система, после подключения модема, создаст /dev/ttyUSB0, это значит, что всё сделано правильно. Проверить это можем с помощью команд:

   ```bash
   dmesg | grep tty
[287645.840210] usb 7-1: GSM modem (1-port) converter now attached to ttyUSB1
[287645.876674] usb 7-1: GSM modem (1-port) converter now attached to ttyUSB2
[287645.913216] usb 7-1: GSM modem (1-port) converter now attached to ttyUSB3

   ls -al /dev/ttyUSB*
crw-rw---- 1 root dialout 188, 1 Feb  6 22:15 /dev/ttyUSB1
crw-rw---- 1 root dialout 188, 2 Feb  6 22:15 /dev/ttyUSB2
crw-rw---- 1 root dialout 188, 3 Feb 16 23:19 /dev/ttyUSB3
   ```

> [!NOTE]
> После подключения модема стоит сразу настроить udev правило для него - дабы зафиксировать ttyID. Подробнее: 

После этого аппаратная часть нашего проекта — Pi и модем — готова к дальнейшей работе.

### Шаг 2: Установка gammu

1. Чаще всего одноплатники поставляются на Debian/Ubuntu подобных дистрибутивах - поэтому ставим пакеты для gammu и используя пакетный менеджер apt. Хорошим тоном будет обновить репозитории и ОС:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. И установка самих пакетов:
   ```bash
   sudo apt install gammu gammu-smsd -y
   ```

### Шаг 3: Конфигурация Gammu

1. Gammu обладает широким спектром возможностей по взаимодействию с модемами и телефонами. Нам же нужен тривиальный функционал обработки SMS сообщений. Конфигурационный файл тривиален:

Лежит по пути - `/etc/gammu-smsdrc`
```shell
# Configuration file for Gammu SMS Daemon - подробнее https://docs.gammu.org/config/

[gammu]
port = /dev/sms # точка подключения к нашему модему, мы настроили ее после подключения модема. Можно использовать ttyUSB*, но могут быть коллизии — см. Полезные советы и рекомендации
connection = at # тип подключения к модему (AT-команды)

[smsd]
service = files # режим работы — сохранять сообщения в локальные файлы
logfile = syslog # путь для логирования — syslog (системный журнал)
debuglevel = 1 # уровень детализации логов (1 — минимальный, 255 — максимальный)
SMSC = +77476934219 # номер центра SMS-сообщений (SMSC), необходим для отправки SMS
CheckSecurity = 0 # отключить проверку безопасности PIN-кода SIM-карты

RunOnReceive = /opt/sms-forwarder/src/main.py # путь к скрипту, который запускается при получении SMS

inboxpath = /var/spool/gammu/inbox/ # папка для входящих SMS
outboxpath = /var/spool/gammu/outbox/ # папка для SMS, подготовленных к отправке
sentsmspath = /var/spool/gammu/sent/ # папка для успешно отправленных SMS
errorsmspath = /var/spool/gammu/error/ # папка для сообщений, которые не удалось отправить
```

2. После заполнения конфигурационного файла можем проверить работу модема и связь утилиты и нашего модема. Если всё нормально — в ответ вы получите примерно следующее:

  ```bash
  gammu -c gammu-smsdrc identify
Device               : /dev/sms
Manufacturer         : Huawei
Model                : E173 (E173)
Firmware             : 11.126.16.17.209
IMEI                 : 863448212120472
SIM IMSI             : 401770091187972
  ```

## ⚙️ Автоматизация с Ansible
## 💡 Полезные советы и рекомендации

### Настройка udev правил

У модемов есть свойство - менять свой ttyd в зависимости от фазы луны, солнцестояния и курс доллара. Хорошим решением будет зафикисровать этот самый ttyd с помощью правил udev. При подключении модема к одноплатнику мы выяснили manufacture id нашего устройства.

  ```bash
  Bus 008 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
  Bus 007 Device 003: ID 12d1:1001 Huawei Technologies Co., Ltd. E161/E169/E620/E800 HSDPA Modem
  Bus 007 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
  ```

Теперь создадим файл по пути `/etc/udev/rules.d/55-USB-modems.rules` со следующим содержанием:

  ```bash
# idVendor           0x12d1 Huawei Technologies Co., Ltd.
# idProduct          0x1001 E169/E620/E800 HSDPA Modem
SUBSYSTEM=="tty", ATTRS{idVendor}=="12d1", ATTRS{idProduct}== "1001", SYMLINK+="sms"
  ```

Следующим правилом мы говорим что устройство вендора Huawei и пределенным id стоит вешать на симлинк `/dev/sms`.

Теперь выполним релоад данных правил:

  ```bash
  udevadm control --reload-rules
  udevadm trigger
  ```

По пути `/dev/sms` мы должны заблюдать симлинк на ttyd от модема:

  ```bash
  ls -hal /dev/sms
  lrwxrwxrwx 1 root root 7 Feb 17 10:41 /dev/sms -> ttyUSB3
  ```

## ⚠️ Ошибки и устранение неполадок