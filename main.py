import os
import sqlite3
import threading
from datetime import datetime

import telebot
from telebot import types


# ============================================================
# AsklyBux Admin Panel Bot
# Python 3.11 + pyTelegramBotAPI + SQLite + Polling
# ============================================================

# Add token manually here or through Railway variable ADMINBOTTOKEN.
ADMINBOTTOKEN = ""

# Admin Telegram user ID.
ADMINID = 8907284640

TOKEN = os.getenv("ADMINBOTTOKEN", ADMINBOTTOKEN)

if not TOKEN:
    raise ValueError("ADMINBOTTOKEN is empty. Add your bot token in main.py or Railway variables.")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DB_NAME = "asklybux_adminbot.db"
db_lock = threading.Lock()

# Temporary admin states.
admin_states = {}


# ============================================================
# Database helpers
# ============================================================

def db_connect():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                userid INTEGER PRIMARY KEY,
                username TEXT,
                firstname TEXT,
                joined_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS wallet (
                userid INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0.0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                reward REAL NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS taskstock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                firstname TEXT NOT NULL,
                login TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                assigned INTEGER DEFAULT 0,
                assigned_to INTEGER,
                assigned_at TEXT,
                created_at TEXT,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS assignedtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                stock_id INTEGER NOT NULL,
                status TEXT DEFAULT 'assigned',
                twofa TEXT,
                decoded_twofa TEXT,
                assigned_at TEXT,
                submitted_at TEXT,
                UNIQUE(stock_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pendingaccounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                task_id INTEGER,
                stock_id INTEGER,
                task_name TEXT NOT NULL,
                reward REAL NOT NULL,
                firstname TEXT NOT NULL,
                login TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                twofa TEXT,
                decoded_twofa TEXT,
                status TEXT DEFAULT 'pending',
                submitted_at TEXT
            )
        """)

        # Starter task.
        cur.execute("SELECT COUNT(*) AS total FROM tasks")
        total = cur.fetchone()["total"]

        if total == 0:
            cur.execute("""
                INSERT INTO tasks (name, reward, active, created_at)
                VALUES (?, ?, 1, ?)
            """, ("📱 Create Inst (2FA)", 0.0200, now()))

        conn.commit()
        conn.close()


def is_admin(message_or_call):
    return message_or_call.from_user.id == ADMINID


def add_balance(userid, amount):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT OR IGNORE INTO wallet (userid, balance)
            VALUES (?, 0.0)
        """, (userid,))

        cur.execute("""
            UPDATE wallet
            SET balance = balance + ?
            WHERE userid = ?
        """, (amount, userid))

        conn.commit()
        conn.close()


def remove_balance(userid, amount):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT OR IGNORE INTO wallet (userid, balance)
            VALUES (?, 0.0)
        """, (userid,))

        cur.execute("""
            UPDATE wallet
            SET balance = CASE
                WHEN balance - ? < 0 THEN 0
                ELSE balance - ?
            END
            WHERE userid = ?
        """, (amount, amount, userid))

        conn.commit()
        conn.close()


def create_task(name, reward):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tasks (name, reward, active, created_at)
            VALUES (?, ?, 1, ?)
        """, (name, reward, now()))

        conn.commit()
        task_id = cur.lastrowid
        conn.close()

    return task_id


def get_tasks():
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT t.*,
                   COUNT(s.id) AS stock_count
            FROM tasks t
            LEFT JOIN taskstock s ON s.task_id = t.id AND s.assigned = 0
            WHERE t.active = 1
            GROUP BY t.id
            ORDER BY t.id DESC
        """)
        rows = cur.fetchall()

        conn.close()

    return rows


def get_task(task_id):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM tasks WHERE id = ? AND active = 1", (task_id,))
        row = cur.fetchone()

        conn.close()

    return row


def add_stock(task_id, firstname, login, password, email):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO taskstock
            (task_id, firstname, login, password, email, assigned, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (task_id, firstname, login, password, email, now()))

        conn.commit()
        conn.close()


def get_pending_accounts():
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM pendingaccounts
            WHERE status = 'pending'
            ORDER BY id ASC
        """)
        rows = cur.fetchall()

        conn.close()

    return rows


def get_pending(pending_id):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM pendingaccounts
            WHERE id = ? AND status = 'pending'
        """, (pending_id,))
        row = cur.fetchone()

        conn.close()

    return row


def update_pending_status(pending_id, status):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM pendingaccounts
            WHERE id = ?
        """, (pending_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return None

        cur.execute("""
            UPDATE pendingaccounts
            SET status = ?
            WHERE id = ?
        """, (status, pending_id))

        if row["stock_id"]:
            cur.execute("""
                UPDATE assignedtasks
                SET status = ?
                WHERE stock_id = ?
            """, (status, row["stock_id"]))

        conn.commit()
        conn.close()

    return row


def save_manual_pending(
    userid,
    task_name,
    reward,
    firstname,
    login,
    password,
    email,
    twofa,
    decoded_twofa
):
    with db_lock:
        conn = db_connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO pendingaccounts
            (userid, task_name, reward, firstname, login, password, email,
             twofa, decoded_twofa, status, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            userid,
            task_name,
            reward,
            firstname,
            login,
            password,
            email,
            twofa,
            decoded_twofa,
            now()
        ))

        conn.commit()
        pending_id = cur.lastrowid
        conn.close()

    return pending_id


# ============================================================
# UI helpers
# ============================================================

def dashboard_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛑 Pending Accounts", callback_data="pending"),
        types.InlineKeyboardButton("➕ Add Task", callback_data="addtask")
    )
    markup.add(
        types.InlineKeyboardButton("📂 Select Tasks", callback_data="selecttasks")
    )
    return markup


def back_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="dashboard"))
    return markup


def tasks_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)

    tasks = get_tasks()

    for task in tasks:
        markup.add(
            types.InlineKeyboardButton(
                f"{task['name']} (${float(task['reward']):.4f}) | Stock: {task['stock_count']}",
                callback_data=f"task_{task['id']}"
            )
        )

    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="dashboard"))
    return markup


def pending_list_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    pending = get_pending_accounts()

    for item in pending:
        markup.add(
            types.InlineKeyboardButton(
                f"#{item['id']} | {item['task_name']} | User {item['userid']}",
                callback_data=f"viewpending_{item['id']}"
            )
        )

    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="dashboard"))
    return markup


def pending_action_markup(pending_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{pending_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{pending_id}")
    )
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="pending"))
    return markup


def safe_edit(call, text, markup=None):
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


def access_denied_message(chat_id):
    bot.send_message(chat_id, "🚫 Access denied.")


# ============================================================
# Handlers
# ============================================================

@bot.message_handler(commands=["start"])
def start_handler(message):
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    text = (
        "🛠 <b>AsklyBux Admin Panel</b>\n\n"
        "Manage tasks, stock, pending accounts, wallet actions, and code delivery."
    )

    bot.send_message(message.chat.id, text, reply_markup=dashboard_markup())


@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    if not is_admin(call):
        bot.answer_callback_query(call.id, "Access denied.")
        return

    data = call.data

    if data == "dashboard":
        admin_states.pop(call.from_user.id, None)

        text = (
            "🛠 <b>AsklyBux Admin Panel</b>\n\n"
            "Manage tasks, stock, pending accounts, wallet actions, and code delivery."
        )

        safe_edit(call, text, dashboard_markup())
        bot.answer_callback_query(call.id)
        return

    if data == "pending":
        pending = get_pending_accounts()

        if not pending:
            text = "🛑 <b>Pending Accounts</b>\n\nNo pending accounts found."
        else:
            text = "🛑 <b>Pending Accounts</b>\n\nSelect a pending account."

        safe_edit(call, text, pending_list_markup())
        bot.answer_callback_query(call.id)
        return

    if data.startswith("viewpending_"):
        try:
            pending_id = int(data.split("_")[1])
        except Exception:
            bot.answer_callback_query(call.id, "Invalid pending ID.")
            return

        item = get_pending(pending_id)

        if not item:
            bot.answer_callback_query(call.id, "Pending account not found.")
            return

        text = (
            f"🛑 <b>Pending Account #{item['id']}</b>\n\n"
            f"📋 <b>Task:</b> {item['task_name']}\n"
            f"💰 <b>Reward:</b> ${float(item['reward']):.4f}\n\n"
            f"👤 <b>First name:</b> <code>{item['firstname']}</code>\n"
            f"🔑 <b>Login:</b> <code>{item['login']}</code>\n"
            f"🔒 <b>Password:</b> <code>{item['password']}</code>\n"
            f"📧 <b>Email:</b> <code>{item['email']}</code>\n"
            f"🔐 <b>2FA:</b> <code>{item['twofa'] or ''}</code>\n"
            f"✅ <b>Decoded:</b> <code>{item['decoded_twofa'] or ''}</code>\n"
            f"🆔 <b>UserID:</b> <code>{item['userid']}</code>\n\n"
            "Status: <b>Pending</b>"
        )

        safe_edit(call, text, pending_action_markup(pending_id))
        bot.answer_callback_query(call.id)
        return

    if data.startswith("approve_"):
        try:
            pending_id = int(data.split("_")[1])
        except Exception:
            bot.answer_callback_query(call.id, "Invalid pending ID.")
            return

        item = update_pending_status(pending_id, "approved")

        if not item:
            bot.answer_callback_query(call.id, "Pending account not found.")
            return

        reward = float(item["reward"])
        userid = int(item["userid"])

        add_balance(userid, reward)

        try:
            bot.send_message(userid, f"🎉 <b>Approved</b>\n\n+${reward:.4f} added.")
        except Exception:
            pass

        text = (
            "✅ <b>Approved</b>\n\n"
            f"UserID: <code>{userid}</code>\n"
            f"Reward added: <b>${reward:.4f}</b>\n\n"
            "If you also use the User Bot database, run this command in the User Bot too:\n"
            f"<code>/add {userid} {reward:.4f}</code>"
        )

        safe_edit(call, text, dashboard_markup())
        bot.answer_callback_query(call.id, "Approved.")
        return

    if data.startswith("reject_"):
        try:
            pending_id = int(data.split("_")[1])
        except Exception:
            bot.answer_callback_query(call.id, "Invalid pending ID.")
            return

        item = update_pending_status(pending_id, "rejected")

        if not item:
            bot.answer_callback_query(call.id, "Pending account not found.")
            return

        userid = int(item["userid"])

        try:
            bot.send_message(userid, "❌ <b>Rejected.</b>")
        except Exception:
            pass

        text = (
            "❌ <b>Rejected</b>\n\n"
            f"UserID: <code>{userid}</code>\n\n"
            "If you also use the User Bot database, run this command in the User Bot too:\n"
            f"<code>/reject {userid}</code>"
        )

        safe_edit(call, text, dashboard_markup())
        bot.answer_callback_query(call.id, "Rejected.")
        return

    if data == "addtask":
        admin_states[call.from_user.id] = {
            "step": "addtask_name"
        }

        text = (
            "➕ <b>Add Task</b>\n\n"
            "Send the task name.\n\n"
            "Example:\n"
            "<code>📱 Create Inst (2FA)</code>"
        )

        safe_edit(call, text, back_markup())
        bot.answer_callback_query(call.id)
        return

    if data == "selecttasks":
        tasks = get_tasks()

        if not tasks:
            text = "📂 <b>Select Tasks</b>\n\nNo tasks created yet."
        else:
            text = "📂 <b>Select Tasks</b>\n\nChoose a task to add stock."

        safe_edit(call, text, tasks_markup())
        bot.answer_callback_query(call.id)
        return

    if data.startswith("task_"):
        try:
            task_id = int(data.split("_")[1])
        except Exception:
            bot.answer_callback_query(call.id, "Invalid task.")
            return

        task = get_task(task_id)

        if not task:
            bot.answer_callback_query(call.id, "Task not found.")
            return

        admin_states[call.from_user.id] = {
            "step": "stock_firstname",
            "task_id": task_id
        }

        text = (
            "📦 <b>Add Stock</b>\n\n"
            f"Task: <b>{task['name']}</b>\n\n"
            "Step 1/4\n"
            "Send first name."
        )

        safe_edit(call, text, back_markup())
        bot.answer_callback_query(call.id)
        return


@bot.message_handler(commands=["add"])
def add_command(message):
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Usage: /add userid amount")
        return

    try:
        userid = int(parts[1])
        amount = float(parts[2])
    except Exception:
        bot.reply_to(message, "Invalid format.")
        return

    add_balance(userid, amount)

    try:
        bot.send_message(userid, f"🎉 <b>Approved</b>\n\n+${amount:.4f} added.")
    except Exception:
        pass

    bot.reply_to(
        message,
        f"✅ Added ${amount:.4f} to {userid}.\n\n"
        f"If using the User Bot wallet, run there too:\n"
        f"<code>/add {userid} {amount:.4f}</code>"
    )


@bot.message_handler(commands=["remove"])
def remove_command(message):
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Usage: /remove userid amount")
        return

    try:
        userid = int(parts[1])
        amount = float(parts[2])
    except Exception:
        bot.reply_to(message, "Invalid format.")
        return

    remove_balance(userid, amount)

    try:
        bot.send_message(userid, f"💸 <b>Wallet Updated</b>\n\n-${amount:.4f} removed.")
    except Exception:
        pass

    bot.reply_to(
        message,
        f"✅ Removed ${amount:.4f} from {userid}.\n\n"
        f"If using the User Bot wallet, run there too:\n"
        f"<code>/remove {userid} {amount:.4f}</code>"
    )


@bot.message_handler(commands=["code"])
def code_command(message):
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Usage: /code userid code")
        return

    try:
        userid = int(parts[1])
        code = parts[2].strip()
    except Exception:
        bot.reply_to(message, "Invalid format.")
        return

    text = (
        "📩 <b>Verification Code:</b>\n\n"
        f"<code>{code}</code>\n\n"
        "🔐 Send your 2FA key."
    )

    try:
        bot.send_message(userid, text)
        bot.reply_to(
            message,
            "✅ Code sent.\n\n"
            "If the user expects the message from the User Bot, run this command in the User Bot too."
        )
    except Exception:
        bot.reply_to(message, "❌ Could not send code. User may not have started this admin bot.")


@bot.message_handler(commands=["manualpending"])
def manual_pending_command(message):
    """
    Add a pending account manually to the Admin Bot database.

    Format:
    /manualpending userid | task name | reward | firstname | login | password | email | twofa | decoded
    """
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    payload = message.text.replace("/manualpending", "", 1).strip()
    parts = [p.strip() for p in payload.split("|")]

    if len(parts) != 9:
        bot.reply_to(
            message,
            "Usage:\n"
            "/manualpending userid | task name | reward | firstname | login | password | email | twofa | decoded"
        )
        return

    try:
        userid = int(parts[0])
        reward = float(parts[2])
    except Exception:
        bot.reply_to(message, "Invalid userid or reward.")
        return

    pending_id = save_manual_pending(
        userid=userid,
        task_name=parts[1],
        reward=reward,
        firstname=parts[3],
        login=parts[4],
        password=parts[5],
        email=parts[6],
        twofa=parts[7],
        decoded_twofa=parts[8]
    )

    bot.reply_to(message, f"✅ Manual pending account saved. ID: {pending_id}")


@bot.message_handler(commands=["taskslist"])
def tasks_list_command(message):
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    tasks = get_tasks()

    if not tasks:
        bot.reply_to(message, "No tasks found.")
        return

    lines = ["📋 <b>Tasks</b>\n"]

    for task in tasks:
        lines.append(
            f"ID: <code>{task['id']}</code> | {task['name']} | "
            f"${float(task['reward']):.4f} | Stock: {task['stock_count']}"
        )

    bot.reply_to(message, "\n".join(lines))


@bot.message_handler(commands=["newtask"])
def newtask_command(message):
    """
    Quick task creation:
    /newtask Task Name | 0.0200
    """
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    payload = message.text.replace("/newtask", "", 1).strip()

    if "|" not in payload:
        bot.reply_to(message, "Usage: /newtask Task Name | 0.0200")
        return

    name, reward_text = payload.split("|", 1)

    try:
        reward = float(reward_text.strip())
    except Exception:
        bot.reply_to(message, "Invalid reward.")
        return

    task_id = create_task(name.strip(), reward)
    bot.reply_to(message, f"✅ Task created. ID: {task_id}")


@bot.message_handler(commands=["addstock"])
def addstock_command(message):
    """
    Quick stock creation:
    /addstock task_id | firstname | login | password | email
    """
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    payload = message.text.replace("/addstock", "", 1).strip()
    parts = [p.strip() for p in payload.split("|")]

    if len(parts) != 5:
        bot.reply_to(message, "Usage: /addstock task_id | firstname | login | password | email")
        return

    try:
        task_id = int(parts[0])
    except Exception:
        bot.reply_to(message, "Invalid task_id.")
        return

    task = get_task(task_id)

    if not task:
        bot.reply_to(message, "Task not found.")
        return

    add_stock(task_id, parts[1], parts[2], parts[3], parts[4])
    bot.reply_to(message, "✅ Stock added.")


@bot.message_handler(func=lambda message: True, content_types=["text"])
def text_steps_handler(message):
    if not is_admin(message):
        access_denied_message(message.chat.id)
        return

    userid = message.from_user.id
    state = admin_states.get(userid)

    if not state:
        bot.send_message(message.chat.id, "Use the admin dashboard.", reply_markup=dashboard_markup())
        return

    step = state.get("step")
    text = message.text.strip()

    if step == "addtask_name":
        if len(text) < 2:
            bot.send_message(message.chat.id, "Task name is too short.")
            return

        state["name"] = text
        state["step"] = "addtask_reward"

        bot.send_message(
            message.chat.id,
            "➕ <b>Add Task</b>\n\n"
            "Send reward amount.\n\n"
            "Example:\n"
            "<code>0.0200</code>"
        )
        return

    if step == "addtask_reward":
        try:
            reward = float(text)
        except Exception:
            bot.send_message(message.chat.id, "Invalid reward. Example: 0.0200")
            return

        task_id = create_task(state["name"], reward)
        admin_states.pop(userid, None)

        bot.send_message(
            message.chat.id,
            f"✅ <b>Task Created</b>\n\n"
            f"ID: <code>{task_id}</code>\n"
            f"Name: {state['name']}\n"
            f"Reward: ${reward:.4f}",
            reply_markup=dashboard_markup()
        )
        return

    if step == "stock_firstname":
        state["firstname"] = text
        state["step"] = "stock_login"

        bot.send_message(
            message.chat.id,
            "📦 <b>Add Stock</b>\n\n"
            "Step 2/4\n"
            "Send login."
        )
        return

    if step == "stock_login":
        state["login"] = text
        state["step"] = "stock_password"

        bot.send_message(
            message.chat.id,
            "📦 <b>Add Stock</b>\n\n"
            "Step 3/4\n"
            "Send password."
        )
        return

    if step == "stock_password":
        state["password"] = text
        state["step"] = "stock_email"

        bot.send_message(
            message.chat.id,
            "📦 <b>Add Stock</b>\n\n"
            "Step 4/4\n"
            "Send email."
        )
        return

    if step == "stock_email":
        email = text

        if "@" not in email:
            bot.send_message(message.chat.id, "Invalid email. Please send a valid email.")
            return

        add_stock(
            task_id=state["task_id"],
            firstname=state["firstname"],
            login=state["login"],
            password=state["password"],
            email=email
        )

        admin_states.pop(userid, None)

        bot.send_message(
            message.chat.id,
            "✅ <b>Stock Added</b>\n\n"
            f"First name: <code>{state['firstname']}</code>\n"
            f"Login: <code>{state['login']}</code>\n"
            f"Password: <code>{state['password']}</code>\n"
            f"Email: <code>{email}</code>",
            reply_markup=dashboard_markup()
        )
        return


# ============================================================
# Run bot
# ============================================================

if __name__ == "__main__":
    init_db()
    print("AsklyBux Admin Panel Bot is running with polling...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
