import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, DataTable, Footer, Header, Input
from textual.widgets import Label
from textual.widgets import Label as ListLabel
from textual.widgets import (
    ListItem,
    ListView,
    Markdown,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from transcriptor.base import Transcriptor
from transcriptor.utils import (
    TEMPLATE_MAPPING,
    extract_date_due,
    extract_job_number,
    get_media_duration,
    get_media_files,
    invoice_template_themes,
    sc,
)
from transcriptor.utils import str_to_date as std


class InvoicePreviewScreen(ModalScreen):
    """Screen for previewing invoices before generating PDF/CSV"""

    def __init__(self, html_content: str, client_name: str, jobs: List[Dict]):
        super().__init__()
        self.html_content = html_content
        self.client_name = client_name
        self.jobs = jobs

    def compose(self) -> ComposeResult:
        with Container(id="invoice-preview"):
            yield Label("Invoice Preview", classes="preview-title")
            yield Markdown(
                self.app.transcriptor.to_md(self.html_content),
                id="invoice-markdown",
            )
            with Horizontal(id="preview-buttons"):
                yield Button(
                    "Generate PDF", variant="primary", id="generate-pdf"
                )
                yield Button(
                    "Generate CSV", variant="primary", id="generate-csv"
                )
                yield Button("Cancel", variant="default", id="cancel-preview")

    @on(Button.Pressed, "#generate-pdf")
    def generate_pdf(self):
        self.app.transcriptor.html_to_pdf(self.html_content, self.client_name)
        self.app.notify("PDF invoice generated successfully!")
        self.dismiss()

    @on(Button.Pressed, "#generate-csv")
    def generate_csv(self):
        self.app.transcriptor.generate_csv_invoice(
            self.jobs, self.client_name
        )
        self.app.notify("CSV invoice generated successfully!")
        self.dismiss()

    @on(Button.Pressed, "#cancel-preview")
    def cancel_preview(self):
        self.dismiss()


class ClientSelectionScreen(ModalScreen):
    """Screen for selecting a client when multiple clients are involved"""

    def __init__(self, clients: List[str], jobs: List[Dict]):
        super().__init__()
        self.clients = clients
        self.jobs = jobs

    def compose(self) -> ComposeResult:
        with Container(id="client-selection"):
            yield Label(
                "Select Client for Invoice", classes="selection-title"
            )
            yield Label(
                "Jobs from multiple clients selected. Please choose one:",
                classes="selection-subtitle",
            )
            yield Select(
                [(client, client) for client in self.clients],
                id="client-select",
            )
            with Horizontal(id="selection-buttons"):
                yield Button(
                    "Generate Invoice",
                    variant="primary",
                    id="generate-invoice",
                )
                yield Button(
                    "Cancel", variant="default", id="cancel-selection"
                )

    @on(Button.Pressed, "#generate-invoice")
    def generate_invoice(self):
        select_widget = self.query_one("#client-select", Select)
        selected_client = select_widget.value
        if selected_client:
            # Filter jobs for selected client
            client_jobs = [
                job
                for job in self.jobs
                if job.get("client_name") == selected_client
            ]
            if client_jobs:
                # Generate invoice for selected client
                html, client_name = self.app.transcriptor.generate_invoice(
                    client_jobs
                )
                if html and client_name:
                    self.app.push_screen(
                        InvoicePreviewScreen(html, client_name, client_jobs)
                    )
        self.dismiss()

    @on(Button.Pressed, "#cancel-selection")
    def cancel_selection(self):
        self.dismiss()


class JobContextMenu(ModalScreen):
    """Context menu for job actions"""

    def __init__(self, job_data: Dict, from_dashboard: bool = False):
        super().__init__()
        self.job_data = job_data
        self.from_dashboard = from_dashboard

    def compose(self) -> ComposeResult:
        with Container(id="context-menu"):
            yield Label(
                f"Job: {self.job_data.get('job_number', '')}",
                classes="context-title",
            )
            with ListView(id="action-list"):
                yield ListItem(ListLabel("📝 Edit Job"), id="edit-job")
                yield ListItem(ListLabel("🗑️ Delete Job"), id="delete-job")
                yield ListItem(
                    ListLabel("🧾 Generate Invoice"), id="generate-invoice"
                )
                yield ListItem(ListLabel("❌ Cancel"), id="cancel-context")

    @on(ListView.Selected)
    def handle_action_selection(self, event: ListView.Selected):
        action = event.item.id
        job_id = self.job_data.get("id")

        if action == "edit-job":
            self.dismiss()
            # Push the edit screen
            if hasattr(self.job_data, "__dict__"):
                job_dict = self.job_data.__dict__
            else:
                job_dict = dict(self.job_data)
            self.app.push_screen(JobEditScreen(job_dict))

        elif action == "delete-job":
            self.dismiss()
            # Confirm and delete
            if self.app.confirm_delete("job"):
                self.app.transcriptor.delete_jobs(
                    conditions={"id": [("=", job_id)]}
                )
                self.app.notify("Job deleted successfully!")
                # Refresh the appropriate table
                if self.from_dashboard:
                    self.app.load_dashboard()
                else:
                    self.app.load_all_jobs()

        elif action == "generate-invoice":
            self.dismiss()
            # Generate invoice for this single job
            selected_jobs_data = []
            if hasattr(self.job_data, "__dict__"):
                job_dict = self.job_data.__dict__
            else:
                job_dict = dict(self.job_data)

            # Extract client name
            if hasattr(self.job_data, "client"):
                client_name = (
                    self.job_data.client.name
                    if hasattr(self.job_data.client, "name")
                    else str(self.job_data.client)
                )
                job_dict["client_name"] = client_name
            else:
                job_dict["client_name"] = job_dict.get(
                    "client_name", "Unknown"
                )

            selected_jobs_data.append(job_dict)

            # Generate invoice
            html, client_name = self.app.transcriptor.generate_invoice(
                selected_jobs_data
            )
            if html and client_name:
                self.app.push_screen(
                    InvoicePreviewScreen(
                        html, client_name, selected_jobs_data
                    )
                )
            else:
                self.app.notify(
                    "Failed to generate invoice!", severity="error"
                )

        elif action == "cancel-context":
            self.dismiss()


# Add this to your tui6.py file
class AddJobScreen(ModalScreen):
    """Screen for adding new jobs following CLI workflow"""

    def __init__(self):
        super().__init__()
        self.step = 1  # Track current step
        self.job_data = {}
        self.media_files = []
        self.current_media_index = 0

    def compose(self) -> ComposeResult:
        with Container(id="add-job-screen"):
            yield Label("Add New Job", classes="add-job-title")
            yield Static("Step 1/4: Select Job File", id="add-job-step-info")

            # Initial form for step 1
            with Container(id="add-job-form"):
                yield Label("Job File Path:")
                yield Input(
                    placeholder="Enter path to job file or folder",
                    id="job-file-path",
                )
                yield Button("Browse", id="browse-file")

            with Horizontal(id="add-job-buttons"):
                yield Button(
                    "Previous",
                    variant="default",
                    id="prev-step",
                    disabled=True,
                )
                yield Button("Next", variant="primary", id="next-step")
                yield Button("Cancel", variant="default", id="cancel-add-job")

    def clear_form(self):
        """Clear the form and remove all widgets to avoid duplicate IDs"""
        form = self.query_one("#add-job-form", Container)
        # Remove all children from the form
        for child in list(form.children):
            child.remove()

    def load_step_1(self):
        """Step 1: Job file selection"""
        self.step = 1
        self.clear_form()

        step_info = self.query_one("#add-job-step-info", Static)
        step_info.update("Step 1/4: Select Job File")

        form = self.query_one("#add-job-form", Container)
        form.mount(
            Label("Job File Path:"),
            Input(
                placeholder="Enter path to job file or folder",
                id="job-file-path",
            ),
            Button("Browse", id="browse-file"),
        )

        self.update_button_states()
        self.query_one("#job-file-path", Input).focus()
        self.refresh(layout=True)

    def load_step_2(self):
        """Step 2: Job information"""
        self.step = 2
        self.clear_form()

        step_info = self.query_one("#add-job-step-info", Static)
        step_info.update("Step 2/4: Job Information")

        # Get clients for selection
        clients = self.app.transcriptor.api.get_clients()
        client_options = [
            (f"{client['name']} (ID: {client['id']})", str(client["id"]))
            for client in clients
        ]

        # Extract job number and date due from file path
        job_file = self.job_data.get("job_file", "")
        job_number = self.extract_job_number(job_file)
        date_due = self.extract_date_due(job_file)

        date_format = self.app.transcriptor.config.date_format
        today = datetime.now().strftime(date_format)

        form = self.query_one("#add-job-form", Container)
        form.mount(
            Label("Client:"),
            Select(
                client_options, id="client-select", prompt="Select a client"
            ),
            Label("Job Number:"),
            Input(
                value=job_number,
                id="job-number",
                placeholder="Auto-extracted or enter manually",
            ),
            Label("Date Received:"),
            Input(value=today, id="date-received", placeholder=date_format),
            Label("Date Due:"),
            Input(value=date_due, id="date-due", placeholder=date_format),
        )

        self.update_button_states()
        self.query_one("#client-select", Select).focus()
        self.refresh(layout=True)

    def load_step_3(self):
        """Step 3: Media file processing"""
        self.step = 3

        # Update step info
        step_info = self.query_one("#add-job-step-info", Static)

        # Get media files from the job directory

        client_name = self.job_data.get("client_name", "")
        job_number = self.job_data.get("job_number", "")
        date_received = self.job_data.get("date_received", "")
        date_due = self.job_data.get("date_due", "")

        job_dir = self.create_job_dir(
            client_name, job_number, date_received, date_due
        )

        job_file_path = Path(self.job_data.get("job_file", ""))

        self.mv_extract_job_file(job_file_path, job_dir)
        try:
            self.media_files = list(get_media_files(job_dir))
        except Exception as e:
            self.media_files = []
            self.app.notify(
                f"Error scanning for media files: {str(e)}", severity="error"
            )

        if not self.media_files:
            step_info.update("Step 3/4: No media files found")

            # Clear and rebuild form
            form = self.query_one("#add-job-form", Container)
            form.remove_children()

            form.mount(
                Label("No audio/video files found in the job directory."),
                Label("Please check the file path and try again."),
            )

            self.update_button_states()
            self.refresh(layout=True)
            return

        step_info.update(
            f"Step 3/4: Process Media Files ({len(self.media_files)} found)"
        )
        self.current_media_index = 0
        self.load_current_media_form()

    def mv_extract_job_file(
        self, job_file: Path | str, job_dir: Path | str
    ) -> None:
        """
        Move/Extract job file to jobs directory

        Arguments:
            job_file: Path object or path-like string to job file
            job_dir: Path object or path-like string to job directory
        """
        job_file = Path(job_file)
        if zipfile.is_zipfile(job_file):
            try:
                with zipfile.ZipFile(job_file) as zf:
                    zf.extractall(job_dir)
                job_file.unlink(missing_ok=True)
            except Exception as e:
                self.app.notify(
                    f"Error extracting zip file: {str(e)}", severity="error"
                )

        else:
            # shutil.move(job_file, job_dir)
            shutil.copy(job_file, job_dir)

    def load_current_media_form(self):
        """Load form for current media file"""
        if self.current_media_index >= len(self.media_files):
            self.load_step_4()
            return

        self.clear_form()

        current_file = self.media_files[self.current_media_index]
        media_info = self.query_one("#add-job-step-info", Static)
        media_info.update(
            f"Step 3/4: Media File {self.current_media_index + 1} of {len(self.media_files)}"
        )

        # Calculate media duration
        try:
            duration = get_media_duration(current_file)
            duration_text = f"{duration:.2f} minutes"
        except Exception as e:
            duration_text = f"Error: {str(e)}"
            duration = 0.0

        # Create unique IDs for this media file
        media_suffix = f"-{self.current_media_index}"

        form = self.query_one("#add-job-form", Container)
        form.mount(
            Label(f"File: {current_file.name}"),
            Label(f"Duration: {duration_text}"),
            Label(f"Path: {str(current_file)}"),
            Checkbox(
                "Process this file?",
                value=True,
                id=f"process-file{media_suffix}",
            ),
            Label("Job Type:"),
            Select(
                [
                    ("Normal", "normal"),
                    ("Expedite", "expedite"),
                    ("Interpreted", "interpreted"),
                ],
                value="normal",
                id=f"job-type{media_suffix}",
            ),
            Label("Quantity (minutes):"),
            Input(value=f"{duration:.2f}", id=f"quantity{media_suffix}"),
            Label("Template:"),
            Select(
                [
                    (v.replace(".docx", ""), k)
                    for k, v in TEMPLATE_MAPPING.items()
                ],
                value="zd",
                id=f"job-template{media_suffix}",
            ),
            Label("Note:"),
            TextArea(
                "",
                id=f"note{media_suffix}",
                placeholder="Optional note for this task",
            ),
        )

        self.update_button_states()
        self.query_one(f"#process-file{media_suffix}", Checkbox).focus()
        self.refresh(layout=True)

    def load_step_4(self):
        """Step 4: Review and confirmation"""
        self.step = 4

        # Update step info
        step_info = self.query_one("#add-job-step-info", Static)
        step_info.update("Step 4/4: Review and Confirm")

        client_name = self.job_data.get("client_name", "N/A")
        job_number = self.job_data.get("job_number", "N/A")
        date_received = self.job_data.get("date_received", "N/A")
        date_due = self.job_data.get("date_due", "N/A")
        tasks = self.job_data.get("tasks", [])

        # Clear and rebuild form
        form = self.query_one("#add-job-form", Container)
        form.remove_children()

        # Build summary content
        summary_widgets = [
            Label("Job Summary:", classes="summary-title"),
            Static(f"Client: {client_name}", classes="summary-item"),
            Static(f"Job Number: {job_number}", classes="summary-item"),
            Static(f"Date Received: {date_received}", classes="summary-item"),
            Static(f"Date Due: {date_due}", classes="summary-item"),
            Static(
                f"Media Files Found: {len(self.media_files)}",
                classes="summary-item",
            ),
            Static(f"Tasks to Create: {len(tasks)}", classes="summary-item"),
        ]

        if tasks:
            summary_widgets.append(Label("Tasks:", classes="summary-title"))
            for i, task in enumerate(tasks):
                summary_widgets.append(
                    Static(
                        f"{i+1}. {task.get('file_name', 'N/A')} - {task.get('job_type', 'N/A')} ({task.get('quantity', 'N/A')} min)",
                        classes="summary-item",
                    )
                )

        # Mount all summary widgets
        for widget in summary_widgets:
            form.mount(widget)

        # Update button states
        self.update_button_states()

        # Force refresh
        self.refresh(layout=True)

    def extract_job_number(self, file_path: str) -> str:
        """Extract job number from file path"""
        return extract_job_number(file_path)

    def extract_date_due(self, file_path: str) -> str:
        """Extract due date from file path"""
        date_due = extract_date_due(file_path)
        if date_due:
            # Convert to proper date format
            date_format = self.app.transcriptor.config.date_format
            try:
                # Try to parse various date formats
                for fmt in ["%m/%d", "%m-%d", "%m.%d"]:
                    try:
                        date_obj = datetime.strptime(date_due, fmt)
                        current_year = datetime.now().year
                        full_date = date_obj.replace(year=current_year)
                        return full_date.strftime(date_format)
                    except ValueError:
                        continue
            except:
                pass
        return ""

    def create_job_dir(
        self,
        client_name: str,
        job_number: str,
        date_received: str,
        date_due: str,
    ) -> Path:
        """
        Create a job directory

        Arguments:
            client_name: Client name
            job_num: Job number
            date_rec: Date received
            date_due: Date due

        Returns:
            Job directory path object
        """
        date_format = self.app.transcriptor.config.date_format
        date_received_obj = std(date_received, date_format)
        date_due_obj = std(date_due, date_format)

        job_dir = (
            self.app.transcriptor.base_dir
            / "clients"
            / sc(client_name)
            / f"{date_received_obj.year}"
            / f"{date_received_obj.strftime('%B')}"
            / f"{date_received_obj.strftime('%d_%a')}_{job_number}_DUE_{date_due_obj.strftime('%d_%a')}"
        )
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    @on(Button.Pressed, "#browse-file")
    def browse_file(self):
        """Open file browser (placeholder - in real implementation, use textual-filebrowser)"""
        # For now, we'll just focus on the input field
        self.query_one("#job-file-path", Input).focus()

    @on(Button.Pressed, "#prev-step")
    def previous_step(self):
        """Go to previous step"""
        if self.step > 1:
            self.step -= 1
            if self.step == 1:
                self.load_step_1()
            elif self.step == 2:
                self.load_step_2()
            elif self.step == 3:
                self.load_step_3()

            # Update button states
            self.update_button_states()

    @on(Button.Pressed, "#next-step")
    def next_step(self):
        """Process current step and move to next"""
        if self.step == 1:
            if not self.process_step_1():
                return
            self.load_step_2()
        elif self.step == 2:
            if not self.process_step_2():
                return
            self.load_step_3()
        elif self.step == 3:
            if not self.process_step_3():
                return
            self.current_media_index += 1
            self.load_current_media_form()
        elif self.step == 4:
            self.create_job()
            return

        self.update_button_states()

    @on(Button.Pressed, "#cancel-add-job")
    def cancel_add_job(self):
        """Cancel job creation"""
        self.dismiss()

    def process_step_1(self) -> bool:
        """Process step 1: Validate job file"""
        file_input = self.query_one("#job-file-path", Input)
        file_path = file_input.value.strip("'").strip('"').strip()

        if not file_path:
            self.app.notify("Please enter a job file path", severity="error")
            return False

        path = Path(file_path)
        if not path.exists():
            self.app.notify(
                "File or directory does not exist", severity="error"
            )
            return False

        self.job_data["job_file"] = file_path
        return True

    def process_step_2(self) -> bool:
        """Process step 2: Validate job information"""
        client_select = self.query_one("#client-select", Select)
        job_number_input = self.query_one("#job-number", Input)
        date_received_input = self.query_one("#date-received", Input)
        date_due_input = self.query_one("#date-due", Input)

        if not client_select.value:
            self.app.notify("Please select a client", severity="error")
            return False

        if not job_number_input.value.strip():
            self.app.notify("Please enter a job number", severity="error")
            return False

        # Basic date validation
        date_format = self.app.transcriptor.config.date_format
        try:
            datetime.strptime(date_received_input.value, date_format)
            datetime.strptime(date_due_input.value, date_format)
        except ValueError:
            self.app.notify(
                f"Invalid date format. Use: {date_format}", severity="error"
            )
            return False

        # Get client name
        client_id = client_select.value
        clients = self.app.transcriptor.api.get_clients(
            conditions={"id": [("=", client_id)]}
        )
        client_name = clients[0]["name"] if clients else "Unknown"

        self.job_data.update(
            {
                "client_id": client_id,
                "client_name": client_name,
                "job_number": job_number_input.value,
                "date_received": date_received_input.value,
                "date_due": date_due_input.value,
            }
        )

        return True

    def process_step_3(self) -> bool:
        """Process step 3: Process current media file"""
        if self.current_media_index >= len(self.media_files):
            return True

        # Use the current media index to get the right IDs
        media_suffix = f"-{self.current_media_index}"

        process_checkbox = self.query_one(
            f"#process-file{media_suffix}", Checkbox
        )
        if not process_checkbox.value:
            return True  # Skip this file

        job_type_select = self.query_one(f"#job-type{media_suffix}", Select)
        quantity_input = self.query_one(f"#quantity{media_suffix}", Input)
        template_select = self.query_one(
            f"#job-template{media_suffix}", Select
        )
        note_textarea = self.query_one(f"#note{media_suffix}", TextArea)

        try:
            quantity = float(quantity_input.value)
        except ValueError:
            self.app.notify("Invalid quantity value", severity="error")
            return False

        current_file = self.media_files[self.current_media_index]

        task_data = {
            "file_path": str(current_file),
            "file_name": current_file.name,
            "job_type": job_type_select.value,
            "quantity": quantity,
            "template": template_select.value,
            "note": note_textarea.text,
        }

        if "tasks" not in self.job_data:
            self.job_data["tasks"] = []
        self.job_data["tasks"].append(task_data)

        return True

    def create_job(self):
        """Create the job using the collected data"""
        try:
            # Prepare job_callback
            def job_callback(job_file):
                return {
                    "client_id": self.job_data["client_id"],
                    "job_number": self.job_data["job_number"],
                    "date_received": self.job_data["date_received"],
                    "date_due": self.job_data["date_due"],
                }

            # Prepare task_callback
            task_mapping = {
                task["file_path"]: task
                for task in self.job_data.get("tasks", [])
            }

            def task_callback(task_file):
                task_info = task_mapping.get(str(task_file))
                if not task_info:
                    return None

                return {
                    "work_on_file": "yes",  # Already filtered by process_step_3
                    "job_type": task_info["job_type"],
                    "total_quantity": task_info[
                        "quantity"
                    ],  # This would ideally be the actual media duration
                    "quantity": task_info["quantity"],
                    "job_template": task_info["template"],
                    "note": task_info["note"],
                }

            # Create the job
            self.app.transcriptor.create_job(
                job_file=self.job_data["job_file"],
                job_callback=job_callback,
                task_callback=task_callback,
            )

            self.app.notify("Job created successfully!")
            self.dismiss()

        except Exception as e:
            self.app.notify(f"Error creating job: {str(e)}", severity="error")

    def update_button_states(self):
        """Update button states based on current step"""
        prev_button = self.query_one("#prev-step", Button)
        next_button = self.query_one("#next-step", Button)

        # Update previous button
        prev_button.disabled = self.step == 1

        # Update next button text
        if (
            self.step == 3
            and self.current_media_index == len(self.media_files) - 1
        ):
            next_button.label = "Review"
        elif self.step == 4:
            next_button.label = "Create Job"
        else:
            next_button.label = "Next"


class JobEditScreen(ModalScreen):
    """Screen for editing job properties with all attributes"""

    def __init__(self, job_data: Dict):
        super().__init__()
        self.job_data = job_data
        self.original_data = job_data.copy()

    def compose(self) -> ComposeResult:
        with Container(id="job-edit"):
            yield Label(
                f"Edit Job: {self.job_data.get('job_number', '')}",
                classes="edit-title",
            )

            # Use a ScrollableContainer to handle overflow
            with VerticalScroll(id="job-form-container"):
                with Vertical():
                    yield Label("Job Number:")
                    yield Input(
                        value=self.job_data.get("job_number", ""),
                        id="job_number",
                    )

                    yield Label("Client ID:")
                    yield Input(
                        value=str(self.job_data.get("client_id", "")),
                        id="client_id",
                    )

                    yield Label("Status:")
                    statuses = ["Pending", "Done"]
                    current_status = self.job_data.get("status", "Pending")
                    yield Select(
                        [(s, s) for s in statuses],
                        value=current_status,
                        id="status",
                    )

                    yield Label("Amount Paid:")
                    yield Input(
                        value=str(self.job_data.get("amount_paid", "")),
                        id="amount_paid",
                    )

                    yield Label("Job Type:")
                    job_types = [
                        "Normal",
                        "Expedite",
                        "Interpreted",
                        "normal",
                        "expedite",
                        "interpreted",
                    ]
                    current_job_type = self.job_data.get("job_type", "Normal")
                    yield Select(
                        [(jt, jt) for jt in job_types],
                        value=current_job_type,
                        id="job_type",
                    )

                    yield Label("Date Submitted:")
                    date_submitted = self.job_data.get("date_submitted", "")
                    yield Input(
                        value=date_submitted if date_submitted else "",
                        id="date_submitted",
                    )

                    yield Label("Job Rate:")
                    yield Input(
                        value=str(self.job_data.get("job_rate", "")),
                        id="job_rate",
                    )

                    yield Label("Date Received:")
                    yield Input(
                        value=self.job_data.get("date_received", ""),
                        id="date_received",
                    )

                    yield Label("Date Due:")
                    yield Input(
                        value=self.job_data.get("date_due", ""), id="date_due"
                    )

                    yield Label("Quantity:")
                    yield Input(
                        value=str(self.job_data.get("quantity", "")),
                        id="quantity",
                    )

                    yield Label("Total Quantity:")
                    yield Input(
                        value=str(self.job_data.get("total_quantity", "")),
                        id="total_quantity",
                    )

                    yield Label("Amount:")
                    yield Input(
                        value=str(self.job_data.get("amount", "")),
                        id="amount",
                    )

                    yield Label("Job Path:")
                    yield Input(
                        value=self.job_data.get("job_path", ""), id="job_path"
                    )

                    yield Label("Note:")
                    yield TextArea(self.job_data.get("note", ""), id="note")

            with Horizontal(id="edit-buttons"):
                yield Button("Save", variant="primary", id="save-job")
                yield Button("Cancel", variant="default", id="cancel-edit")

    @on(Button.Pressed, "#save-job")
    def save_job(self):
        # Collect updated values
        updated_values = {}

        # Text input fields
        text_fields = [
            "job_number",
            "date_received",
            "date_due",
            "date_submitted",
            "job_path",
        ]
        for field in text_fields:
            widget = self.query_one(f"#{field}", Input)
            updated_values[field] = widget.value
        updated_values["date_submitted"] = (
            updated_values["date_submitted"] or None
        )

        # Numeric fields
        numeric_fields = [
            "client_id",
            "total_quantity",
            "quantity",
            "job_rate",
            "amount",
            "amount_paid",
        ]
        for field in numeric_fields:
            widget = self.query_one(f"#{field}", Input)
            try:
                if widget.value.strip():  # Only convert if not empty
                    if field == "client_id":
                        updated_values[field] = int(widget.value)
                    else:
                        updated_values[field] = float(widget.value)
                else:
                    updated_values[field] = 0.0 if field != "client_id" else 0
            except ValueError:
                self.app.notify(
                    f"Invalid value for {field}!", severity="error"
                )
                return

        # Select fields
        select_fields = ["job_type", "status"]
        for field in select_fields:
            widget = self.query_one(f"#{field}", Select)
            updated_values[field] = widget.value

        # TextArea field
        note_widget = self.query_one("#note", TextArea)
        updated_values["note"] = note_widget.text

        # Update job in database
        job_id = self.job_data.get("id")
        if job_id:
            conditions = {"id": [("=", job_id)]}
            self.app.transcriptor.update_jobs(
                conditions=conditions, values=updated_values
            )
            self.app.notify("Job updated successfully!")
            self.dismiss()

    @on(Button.Pressed, "#cancel-edit")
    def cancel_edit(self):
        self.dismiss()


class JobCheckbox(Checkbox):
    """Checkbox for job selection with job data"""

    def __init__(self, job_data: Dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_data = job_data


class JobsTable(Container):
    """Custom table widget for jobs with checkboxes"""

    def __init__(self):
        super().__init__()
        self.selected_jobs = []
        self.checkboxes = []

    def compose(self) -> ComposeResult:
        yield DataTable(id="jobs-data-table")
        yield Static(id="jobs-selection-info")

    def on_mount(self):
        table = self.query_one("#jobs-data-table", DataTable)
        table.clear()
        table.add_columns(
            "Select",
            "ID",
            "Job Number",
            "Client",
            "Status",
            "Date Due",
            "Job Type",
            "Quantity",
            "Amount",
        )

        # Load jobs
        jobs = self.app.transcriptor.api.get_jobs()
        self.jobs_data = jobs

        for job in jobs:
            client_name = (
                job.get("client").name
                if hasattr(job.get("client"), "name")
                else str(job.get("client"))
            )
            table.add_row(
                "□",  # Checkbox placeholder
                str(job.get("id")),
                job.get("job_number"),
                client_name,
                job.get("date_received"),
                job.get("date_due"),
                job.get("job_type"),
                job.get("status"),
                job.get("date_submitted"),
                str(job.get("quantity")),
                f"${job.get('amount', 0):.2f}",
            )

    @on(DataTable.CellSelected)
    def handle_cell_selection(self, event: DataTable.CellSelected):
        if event.coordinate.column == 0:  # Checkbox column
            table = event.data_table
            row_key = event.coordinate.row

            # Toggle selection
            current_value = table.get_cell(row_key, 0)
            if current_value == "□":
                table.update_cell(row_key, "select", "✓")
                # Add to selected jobs
                job_id = int(table.get_cell(row_key, "id"))
                if job_id not in self.selected_jobs:
                    self.selected_jobs.append(job_id)
            else:
                table.update_cell(row_key, "select", "□")
                # Remove from selected jobs
                job_id = int(table.get_cell(row_key, "id"))
                if job_id in self.selected_jobs:
                    self.selected_jobs.remove(job_id)

            # Update selection info
            self.update_selection_info()

    def update_selection_info(self):
        info = self.query_one("#jobs-selection-info", Static)
        info.update(f"Selected: {len(self.selected_jobs)} jobs")

    def get_selected_jobs_data(self):
        """Get full data for selected jobs"""
        selected_data = []
        for job in self.jobs_data:
            if job.get("id") in self.selected_jobs:
                # Extract client name
                if hasattr(job, "client"):
                    client_name = (
                        job.client.name
                        if hasattr(job.client, "name")
                        else str(job.client)
                    )
                    job_dict = (
                        job.__dict__
                        if hasattr(job, "__dict__")
                        else dict(job)
                    )
                    job_dict["client_name"] = client_name
                    selected_data.append(job_dict)
                else:
                    job_dict = dict(job)
                    job_dict["client_name"] = job.get(
                        "client_name", "Unknown"
                    )
                    selected_data.append(job_dict)
        return selected_data


# Update the SQL Query Screen to use CLI-style raw queries
class SQLQueryScreen(ModalScreen):
    """Screen for executing raw SQL queries in CLI style"""

    def compose(self) -> ComposeResult:
        with Container(id="sql-query"):
            yield Label("Raw SQL Query (CLI Style)", classes="query-title")
            yield Label(
                "Example: show jobs -r 'WHERE id > 120'",
                classes="query-subtitle",
            )

            with Horizontal():
                yield Select(
                    [
                        ("show jobs", "show_jobs"),
                        ("show clients", "show_clients"),
                        ("show rates", "show_rates"),
                        ("update jobs", "update_jobs"),
                        ("update clients", "update_clients"),
                        ("update rates", "update_rates"),
                        ("delete jobs", "delete_jobs"),
                        ("delete clients", "delete_clients"),
                    ],
                    id="sql-command",
                )
                yield Input(
                    placeholder="-r 'WHERE condition'", id="sql-raw-arg"
                )

            with Horizontal(id="query-buttons"):
                yield Button("Execute", variant="primary", id="execute-sql")
                yield Button("Clear", variant="default", id="clear-sql")
                yield Button("Close", variant="default", id="close-sql")

            yield DataTable(id="sql-results")
            yield Static(id="sql-status")

    def on_mount(self):
        table = self.query_one("#sql-results", DataTable)
        table.clear()

    @on(Button.Pressed, "#execute-sql")
    def execute_sql(self):
        command_select = self.query_one("#sql-command", Select)
        raw_input = self.query_one("#sql-raw-arg", Input)
        status = self.query_one("#sql-status", Static)
        table = self.query_one("#sql-results", DataTable)

        command = command_select.value
        raw_arg = raw_input.value.strip()

        if not command:
            status.update("Please select a command")
            return

        try:
            # Parse the raw argument to extract the SQL
            raw_sql = ""
            if raw_arg.startswith("-r") or raw_arg.startswith("--raw"):
                # Extract the SQL part after -r/--raw
                parts = raw_arg.split("'", 1)
                if len(parts) > 1:
                    raw_sql = parts[1].rsplit("'", 1)[0]
                else:
                    # Try without quotes
                    parts = raw_arg.split()
                    if len(parts) > 1:
                        raw_sql = " ".join(parts[1:])

            table.clear()
            status.update(f"Executing: {command} {raw_arg}")

            if command == "show_jobs":
                results = self.app.transcriptor.api.get_jobs(
                    raw_sql_stmt=raw_sql
                )
                self.display_results(
                    results,
                    ["ID", "Job Number", "Client", "Status", "Date Due"],
                )

            elif command == "show_clients":
                results = self.app.transcriptor.api.get_clients(
                    raw_sql_stmt=raw_sql
                )
                self.display_results(results, ["ID", "Name", "Email"])

            elif command == "show_rates":
                results = self.app.transcriptor.api.get_rates(
                    raw_sql_stmt=raw_sql
                )
                self.display_results(
                    results,
                    ["ID", "Client", "Normal", "Expedite", "Interpreted"],
                )

            elif command == "update_jobs":
                self.app.transcriptor.update_jobs(raw_sql_stmt=raw_sql)
                status.update("Jobs updated successfully")

            elif command == "update_clients":
                self.app.transcriptor.api.update_clients(raw_sql_stmt=raw_sql)
                status.update("Clients updated successfully")

            elif command == "update_rates":
                self.app.transcriptor.api.update_rates(raw_sql_stmt=raw_sql)
                status.update("Rates updated successfully")

            elif command == "delete_jobs":
                self.app.transcriptor.delete_jobs(raw_sql_stmt=raw_sql)
                status.update("Jobs deleted successfully")

            elif command == "delete_clients":
                self.app.transcriptor.delete_clients(raw_sql_stmt=raw_sql)
                status.update("Clients deleted successfully")

        except Exception as e:
            status.update(f"Error: {str(e)}")
            self.app.notify(f"SQL Error: {str(e)}", severity="error")

    def display_results(self, results, columns):
        table = self.query_one("#sql-results", DataTable)
        table.clear()
        table.add_columns(*columns)

        if not results:
            table.add_row("No results found")
            return

        for result in results:
            if hasattr(result, "__dict__"):
                row_data = [
                    str(getattr(result, col.lower().replace(" ", "_"), ""))
                    for col in columns
                ]
            elif isinstance(result, dict):
                row_data = [
                    str(result.get(col.lower().replace(" ", "_"), ""))
                    for col in columns
                ]
            else:
                row_data = [str(result)]
            table.add_row(*row_data)

    @on(Button.Pressed, "#clear-sql")
    def clear_sql(self):
        self.query_one("#sql-raw-arg", Input).value = ""
        self.query_one("#sql-results", DataTable).clear()
        self.query_one("#sql-status", Static).update("")

    @on(Button.Pressed, "#close-sql")
    def close_sql(self):
        self.dismiss()


# Update Configuration Screen to fix the themes issue
class ConfigurationScreen(ModalScreen):
    """Screen for editing configuration"""

    def compose(self) -> ComposeResult:
        with Container(id="config-edit"):
            yield Label("Edit Configuration", classes="config-title")

            with Vertical():
                yield Label("Base Directory:")
                yield Input(
                    value=self.app.transcriptor.config.base_dir, id="base_dir"
                )

                yield Label("Date Format:")
                yield Input(
                    value=self.app.transcriptor.config.date_format,
                    id="date_format",
                )

                yield Label("Invoice Theme:")
                # Fix: Import invoice_template_themes at the top
                themes = invoice_template_themes()
                select = Select(
                    [(theme, theme) for theme in themes], id="invoice_theme"
                )
                # Set current value
                try:
                    select.value = self.app.transcriptor.config.invoice_theme
                except:
                    pass
                yield select

            with Horizontal(id="config-buttons"):
                yield Button("Save", variant="primary", id="save-config")
                yield Button("Cancel", variant="default", id="cancel-config")

    @on(Button.Pressed, "#save-config")
    def save_config(self):
        base_dir = self.query_one("#base_dir", Input).value
        date_format = self.query_one("#date_format", Input).value
        invoice_theme_select = self.query_one("#invoice_theme", Select)
        invoice_theme = (
            invoice_theme_select.value
            if invoice_theme_select.value
            else "default"
        )

        # Update config
        self.app.transcriptor.config.base_dir = base_dir
        self.app.transcriptor.config.date_format = date_format
        self.app.transcriptor.config.invoice_theme = invoice_theme

        # Save to file
        self.app.transcriptor.save_config()
        self.app.notify("Configuration saved successfully!")
        self.dismiss()
        # Refresh config display
        self.app.load_config_display()

    @on(Button.Pressed, "#cancel-config")
    def cancel_config(self):
        self.dismiss()


# Update the main app class
class TranscriptorTUI(App):
    """Main TUI application for Transcriptor"""

    CSS_PATH = "tui.css"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f1", "show_help", "Help"),
        Binding("i", "generate_invoice", "Generate Invoice"),
        Binding("r", "refresh", "Refresh"),
    ]

    selected_jobs = reactive([])

    def __init__(self):
        super().__init__()
        self.transcriptor = Transcriptor()
        self.jobs_table = None

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard", id="dashboard"):
                yield Container(
                    Horizontal(
                        Button("Add Job", id="add-job"),
                        classes="dashboard-toolbar",
                    ),
                    Label("Pending Jobs", classes="section-title"),
                    DataTable(id="pending-jobs-table"),
                    classes="dashboard-container",
                )

            with TabPane("All Jobs", id="all-jobs"):
                yield Container(
                    Horizontal(
                        Button("Edit Selected", id="edit-job"),
                        Button("Delete Selected", id="delete-job"),
                        Button("Generate Invoice", id="generate-invoice-btn"),
                        Button("Refresh", id="refresh-jobs"),
                        classes="jobs-toolbar",
                    ),
                    Static("Selected: 0 jobs", id="jobs-selection-info"),
                    DataTable(id="all-jobs-table"),
                    classes="jobs-container",
                )

            with TabPane("Cutoffs", id="cutoffs"):
                yield Container(
                    DataTable(id="cutoffs-table"), classes="cutoffs-container"
                )

            with TabPane("Clients", id="clients"):
                yield Container(
                    Horizontal(
                        Button("Add Client", id="add-client"),
                        Button("Edit Client", id="edit-client"),
                        Button("Delete Client", id="delete-client"),
                        Button("Refresh", id="refresh-clients"),
                        classes="clients-toolbar",
                    ),
                    DataTable(id="clients-table"),
                    classes="clients-container",
                )

            with TabPane("Rates", id="rates"):
                yield Container(
                    Horizontal(
                        Button("Edit Rates", id="edit-rates"),
                        Button("Refresh", id="refresh-rates"),
                        classes="rates-toolbar",
                    ),
                    DataTable(id="rates-table"),
                    classes="rates-container",
                )

            with TabPane("Configuration", id="configuration"):
                yield Container(
                    Button("Edit Configuration", id="edit-config"),
                    Static(id="config-display"),
                    classes="config-container",
                )

            with TabPane("SQL", id="sql"):
                yield Container(
                    Button("Open SQL Query", id="open-sql"),
                    classes="sql-container",
                )

        yield Footer()

    def on_mount(self) -> None:
        self.title = "Transcriptor TUI"
        self.sub_title = "Transcription Management System"
        self.load_dashboard()
        self.load_all_jobs()
        self.load_cutoffs()
        self.load_clients()
        self.load_rates()
        self.load_config_display()

    def load_dashboard(self):
        """Load pending jobs for dashboard with menu icons"""
        table = self.query_one("#pending-jobs-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            ("⋮", "⋮"),
            ("ID", "ID"),
            "Job Number",
            "Client",
            "Date Due",
            "Job Type",
            "Quantity",
            "Amount",
        )

        jobs = self.transcriptor.api.get_jobs(
            conditions={"status": [("=", "Pending")]}
        )
        self.dashboard_jobs_data = jobs  # Store for reference

        for job in jobs:
            client_name = (
                job.get("client").name
                if hasattr(job.get("client"), "name")
                else str(job.get("client"))
            )
            table.add_row(
                "⋯",  # Menu icon (three dots)
                str(job.get("id")),
                job.get("job_number"),
                client_name,
                job.get("date_due"),
                job.get("job_type"),
                str(job.get("quantity")),
                f"${job.get('amount', 0):.2f}",
            )

    def load_all_jobs(self):
        """Load all jobs with checkboxes and menu icons"""
        table = self.query_one("#all-jobs-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            ("⋮", "menu"),
            ("Select", "select"),
            ("ID", "id"),
            ("Job Number", "job number"),
            ("Client", "client"),
            ("Status", "status"),
            ("Date Due", "date due"),
            ("Job Type", "job type"),
            ("Quantity", "quantity"),
            ("Amount", "amount"),
        )

        jobs = self.transcriptor.api.get_jobs()
        self.all_jobs_data = jobs  # Store for reference

        for job_idx, job in enumerate(jobs):
            client_name = (
                job.get("client").name
                if hasattr(job.get("client"), "name")
                else str(job.get("client"))
            )
            table.add_row(
                "⋯",  # Menu icon (three dots)
                "□",  # Checkbox placeholder
                str(job.get("id")),
                job.get("job_number"),
                client_name,
                job.get("status"),
                job.get("date_due"),
                job.get("job_type"),
                str(job.get("quantity")),
                f"${job.get('amount', 0):.2f}",
                key=str(job_idx),
            )

        # Reset selection
        self.selected_jobs = []
        self.update_jobs_selection_info()

    @on(DataTable.CellSelected, "#pending-jobs-table")
    def handle_dashboard_menu_click(self, event: DataTable.CellSelected):
        """Handle menu icon click in dashboard"""
        table = event.data_table
        row_key = event.cell_key.row_key
        column_key = event.cell_key.column_key

        # Only handle clicks in the menu column (first column)
        if column_key == "⋮":
            # Find the job data for this row
            job_id_cell = table.get_cell(row_key, "ID")
            if job_id_cell:
                try:
                    job_id = int(job_id_cell)
                    # Find the job in our stored data
                    job_data = None
                    for job in self.dashboard_jobs_data:
                        if job.get("id") == job_id:
                            job_data = job
                            break

                    if job_data:
                        self.push_screen(
                            JobContextMenu(job_data, from_dashboard=True)
                        )
                except (ValueError, KeyError):
                    self.notify("Could not find job data", severity="error")

    @on(DataTable.CellSelected, "#all-jobs-table")
    def handle_all_jobs_cell_click(self, event: DataTable.CellSelected):
        """Handle cell clicks in all jobs table"""
        table = event.data_table
        row_key = event.cell_key.row_key
        column_key = event.cell_key.column_key

        if column_key == "menu":  # Menu icon column
            # Find the job data for this row
            job_id_cell = table.get_cell(row_key, "id")
            if job_id_cell:
                try:
                    job_id = int(job_id_cell)
                    # Find the job in our stored data
                    job_data = None
                    for job in self.all_jobs_data:
                        if job.get("id") == job_id:
                            job_data = job
                            break

                    if job_data:
                        self.push_screen(
                            JobContextMenu(job_data, from_dashboard=False)
                        )
                except (ValueError, KeyError):
                    self.notify("Could not find job data", severity="error")

        elif column_key == "select":  # Checkbox column
            # Get job ID from the row
            job_id = int(table.get_cell(row_key, "id"))

            # Toggle selection
            current_value = table.get_cell(row_key, "select")
            if current_value == "□":
                table.update_cell(row_key, "select", "✓")
                if job_id not in self.selected_jobs:
                    self.selected_jobs.append(job_id)
            else:
                table.update_cell(row_key, "select", "□")
                if job_id in self.selected_jobs:
                    self.selected_jobs.remove(job_id)

            self.update_jobs_selection_info()

    def update_jobs_selection_info(self):
        """Update the selection info display"""
        info = self.query_one("#jobs-selection-info", Static)
        info.update(f"Selected: {len(self.selected_jobs)} jobs")

    def get_selected_jobs_data(self):
        """Get full data for selected jobs"""
        selected_data = []
        for job in self.all_jobs_data:
            if hasattr(job, "id"):
                job_id = job.id
            else:
                job_id = job.get("id")

            if job_id in self.selected_jobs:
                # Extract client name
                if hasattr(job, "client"):
                    client_name = (
                        job.client.name
                        if hasattr(job.client, "name")
                        else str(job.client)
                    )
                    job_dict = (
                        job.__dict__
                        if hasattr(job, "__dict__")
                        else dict(job)
                    )
                    job_dict["client_name"] = client_name
                    selected_data.append(job_dict)
                else:
                    job_dict = dict(job)
                    job_dict["client_name"] = job.get(
                        "client_name", "Unknown"
                    )
                    selected_data.append(job_dict)
        return selected_data

    def confirm_delete(self, item_type: str) -> bool:
        """Simple confirmation dialog"""
        # In a real implementation, you'd show a proper confirmation dialog
        # For now, we'll assume confirmation
        return True

    def load_cutoffs(self):
        """Load cutoff dates"""
        table = self.query_one("#cutoffs-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            ("Cutoff Date", "cutoff-date"), ("Deposit Date", "deposit-date")
        )

        try:
            cutoffs = self.transcriptor.load_cutoffs(as_str=True)
            for cutoff in cutoffs[1:]:  # Skip header
                if len(cutoff) >= 2:
                    table.add_row(cutoff[0], cutoff[1])
        except Exception as e:
            table.add_row("Error loading cutoffs", str(e))

    def load_clients(self):
        """Load clients"""
        table = self.query_one("#clients-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Name", "Email")

        clients = self.transcriptor.api.get_clients()
        for client in clients:
            table.add_row(
                str(client.get("id")), client.get("name"), client.get("email")
            )

    def load_rates(self):
        """Load client rates"""
        table = self.query_one("#rates-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Client", "Normal", "Expedite", "Interpreted")

        rates = self.transcriptor.api.get_rates()
        for rate in rates:
            table.add_row(
                rate.get("client_name"),
                f"${rate.get('normal', 0):.2f}",
                f"${rate.get('expedite', 0):.2f}",
                f"${rate.get('interpreted', 0):.2f}",
            )

    def load_config_display(self):
        """Load current configuration for display"""
        config_display = self.query_one("#config-display", Static)
        config = self.transcriptor.config
        display_text = f"""
Base Directory: {config.base_dir}
Date Format: {config.date_format}
Invoice Theme: {config.invoice_theme}
        """
        config_display.update(display_text)

    @on(Button.Pressed, "#add-job")
    def open_add_job_screen(self):
        """Open the add job screen"""
        self.push_screen(AddJobScreen())

    @on(Button.Pressed, "#edit-job")
    def edit_selected_job(self):
        """Edit the first selected job"""
        if not self.selected_jobs:
            self.notify("No job selected!", severity="error")
            return

        job_id = self.selected_jobs[0]
        jobs = self.transcriptor.api.get_jobs(
            conditions={"id": [("=", job_id)]}
        )
        if jobs:
            job_data = jobs[0]
            if hasattr(job_data, "__dict__"):
                job_data = job_data.__dict__
            self.push_screen(JobEditScreen(job_data))

    @on(Button.Pressed, "#delete-job")
    def delete_selected_jobs(self):
        """Delete selected jobs"""
        if not self.selected_jobs:
            self.notify("No jobs selected!", severity="error")
            return

        # Confirm deletion
        if self.confirm_delete("jobs"):
            for job_id in self.selected_jobs:
                self.transcriptor.delete_jobs(
                    conditions={"id": [("=", job_id)]}
                )
            self.selected_jobs.clear()
            self.load_all_jobs()
            self.notify("Jobs deleted successfully!")

    @on(Button.Pressed, "#generate-invoice-btn")
    def generate_invoice_from_button(self):
        """Generate invoice from button click"""
        self.action_generate_invoice()

    @on(Button.Pressed, "#refresh-jobs")
    def refresh_jobs(self):
        self.load_all_jobs()
        self.load_dashboard()
        self.notify("Jobs refreshed!")

    @on(Button.Pressed, "#refresh-clients")
    def refresh_clients(self):
        self.load_clients()
        self.notify("Clients refreshed!")

    @on(Button.Pressed, "#refresh-rates")
    def refresh_rates(self):
        self.load_rates()
        self.notify("Rates refreshed!")

    @on(Button.Pressed, "#edit-config")
    def edit_configuration(self):
        self.push_screen(ConfigurationScreen())

    @on(Button.Pressed, "#open-sql")
    def open_sql_query(self):
        self.push_screen(SQLQueryScreen())

    def action_generate_invoice(self):
        """Generate invoice from selected jobs"""
        if not self.selected_jobs:
            self.notify("No jobs selected for invoice!", severity="error")
            return

        # Get full job data for selected jobs
        selected_jobs_data = self.get_selected_jobs_data()

        if not selected_jobs_data:
            self.notify("No valid jobs selected!", severity="error")
            return

        # Check if jobs are from multiple clients
        clients = set(job.get("client_name") for job in selected_jobs_data)

        if len(clients) > 1:
            # Show client selection screen
            self.push_screen(
                ClientSelectionScreen(list(clients), selected_jobs_data)
            )
        else:
            # Generate invoice directly
            client_name = list(clients)[0]
            html, client_name = self.transcriptor.generate_invoice(
                selected_jobs_data
            )
            if html and client_name:
                self.push_screen(
                    InvoicePreviewScreen(
                        html, client_name, selected_jobs_data
                    )
                )
            else:
                self.notify("Failed to generate invoice!", severity="error")

    def action_refresh(self):
        """Refresh all data"""
        self.load_dashboard()
        self.load_all_jobs()
        self.load_cutoffs()
        self.load_clients()
        self.load_rates()
        self.load_config_display()
        self.notify("All data refreshed!")


def main():
    app = TranscriptorTUI()
    app.run()


if __name__ == "__main__":
    main()
