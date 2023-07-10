"""
This module defines the TUI of the transcriptor application
"""


import contextlib
from itertools import cycle

from textual.app import App
from textual.containers import Container, Grid, Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Markdown,
    TabbedContent,
    TabPane,
    Tabs,
)
from textual.widgets.data_table import RowDoesNotExist

from transcriptor.base import Transcriptor
from transcriptor.utils import dicts_to_md

transapp = Transcriptor()


class QuitScreen(ModalScreen):
    def compose(self):
        yield Grid(
            Label("Are you sure you want to quit", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event):
        if event.button.id == "quit":
            self.dismiss(True)
        else:
            self.dismiss(False)


class ClientsList(VerticalScroll):
    def compose(self):
        if clients := transapp.api.get_clients():
            for client in clients:
                btn_label = client["name"]
                btn_id = client["client_id"]
                yield Button(
                    label=btn_label, id=f"client-{btn_id}", classes="clientbtn"
                )

        else:
            yield Button("No Clients")


class SortableTable(DataTable):
    BINDINGS = [
        ("c", "change_cursor", "Change Cursor"),
        ("s", "sort", "Sort"),
    ]
    cursors = cycle(["column", "row", "cell"])
    column_reverse = False
    job_columns = []
    jobs = []
    client_id = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_cursor = True
        self.zebra_stripes = True

    def action_sort(self, reverse=False):
        if self.cursor_type in ["column", "cell"]:
            column_key = self.coordinate_to_cell_key(self.cursor_coordinate).column_key
            self.sort(column_key, reverse=self.column_reverse)
            self.column_reverse = not self.column_reverse

    def action_change_cursor(self):
        self.cursor_type = next(self.cursors)

    def key_p(self, event):
        self.pending_jobs(self.client_id)

    def key_a(self, event):
        self.all_jobs(self.client_id)

    def on_key(self, event):
        action = {
            "l": self.action_cursor_right,
            "h": self.action_cursor_left,
            "k": self.action_cursor_up,
            "j": self.action_cursor_down,
        }
        # lambda that returns another lambda.
        # When the returned lambda is called it returns None.
        action.get(event.key, lambda: lambda: None)()

    def populate_table(self, jobs):
        with contextlib.suppress(Exception):
            self.clear(columns=True)

            for column in jobs[0].keys():
                self.add_column(column, key=column)

            for job in jobs:
                self.add_row(*job.values())

    def pending_jobs(self, client_id):
        self.client_id = client_id
        jobs = transapp.api.get_jobs([f"client_id={client_id} status=Pending"])
        self.populate_table(jobs)

    def all_jobs(self, client_id):
        self.client_id = client_id
        jobs = transapp.api.get_jobs([f"client_id={client_id}"])
        self.populate_table(jobs)

    def on_data_table_header_selected(self, event):
        self.sort(event.column_key, reverse=self.column_reverse)
        self.column_reverse = not self.column_reverse


class GenerateInvoice(Container):
    def compose(self):
        yield Container(
            Label("From: "),
            Input(placeholder="From", id="invoice-from"),
            Label("To: "),
            Input(placeholder="To", id="invoice-to"),
            Button("Generate", id="invoice-btn", disabled=True),
            classes="box",
        )
        yield DataTable(id="cutoffs-table", classes="box")
        yield VerticalScroll(
            Markdown(id="md-invoice"), id="invoice-md-container", classes="box"
        )

    def on_data_table_cell_selected(self, event):
        column = event.coordinate.column
        if column == 1:
            # TODO When start doesn't exist popup prompt window
            with contextlib.suppress(RowDoesNotExist):
                start = event.data_table.get_row_at(event.coordinate.row - 1)[0]
                end = event.data_table.get_row_at(event.coordinate.row)[0]
                self.query_one("#invoice-from").value = start
                self.query_one("#invoice-to").value = end


class ClientTabs(VerticalScroll):
    def compose(self):
        with TabbedContent():
            with TabPane("Jobs", id="jobs"):
                yield SortableTable(id="jobs-table")
            with TabPane("Information", id="info"):
                yield Markdown(id="info-md")
            with TabPane("Invoice", id="invoice"):
                yield Horizontal(
                    GenerateInvoice(id="gen-invoice"),
                    id="invoice-container",
                )


class TranscriptorScreen(Screen):
    def compose(self):
        yield Header()
        with VerticalScroll(id="MainViewContainer", classes="mainviewcontainer hidden"):
            yield ClientTabs(id="client_tabs")
        yield Footer()
        yield ClientsList(id="clients_list", classes="hidden")


class TranscriptorApp(App):
    CSS_PATH = "Transcriptor.css"
    TITLE = "Transcriptor"
    BINDINGS = [
        ("ctrl+b", "toggle_client_list", "Clients"),
        ("ctrl+t", "change_cursor_type", "Cursor Type"),
        ("ctrl+n", "next_tab", "next tab"),
        ("ctrl+p", "previous_tab", "previous tab"),
        ("q", "request_quit", "Quit"),
    ]
    cursors = cycle(["column", "row", "cell"])

    show_client_list = reactive(False)

    def on_mount(self):
        self.push_screen(TranscriptorScreen())

    def action_request_quit(self):
        def check_quit(quit):
            if quit:
                self.exit()

        self.push_screen(QuitScreen(), check_quit)

    def action_toggle_client_list(self):
        client_list = self.query_one(ClientsList)
        main_view = self.query_one("#MainViewContainer")
        self.set_focus(None)
        if client_list.has_class("-hidden"):
            client_list.remove_class("-hidden")
            main_view.add_class("hidden")
        else:
            if client_list.query("*:focus"):
                self.screen.set_focus(None)
            client_list.add_class("-hidden")
            main_view.remove_class("hidden")

    def action_change_cursor_type(self):
        data_table = self.query_one("#jobs-table")
        data_table.cursor_type = next(self.cursors)

    def on_button_pressed(self, event):  # sourcery skip: move-assign
        button_id = event.button.id
        if button_id.partition("-")[0] == "client":
            self.client_id = button_id.partition("-")[-1]
            self.query_one("#invoice-btn").disabled = False
            self.update_tabs(self.client_id)
        elif button_id == "invoice-btn":
            self.query_one("#md-invoice")
            start = self.query_one("#invoice-from").value
            end = self.query_one("#invoice-to").value
            if all([start, end]):
                if invoice := transapp.create_invoice(
                    client_id=self.client_id,
                    jobs_conditions=[
                        [
                            f"client_id={self.client_id} date_submitted>{start} date_submitted<={end} date_submitted!=NULL"
                        ],
                        [],
                    ],
                ):
                    self.query_one("#md-invoice").update(invoice)

    def action_next_tab(self):
        self.query_one(Tabs).action_next_tab()

    def previous_tab(self):
        self.query_one(Tabs).action_previous_tab()

    def update_tabs(self, client_id):
        data_table = self.query_one("#jobs-table")
        data_table.pending_jobs(client_id)
        client = transapp.api.get_clients([f"client_id={client_id}"])
        client_info = dicts_to_md(client, "hor")
        info_markdown = self.query_one("#info-md")
        info_markdown.update(client_info)

        cutoffs_table = self.query_one("#cutoffs-table")
        cutoffs_table.clear(columns=True)
        rows = iter(transapp.load_cutoffs())
        cutoffs_table.add_columns(*next(rows))
        cutoffs_table.add_rows(rows)


if __name__ == "__main__":
    app = TranscriptorApp()
    app.run()
