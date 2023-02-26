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


def parse_form(query_keys, query_values):
    return_value = {}
    for query_key in query_keys:
        for query_value in query_values:
            if query_key.id.partition("-")[-1] == query_value.id.partition("-")[-1]:
                return_value[query_key.name] = query_value.value
                break
    return return_value


def remove_children(query):
    [child.remove() for child in query.children]


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
            update_dict = parse_form(query_keys, query_values)
            trans_app.config.__dict__.update(update_dict)
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
            update_dict = parse_form(query_keys, query_values)
            trans_app.profile.__dict__.update(update_dict)
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


class AddClient(Container):
    def compose(self):
        fields = ["Name", "Email"]
        rates = {"Normal": "0.4", "Expedite": "0.6", "Interpreted": "0.3"}

        for idx, field in enumerate(fields):
            yield Static(
                tc(field),
                name=f"{field}-static",
                id=f"{field}-static",
                classes="pop-up",
            )
            yield Input(name=f"{field}", id=f"{field}-value", classes="pop-up")
        #
        yield Horizontal(
            *[
                Vertical(
                    Static(name=f"{rate}-static", classes="pop-up"),
                    Input(
                        name=f"{rate}",
                        value=rates[rate],
                        id=f"{rate}-value",
                        classes="pop-up",
                    ),
                    classes="column",
                )
                for rate in rates
            ]
        )
        yield Horizontal(Button("Add", id="add_client_button"))


class ClientActions(Container):
    def compose(self):
        actions = ["Add Job", "Create Invoice"]

        yield Horizontal(
            *[
                Button(label=f"{action}", id=f"{action}", classes="footer_button")
                for action in actions
            ]
        )


class GenInvoice(Container):
    def compose(self):
        fields = ["date_from", "date_to"]
        for idx, field in enumerate(fields):
            yield Static(
                tc(field), name=f"{field}", id=f"field-{idx}", classes="pop-up"
            )
            yield Input(id=f"value-{idx}", classes="pop-up")


class Jobs(Container):
    def __init__(self, jobs_scalar=None):
        super().__init__()
        self.jobs_scalar = (
            jobs_scalar if jobs_scalar is not None else trans_app.api.list_jobs()
        )

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
        yield table


class MenuBar(Horizontal):
    def compose(self):
        fields = ["config", "profile", "clients", "jobs"]
        yield Horizontal(
            *[
                Button(f"{field}", id=f"{field}", classes="menu_button")
                for field in fields
            ]
        )


class FooterBar(Horizontal):
    def compose(self):
        yield Horizontal(
            Button(label="Add Client", id="add_client", classes="footer_button"),
            Button("Delete Client", id="del_client", classes="footer_button"),
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
        yield Container(FooterBar(), id="footer_bar")
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

    def on_button_pressed(self, event):
        button_id = event.button.id
        button_class = event.button.classes
        assert button_id is not None
        #
        button_mapping = {
            "config": Configs,
            "profile": Profiles,
            "clients": Clients,
            "jobs": Jobs,
        }

        if button_id in ["config", "profile", "clients", "jobs"]:
            body = self.query_one("#body")
            footer_bar = self.query_one("#footer_bar")
            remove_children(body)
            body.mount(button_mapping[button_id]())
            remove_children(footer_bar)
            footer_bar.mount(FooterBar())

        if "client_button" in button_class:
            client_id = button_id.partition("-")[-1]

            body = self.query_one("#body")
            footer_bar = self.query_one("#footer_bar")
            remove_children(body)
            remove_children(footer_bar)
            jobs = trans_app.api.list_jobs(attributes={"client_id": client_id})
            body.mount(Jobs(jobs))
            footer_bar.mount(ClientActions())
            # body.mount(ClientActions())
        if button_id in ["add_client"]:
            body = self.query_one("#body")
            remove_children(body)
            body.mount(AddClient())

        if button_id == "add_client_button":
            query_keys = self.query(Static)
            query_values = self.query(Input)

            client_dict = {"rates": {}}
            for query_value in query_values:
                if query_value.name in ["Normal", "Expedite", "Interpreted"]:
                    client_dict["rates"].update(
                        {query_value.name.lower(): query_value.value}
                    )
                else:
                    client_dict.update({query_value.name.lower(): query_value.value})
            # trans_app.add_client(**client_dict)
            body = self.query_one("#body")
            remove_children(body)
            body.mount(Clients())


def main():
    app = TranscriptorTUI()
    app.run()


if __name__ == "__main__":
    main()
