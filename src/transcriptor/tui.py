import csv
import io

from textual.app import App
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from transcriptor.base import Transcriptor
from transcriptor.utils import *

trans_app = Transcriptor()


class Configs(Container):
    def compose(self):
        for idx, (key, value) in enumerate(trans_app.config.__dict__.items()):
            yield Static(f"{tc(key)}", name=f"{key}", id=f"ck-{idx}")
            yield Input(value=f"{value}", id=f"cv-{idx}")
        yield Button("Save", id="save_config_button")

    def on_button_pressed(self, event):
        button_id = event.button.id
        assert button_id is not None

        if button_id == "save_config_button":
            query_keys = self.query(Static)
            query_values = self.query(Input)

            for query_key in query_keys:
                for query_value in query_values:
                    if (
                        query_key.id.partition("-")[-1]
                        == query_value.id.partition("-")[-1]
                    ):
                        trans_app.config.__dict__[query_key.name] = query_value.value
                        break
            trans_app.save_config()


class Profiles(Container):
    def compose(self):
        for idx, (key, value) in enumerate(trans_app.profile.__dict__.items()):
            yield Static(f"{tc(key)}", name=f"{key}", id=f"pk-{idx}")
            yield Input(value=f"{value}", id=f"pv-{idx}")
        yield Button("Save", id="save_profile_button")

    def on_button_pressed(self, event):
        button_id = event.button.id
        assert button_id is not None

        if button_id == "save_profile_button":
            query_keys = self.query(Static)
            query_values = self.query(Input)

            for query_key in query_keys:
                for query_value in query_values:
                    if (
                        query_key.id.partition("-")[-1]
                        == query_value.id.partition("-")[-1]
                    ):
                        trans_app.profile.__dict__[query_key.name] = query_value.value
                        break
            trans_app.save_profile()


class SideBar(Vertical):
    def compose(self):
        clients = trans_app.api.list_clients()
        yield Vertical(
            *[
                Button(
                    client[0].name, id=f"client-{client[0].id}", classes="client_button"
                )
                for client in clients
            ]
        )


class RightSideBar(Vertical):
    def compose(self):
        actions = ["create-invoice"]
        yield Vertical(
            *[
                Button(tc(action), id=f"{action}", classes="client_button")
                for action in actions
            ]
        )


class Clients(Container):
    def compose(self):
        table = DataTable()
        clients = trans_app.api.list_clients()
        headers = ["id", "name", "email", "normal", "expedite", "interpreted"]
        if clients:
            clients_csv = list_of_rows_to_csv(
                clients, headers=headers, omit=["rates_id"]
            )
            rows = csv.reader(io.StringIO(clients_csv))
            table.add_columns(*[tc(n) for n in next(rows)])
            table.add_rows(rows)
        yield table


class GenInvoice(Container):
    def compose(self):
        fields = ["date_from", "date_to"]
        for idx, field in enumerate(fields):
            yield Static(
                tc(field), name=f"{field}", id=f"field-{idx}", classes="pop-up"
            )
            yield Input(id=f"value-{idx}", classes="pop-up")


class Jobs(Container):
    def __init__(self, jobs_scalar):
        super().__init__()
        self.jobs_scalar = jobs_scalar

    def compose(self):
        table = DataTable()
        jobs = self.jobs_scalar
        headers = [
            "client_id",
            "date_received",
            "id",
            "job_number",
            "job_type",
            "status",
            "date_due",
            "total_quantity",
            "quantity",
            "job_rate",
            "date_submitted",
            "amount",
            "amount_paid",
            "job_path",
            "note",
        ]
        if jobs:
            jobs_csv = list_of_rows_to_csv(jobs, headers=headers)
            rows = csv.reader(io.StringIO(jobs_csv))
            table.add_columns(*[tc(n) for n in next(rows)])
            table.add_rows(rows)
        # yield Button(label="create_invoice", id="create-invoice")
        yield table

    # def on_button_pressed(self, event):
    #     button_id = event.button.id
    #
    #     assert button_id is not None
    #


class MenuBar(Horizontal):
    def compose(self):
        yield Horizontal(
            Button(label="config", id="config", classes="menu_button"),
            Button("profile", id="profile", classes="menu_button"),
            Button("clients", id="clients", classes="menu_button"),
            Button("jobs", id="jobs", classes="menu_button"),
        )


class TranscriptorTUI(App):
    CSS_PATH = "layout.css"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+l", "toggle_right_sidebar", "RightSideBar"),
    ]

    show_sidebar = reactive(False)

    def compose(self):
        yield Container(SideBar(), id="side_bar", classes="-hidden")
        yield Container(RightSideBar(), id="right_side_bar", classes="-hidden")
        yield Container(MenuBar(), id="menu_bar")
        yield Container(id="body")
        yield Header()
        yield Footer()

    def action_toggle_sidebar(self):
        sidebar = self.query_one("#side_bar")
        self.set_focus(None)

        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def action_toggle_right_sidebar(self):
        sidebar = self.query_one("#right_side_bar")
        self.set_focus(None)

        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    # def compose(self) -> ComposeResult:
    #     yield Horizontal(
    #             Vertical(Button(label="config", id="config"), classes="column"),
    #             Vertical(Button("profile", id="profile"), classes="column"),
    #             Vertical(Button("clients", id="clients"), classes="column"),
    #             Vertical(Button("jobs", id="jobs"), classes="column"),
    #             classes="title_bar")
    #     yield Container(Config(), id="big")
    #
    def on_button_pressed(self, event):
        button_id = event.button.id
        button_class = event.button.classes
        assert button_id is not None
        #
        if button_id == "config":
            body = self.query_one("#body")
            for child in body.children:
                child.remove()
            body.mount(Configs())

        elif button_id == "profile":
            body = self.query_one("#body")
            for child in body.children:
                child.remove()
            body.mount(Profiles())

        elif button_id == "clients":
            body = self.query_one("#body")
            for child in body.children:
                child.remove()
            body.mount(Clients())

        elif button_id == "jobs":
            body = self.query_one("#body")
            for child in body.children:
                child.remove()

            jobs = trans_app.api.list_jobs()
            body.mount(Jobs(jobs))

        if "client_button" in button_class:
            client_id = button_id.partition("-")[-1]

            body = self.query_one("#body")
            for child in body.children:
                child.remove()

            jobs = trans_app.api.list_jobs(attributes={"client_id": client_id})
            body.mount(Jobs(jobs))


if __name__ == "__main__":

    app = TranscriptorTUI()
    app.run()
