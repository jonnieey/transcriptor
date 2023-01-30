import csv
import io
import json

from textual.app import App, ComposeResult
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
        # clients_names = [client[1] for client in clients[1]]
        yield Vertical(
            *[
                Button(client[1], id=f"client_{client[0]}", classes="client_button")
                for client in clients[1]
            ]
        )


class Clients(Container):
    def compose(self):
        table = DataTable()
        clients = trans_app.api.list_clients()
        if clients:
            clients_csv = list_of_tuples_to_csv(clients)
            rows = csv.reader(io.StringIO(clients_csv))
            table.add_columns(*next(rows))
            table.add_rows(rows)
        yield table


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
        ("q", "quit", "Quit"),
        ("ctrl+b", "toggle_sidebar", "Sidebar"),
    ]

    show_sidebar = reactive(False)

    def compose(self):
        yield Container(SideBar(), id="side_bar", classes="-hidden")
        yield Container(MenuBar(), id="menu_bar")
        yield Container(id="body")
        yield Header()
        yield Footer()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#side_bar")
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

    #
    #     if button_id == "profile":
    #         w = self.query_one("#big")
    #         for child in w.children:
    #             child.remove()
    #         self.query_one(Container).mount(Profile())
    #         ### Find out how to clear container
    # # def on_mount(self) -> None:
    # #     table = self.query_one(DataTable)
    # #     rows = csv.reader(io.StringIO(dict_to_csv([config.__dict__])))
    # #     table.add_columns(*next(rows))
    # #     table.add_rows(rows)
    #


# if __name__ == "__main__":
#     # print( dict_to_csv([config.__dict__]))
#
# print(dir(Container()))
app = TranscriptorTUI()
app.run()
