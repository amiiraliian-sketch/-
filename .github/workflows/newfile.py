import os
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView


Window.clearcolor = (0.055, 0.065, 0.08, 1)


class AccountingApp(App):

    def build(self):
        self.db_path = os.path.join(self.user_data_dir, "accounting.db")
        self.setup_database()
        return self.build_dashboard()

    # ---------------- DATABASE ----------------

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT DEFAULT 'Other',
                date_time TEXT
            )
        """)

        # Add missing columns to old databases
        cur.execute("PRAGMA table_info(transactions)")
        columns = [row[1] for row in cur.fetchall()]

        if "category" not in columns:
            cur.execute(
                "ALTER TABLE transactions ADD COLUMN category TEXT DEFAULT 'Other'"
            )

        if "date_time" not in columns:
            cur.execute(
                "ALTER TABLE transactions ADD COLUMN date_time TEXT"
            )

        cur.execute("""
            UPDATE transactions
            SET date_time = ?
            WHERE date_time IS NULL
        """, (datetime.now().strftime("%Y-%m-%d %H:%M"),))

        conn.commit()
        conn.close()

    def add_transaction(self, trans_type, amount, category):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO transactions
            (type, amount, category, date_time)
            VALUES (?, ?, ?, ?)
        """, (
            trans_type,
            amount,
            category,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))

        conn.commit()
        conn.close()

    def get_transactions(self, limit=None):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        if limit:
            cur.execute("""
                SELECT id, type, amount, category, date_time
                FROM transactions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        else:
            cur.execute("""
                SELECT id, type, amount, category, date_time
                FROM transactions
                ORDER BY id DESC
            """)

        rows = cur.fetchall()
        conn.close()
        return rows

    def get_totals(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0)
            FROM transactions
        """)

        income, expense = cur.fetchone()
        conn.close()

        return income, expense

    def delete_transaction(self, transaction_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM transactions WHERE id=?",
            (transaction_id,)
        )

        conn.commit()
        conn.close()

    def update_transaction(self, transaction_id, trans_type, amount, category):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            UPDATE transactions
            SET type=?, amount=?, category=?
            WHERE id=?
        """, (
            trans_type,
            amount,
            category,
            transaction_id
        ))

        conn.commit()
        conn.close()

    # ---------------- UI HELPERS ----------------

    def rounded_background(self, widget, color, radius=18):
        with widget.canvas.before:
            Color(*color)
            rect = RoundedRectangle(
                pos=widget.pos,
                size=widget.size,
                radius=[dp(radius)]
            )

        def update_rect(instance, value):
            rect.pos = instance.pos
            rect.size = instance.size

        widget.bind(pos=update_rect, size=update_rect)

    def make_label(
        self,
        text="",
        font_size=16,
        color=(1, 1, 1, 1),
        bold=False
    ):
        label = Label(
            text=text,
            font_size=sp(font_size),
            color=color,
            bold=bold,
            halign="left",
            valign="middle"
        )
        label.bind(
            size=lambda obj, value: setattr(
                obj, "text_size", (obj.width, None)
            )
        )
        return label

    # ---------------- DASHBOARD ----------------

    def build_dashboard(self):

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(14)
        )

        title = Label(
            text="ACCOUNTING",
            font_size=dp(28),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(50)
        )

        root.add_widget(title)

        # Balance card
        self.balance_card = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            size_hint_y=None,
            height=dp(125)
        )

        self.rounded_background(
            self.balance_card,
            (0.12, 0.14, 0.18, 1),
            20
        )

        balance_title = Label(
            text="TOTAL BALANCE",
            font_size=dp(14),
            color=(0.65, 0.68, 0.75, 1),
            size_hint_y=None,
            height=dp(30)
        )

        self.balance_label = Label(
            text="0",
            font_size=dp(32),
            bold=True,
            color=(1, 1, 1, 1)
        )

        self.balance_card.add_widget(balance_title)
        self.balance_card.add_widget(self.balance_label)

        root.add_widget(self.balance_card)

        # Income / Expense cards
        stats = BoxLayout(
            spacing=dp(12),
            size_hint_y=None,
            height=dp(105)
        )

        self.income_card = BoxLayout(
            orientation="vertical",
            padding=dp(14)
        )
        self.rounded_background(
            self.income_card,
            (0.08, 0.20, 0.14, 1),
            18
        )

        income_title = Label(
            text="INCOME",
            font_size=dp(13),
            color=(0.55, 0.85, 0.65, 1)
        )

        self.income_label = Label(
            text="0",
            font_size=dp(23),
            bold=True,
            color=(0.5, 1, 0.65, 1)
        )

        self.income_card.add_widget(income_title)
        self.income_card.add_widget(self.income_label)

        self.expense_card = BoxLayout(
            orientation="vertical",
            padding=dp(14)
        )
        self.rounded_background(
            self.expense_card,
            (0.22, 0.09, 0.10, 1),
            18
        )

        expense_title = Label(
            text="EXPENSE",
            font_size=dp(13),
            color=(0.9, 0.55, 0.55, 1)
        )

        self.expense_label = Label(
            text="0",
            font_size=dp(23),
            bold=True,
            color=(1, 0.5, 0.5, 1)
        )

        self.expense_card.add_widget(expense_title)
        self.expense_card.add_widget(self.expense_label)

        stats.add_widget(self.income_card)
        stats.add_widget(self.expense_card)

        root.add_widget(stats)

        # Buttons
        buttons = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(52)
        )

        add_income = Button(
            text="+ INCOME",
            font_size=dp(15)
        )
        add_income.bind(on_release=lambda x: self.amount_popup("income"))

        add_expense = Button(
            text="- EXPENSE",
            font_size=dp(15)
        )
        add_expense.bind(on_release=lambda x: self.amount_popup("expense"))

        buttons.add_widget(add_income)
        buttons.add_widget(add_expense)

        root.add_widget(buttons)

        # Recent title
        recent_title = Label(
            text="RECENT TRANSACTIONS",
            font_size=dp(16),
            bold=True,
            color=(0.8, 0.82, 0.88, 1),
            size_hint_y=None,
            height=dp(35)
        )

        root.add_widget(recent_title)

        # Recent transactions
        self.transactions_box = BoxLayout(
            orientation="vertical",
            spacing=dp(8)
        )

        scroll = ScrollView()
        scroll.add_widget(self.transactions_box)
        root.add_widget(scroll)

        # View all
        view_all = Button(
            text="VIEW ALL TRANSACTIONS",
            size_hint_y=None,
            height=dp(48),
            font_size=dp(14)
        )

        view_all.bind(on_release=self.show_all_transactions)

        root.add_widget(view_all)

        self.update_dashboard()

        return root

    # ---------------- DASHBOARD UPDATE ----------------

    def update_dashboard(self):

        income, expense = self.get_totals()
        balance = income - expense

        self.balance_label.text = f"{balance:,.0f}"
        self.income_label.text = f"{income:,.0f}"
        self.expense_label.text = f"{expense:,.0f}"

        self.transactions_box.clear_widgets()

        rows = self.get_transactions(5)

        if not rows:
            empty = Label(
                text="No transactions yet",
                color=(0.55, 0.58, 0.65, 1),
                font_size=dp(15)
            )
            self.transactions_box.add_widget(empty)
            return

        for row in rows:
            self.add_transaction_row(
                self.transactions_box,
                row,
                compact=True
            )

    # ---------------- TRANSACTION ROW ----------------

    def add_transaction_row(self, container, row, compact=False):

        transaction_id, trans_type, amount, category, date_time = row

        row_box = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            padding=dp(10),
            size_hint_y=None,
            height=dp(70 if compact else 82)
        )

        self.rounded_background(
            row_box,
            (0.10, 0.115, 0.15, 1),
            14
        )

        info = BoxLayout(
            orientation="vertical"
        )

        sign = "+" if trans_type == "income" else "-"

        amount_color = (
            (0.45, 1, 0.6, 1)
            if trans_type == "income"
            else
            (1, 0.45, 0.45, 1)
        )

        amount_label = Label(
            text=f"{sign} {amount:,.0f}",
            font_size=dp(17),
            bold=True,
            color=amount_color,
            halign="left",
            valign="middle"
        )

        category_label = Label(
            text=f"{category}  •  {date_time}",
            font_size=dp(12),
            color=(0.62, 0.65, 0.72, 1),
            halign="left",
            valign="middle"
        )

        info.add_widget(amount_label)
        info.add_widget(category_label)

        edit_btn = Button(
            text="Edit",
            size_hint_x=None,
            width=dp(60)
        )

        delete_btn = Button(
            text="X",
            size_hint_x=None,
            width=dp(45)
        )

        edit_btn.bind(
            on_release=lambda x, r=row:
            self.edit_popup(r)
        )

        delete_btn.bind(
            on_release=lambda x, tid=transaction_id:
            self.confirm_delete(tid)
        )

        row_box.add_widget(info)
        row_box.add_widget(edit_btn)
        row_box.add_widget(delete_btn)

        container.add_widget(row_box)

    # ---------------- ADD TRANSACTION ----------------

    def amount_popup(self, trans_type):

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        amount_input = TextInput(
            hint_text="Amount",
            input_filter="float",
            multiline=False,
            font_size=dp(18)
        )

        categories = [
            "Food",
            "Transport",
            "Shopping",
            "Bills",
            "Technology",
            "Other"
        ]

        category_buttons = GridLayout(
            cols=3,
            spacing=dp(6),
            size_hint_y=None,
            height=dp(110)
        )

        selected = ["Other"]

        for category in categories:
            btn = Button(text=category)

            def select_category(instance, c=category):
                selected[0] = c

            btn.bind(on_release=select_category)
            category_buttons.add_widget(btn)

        save_btn = Button(
            text="SAVE",
            size_hint_y=None,
            height=dp(48)
        )

        layout.add_widget(amount_input)
        layout.add_widget(category_buttons)
        layout.add_widget(save_btn)

        popup = Popup(
            title="Add Income" if trans_type == "income" else "Add Expense",
            content=layout,
            size_hint=(0.9, 0.65)
        )

        def save(instance):

            try:
                amount = float(amount_input.text)

                if amount <= 0:
                    return

                self.add_transaction(
                    trans_type,
                    amount,
                    selected[0]
                )

                popup.dismiss()
                self.update_dashboard()

            except:
                pass

        save_btn.bind(on_release=save)

        popup.open()

    # ---------------- EDIT ----------------

    def edit_popup(self, row):

        transaction_id, trans_type, amount, category, date_time = row

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        amount_input = TextInput(
            text=str(amount),
            input_filter="float",
            multiline=False,
            font_size=dp(18)
        )

        selected_type = [trans_type]
        selected_category = [category]

        type_buttons = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        income_btn = Button(text="Income")
        expense_btn = Button(text="Expense")

        income_btn.bind(
            on_release=lambda x: selected_type.__setitem__(0, "income")
        )

        expense_btn.bind(
            on_release=lambda x: selected_type.__setitem__(0, "expense")
        )

        type_buttons.add_widget(income_btn)
        type_buttons.add_widget(expense_btn)

        categories = [
            "Food",
            "Transport",
            "Shopping",
            "Bills",
            "Technology",
            "Other"
        ]

        category_buttons = GridLayout(
            cols=3,
            spacing=dp(6),
            size_hint_y=None,
            height=dp(110)
        )

        for c in categories:
            btn = Button(text=c)

            btn.bind(
                on_release=lambda x, value=c:
                selected_category.__setitem__(0, value)
            )

            category_buttons.add_widget(btn)

        save_btn = Button(
            text="SAVE",
            size_hint_y=None,
            height=dp(48)
        )

        layout.add_widget(amount_input)
        layout.add_widget(type_buttons)
        layout.add_widget(category_buttons)
        layout.add_widget(save_btn)

        popup = Popup(
            title="Edit Transaction",
            content=layout,
            size_hint=(0.9, 0.7)
        )

        def save(instance):

            try:
                new_amount = float(amount_input.text)

                if new_amount <= 0:
                    return

                self.update_transaction(
                    transaction_id,
                    selected_type[0],
                    new_amount,
                    selected_category[0]
                )

                popup.dismiss()
                self.update_dashboard()

            except:
                pass

        save_btn.bind(on_release=save)

        popup.open()

    # ---------------- DELETE ----------------

    def confirm_delete(self, transaction_id):

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(12)
        )

        text = Label(
            text="Delete this transaction?",
            font_size=dp(17)
        )

        buttons = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(48)
        )

        yes = Button(text="DELETE")
        no = Button(text="CANCEL")

        buttons.add_widget(no)
        buttons.add_widget(yes)

        layout.add_widget(text)
        layout.add_widget(buttons)

        popup = Popup(
            title="Confirm",
            content=layout,
            size_hint=(0.85, 0.35)
        )

        no.bind(
            on_release=popup.dismiss
        )

        def delete(instance):
            self.delete_transaction(transaction_id)
            popup.dismiss()
            self.update_dashboard()

        yes.bind(on_release=delete)

        popup.open()

    # ---------------- ALL TRANSACTIONS ----------------

    def show_all_transactions(self, instance):

        rows = self.get_transactions()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        close_btn = Button(
            text="CLOSE",
            size_hint_y=None,
            height=dp(48)
        )

        scroll = ScrollView()

        transaction_box = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None
        )

        transaction_box.bind(
            minimum_height=transaction_box.setter("height")
        )

        if not rows:
            transaction_box.add_widget(
                Label(
                    text="No transactions",
                    size_hint_y=None,
                    height=dp(60)
                )
            )
        else:
            for row in rows:
                self.add_transaction_row(
                    transaction_box,
                    row,
                    compact=False
                )

        scroll.add_widget(transaction_box)

        main.add_widget(scroll)
        main.add_widget(close_btn)

        popup = Popup(
            title="All Transactions",
            content=main,
            size_hint=(0.95, 0.9)
        )

        close_btn.bind(
            on_release=popup.dismiss
        )

        popup.open()


if __name__ == "__main__":
    AccountingApp().run()