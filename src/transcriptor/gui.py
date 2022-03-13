import PySimpleGUI as sg
import shutil
import zipfile
from transcriptor.methods import get_clients, get_jobs, get_total_amount, get_total_amount_paid, settings, create_task, get_template_file, save_job_to_file, update_job, get_settings,save_settings
from transcriptor.api import add_client, get_client_object, create_invoice
from transcriptor.utils import parse_job_due_date, parse_job_number, get_media_files, get_media_duration, custom_round, deformat_date
from datetime import date
from transcriptor.settings import Settings
from transcriptor.profile import Profile

CLIENTS_FOLDER, WORKS_FOLDER, JOBS_FOLDER, CONFIG_FOLDER, RESOURCES_FOLDER = (
    settings.clients_folder,
    settings.works_folder,
    settings.jobs_folder,
    settings.config_folder,
    settings.resources_folder,
)

def get_clients_list():
    clients = [client.name for client in get_clients()]
    clients.append('All')
    return clients

def get_jobs_list(client=''):
    try:
        if client in ('All'):
            j = get_jobs()
            amount, amount_paid = get_total_amount(j.all_jobs()), get_total_amount_paid(j.all_jobs())
            headers =  j.headers()
            jobs = [job.to_dict() for job in j.all_jobs()]
        elif client == '':
            return [], []
        else:
            j = get_jobs(client)
            amount, amount_paid = get_total_amount(j.jobs()), get_total_amount_paid(j.jobs())
            headers =  j.headers()
            jobs = [job.to_dict() for job in j.jobs()]
    except IndexError as e:
        return [],[]

    job_lists = []
    headings = [h.replace('_', " ").title() for h in headers]
    for job in jobs:
        job_lists.append(list(job.values()))
    job_lists = sorted(job_lists)
    # job_lists.insert(0,headings )
    job_lists.append(['','', '', '', '', '', '', '', '', amount, amount_paid,''])
    return job_lists, headings

def add_settings_window():
    def TextLabel(text): return sg.Text(text+':', justification='right', size=(15,1))
    settings = get_settings()

    layout = []
    for k, v in settings.to_dict().items():
        if not k == 'date_fmt':
            layout.append([TextLabel(k.replace('_', " ").title()), sg.Input(default_text=v, key=f"-{k.replace('_', '-').upper()}-"), sg.FolderBrowse()])
        else:
            layout.append([TextLabel(k.replace('_', " ").title()), sg.Input(default_text=v, key=f"-{k.replace('_', '-').upper()}-")])

    layout.append([sg.Button('Save', key='-SAVE-'), sg.Button('Exit')])
    window = sg.Window('Settings Window', layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            window.close()
            break
        if event in ['-SAVE-']:
            settings_dict = {}
            for k, v in values.items():
                if not k.startswith('Browse'):
                    settings_dict[k.strip('-').replace('-', '_').lower()] = v
            save_settings(Settings(**settings_dict))
            window.close()
            break

def add_profile_window():
    def TextLabel(text): return sg.Text(text+':', justification='right', size=(15,1))
    profile_file = CONFIG_FOLDER/'profile.json'
    try:
        profile = Profile.load(profile_file)
    except FileNotFoundError:
        profile = Profile(**{ 'area': '', 'country': '', 'first_name': '', 'last_name': '' })

    layout = []
    for k, v in profile.to_dict().items():
        layout.append([TextLabel(k.replace('_', ' ').title()), sg.Input(default_text=v, key=f"-{k.replace('_', '-').upper()}-")])
    layout.append([sg.Button('Save', key='-SAVE-'), sg.Button('Exit')])
    window = sg.Window('Profile Window', layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            window.close()
            break
        if event in ['-SAVE-']:
            profile_dict = {}
            for k, v in values.items():
                profile_dict[k.strip('-').replace('-', '_').lower()] = v
            Profile(**profile_dict).save(profile_file)
            window.close()
            break





def add_client_window():
    def TextLabel(text): return sg.Text(text+':', justification='right', size=(15,1))

    layout = [
        [TextLabel('Name'), sg.Input(key='-NEW-CLIENT-NAME-')],
        [TextLabel('Email'), sg.Input(key='-NEW-CLIENT-EMAIL-')],
        [sg.Button('Add'), sg.Button('Exit')]
    ]

    window = sg.Window('Addclient', layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            window.close()
            break
        if not values['-NEW-CLIENT-NAME-'] or not values['-NEW-CLIENT-EMAIL-']:
            sg.popup_no_buttons('Name and Email values required.', title="ERROR", background_color='red', keep_on_top=True, auto_close=True, auto_close_duration=2)
        else:
            add_client(values['-NEW-CLIENT-NAME-'], values['-NEW-CLIENT-EMAIL-'])
            sg.popup_quick(f"Client {values['-NEW-CLIENT-NAME-']} added successfully", title="SUCCESS", background_color='green', keep_on_top=True, auto_close=True, auto_close_duration=2)
            window.close()
            break

def add_job_window(client):
    def TextLabel(text): return sg.Text(text+':', justification='right', size=(15,1))
    layout = [
            [TextLabel('Job Path'), sg.Input(key='-JOB-FILE-', default_text='/home/kamikaze/.python/projects/transcriptor/tests/525529 Due 2.1 TT.zip'), sg.FileBrowse()],
            [sg.Frame('Job Info:', [[]], key='-JOB-INFO-')],
            [sg.Frame('Task Info:', [[]], key='-TASK-INFO-')],
            [sg.Button('Select', key='-Select-', visible=False, bind_return_key=True) ,sg.Button('Exit')]
    ]
    window = sg.Window('Add Job', layout, keep_on_top=True)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            window.close()
            break
        if event in ['Select', '-Select-']:
            if not values['-JOB-FILE-']:
                sg.popup_no_buttons('File path required.', title="ERROR", background_color='red', keep_on_top=True, auto_close=True, auto_close_duration=2)
            else:
                window.extend_layout(window['-JOB-INFO-'], create_job_info_form(values['-JOB-FILE-'], client=client) )
                while True:
                    event, values = window.read()
                    if event in (sg.WIN_CLOSED, 'Exit', 'Exit0'):
                        window.close()
                        break
                    if event in ('Create', '-Create-'):
                        job_folder_stem = "%s-%s_DUE_%s" % (values['-DATE-REC-'], values['-JOB-NUM-'], values['-DUE-DATE-'])
                        works_folder = WORKS_FOLDER
                        assert works_folder is not None
                        job_folder = works_folder / values['-CLIENT-'] / job_folder_stem
                        if not job_folder.exists():
                            job_folder.mkdir(parents=True, exist_ok=True)

                        try:
                            new_zip_file = shutil.copy2(values['-JOB-FILE-'], job_folder)
                        except (shutil.SameFileError, shutil.Error):
                            new_zip_file = zip_file
                        try:
                            zipfile.ZipFile(new_zip_file).extractall(job_folder)
                        except Exception as error:
                            sg.popup_error_with_traceback("ERROR:", error)

                        tasks = []

                        media_files = get_media_files(job_folder)
                        for media_file in media_files:
                            tasks.append(media_file)
                        window.extend_layout(window['-TASK-INFO-'], create_task_info_form(tasks) )
                        # task_window = create_task_info_form(tasks)
                        while True:
                            event, values = window.read()
                            if event in (sg.WIN_CLOSED, 'Exit', 'Exit0', 'Exit1'):
                                window.close()
                                break
                            if event in ['-CREATE-TASKS-']:
                                parse_task_info_values(values)
                                window.close()
                                break


def create_job_info_form(job_file_path, client):
    def TextLabel(text): return sg.Text(text+':', justification='right', size=(15,1))

    job_number = parse_job_number(job_file_path)
    date_due = parse_job_due_date(job_file_path)

    layout = [
        [TextLabel('Client'), sg.Input(key='-CLIENT-', default_text=client)],
        [TextLabel('Date Received'), sg.Input(key='-DATE-REC-', default_text=str(date.today().strftime("%Y-%m-%d")))],
        [TextLabel('Job Number'), sg.Input(key='-JOB-NUM-', default_text=job_number)],
        [TextLabel('Due Date '), sg.Input(key='-DUE-DATE-', default_text=date_due)],
        [sg.Button('Create', key='-Create-') ,sg.Button('Exit')]
    ]
    return layout

def create_task_info_form(l):
    def TextLabel(text): return sg.Text(text+':', justification='right')

    job_types = ['Normal', 'Interpreted', 'Expedite']
    template_types =  ["nd", "nh", "ne", "zd", "zh", "ze", "tt", "di", "me"]
    job_status = ['Pending', 'Done', 'Canceled']

    def task_layout(task, duration, idx):
        l = [ [TextLabel(task)],
            [
                sg.Checkbox("Workon", key=f"-WORKON-{idx}"),
                sg.Input(visible=False, disabled=True, default_text=duration, size=(6, 1), key=f"-TOT-QUANTITY-{idx}"),
                sg.Input(default_text=duration, size=(6, 1), key=f"-QUANTITY-{idx}"),
                sg.OptionMenu(job_types, key=f"-JOB-TYPE-{idx}"),
                sg.OptionMenu(template_types, key=f"-TEMP-TYPE-{idx}"),
                sg.OptionMenu(job_status, default_value=job_status[0], key=f"-STATUS-{idx}"),
                sg.Multiline(key=f"-NOTE-{idx}"),
            ],
        ]
        return l

    layout = [] 
    # return layout
    for idx, task in enumerate(l):
        total_quantity = get_media_duration(task)
        layout.extend(task_layout(str(task.stem), total_quantity, idx+1))

    layout.append([sg.Input(task.parent, visible=False, key='-JOB-PATH-')])
    layout.append([sg.Button('Create', key='-CREATE-TASKS-'), sg.Button('Exit')])
    return layout

def parse_task_info_values(info_values):
    job_path = info_values.pop( '-JOB-PATH-' )
    client = info_values.pop( '-CLIENT-' )
    date_received = info_values.pop( '-DATE-REC-' )
    date_due = info_values.pop( '-DUE-DATE-' )
    job_number = info_values.pop( '-JOB-NUM-' )
    job_file = info_values.pop( '-JOB-FILE-' )
    browse = info_values.pop('Browse')
    counter = 0

    lol = lambda lst, size: [lst[i:i+size] for i in range(0, len(lst), size)]
    tasks_list = lol(list(info_values.items()), 7) # 7 is number of dict values
    tasks = []

    for idx, task in enumerate(tasks_list):
        if task[0][1] == False:
            continue
        else:
            task_dict = dict(task)
            total_quantity = task_dict[f"-TOT-QUANTITY-{idx+1}"]
            quantity = task_dict[f"-QUANTITY-{idx+1}"]
            job_type = task_dict[f"-JOB-TYPE-{idx+1}"]
            template_type = task_dict[f"-TEMP-TYPE-{idx+1}"]
            status = task_dict[f"-STATUS-{idx+1}"]
            note = task_dict[f"-NOTE-{idx+1}"]

            task = create_task(
                date_received=date_received,
                job_number=job_number,
                job_type=job_type,
                total_quantity=float(total_quantity),
                quantity=float(quantity),
                date_due=date_due,
                job_path=job_path,
                note=note,
            )
            task.amount = custom_round(task.job_rate * task.quantity, 2)
            tasks.append(task)

            template_file = get_template_file(client, template_type)
            shutil.copy2(
                template_file,
                "%s/%s"
                % (job_path, "%s Due %s.doc" % (job_number, deformat_date(date_due))),
            )
    try:
        assert JOBS_FOLDER is not None
        job_bak = JOBS_FOLDER / client
        if job_bak.exists():
            shutil.copy2(JOBS_FOLDER / client, "%s.bak" % (job_bak))
    except Exception as error:
        sg.popup_error_with_traceback("ERROR:", error)
        # log could not create backup
    client_obj = get_client_object(client)
    save_job_to_file(client_obj, tasks, JOBS_FOLDER)
            # final_tasks.append(info_dict)

def update_job_window(headers, values, client):
    def TextLabel(text): return sg.Text(text+':', justification='right', size=(15,1))

    layout = []
    for idx, i in enumerate(headers):
        layout.append([TextLabel(i), sg.Input(default_text=values[idx])])

    layout.append([sg.Button('Update', key='-UPDATE-JOB-'), sg.Button('Exit')])
    window = sg.Window("Edit Job", layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Exit0', 'Exit1'):
            window.close()
            break

        if event in ['-UPDATE-JOB-']:
            updated_values = list(values.values())
            updated_job = dict(zip([h.lower().replace(" ", "_") for h in headers], updated_values))
            update_job(updated_job['job_number'], updated_job)
            jobs, headers = get_jobs_list(client)
            window.close()
            break

    # j = dict(zip(headers, values))

def create_invoice_window(client):
    def TextLabel(text): return sg.Text(text+':', justification='right', size=(15,1))

    layout = [
        [sg.Checkbox('As docx', key='-AS-DOCX-')],
        [TextLabel('Jobs from'), sg.Input(key='-DATE-FROM-')],
        [TextLabel('Jobs to'), sg.Input(key='-DATE-TO-', default_text=date.today().strftime("%Y-%m-%d"))],
        [sg.Button('Gen Invoice', key='-GEN-INVOICE-'), sg.Button('Exit')],
        [sg.Input(visible=False, default_text=client, key='-CLIENT-')],
    ]
    window = sg.Window('Generate Invoice', layout)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit', 'Exit0', 'Exit1'):
            window.close()
            break
        if event in ['-GEN-INVOICE-']:
            window.perform_long_operation(lambda: create_invoice(values['-CLIENT-'], values['-DATE-FROM-'], values['-DATE-TO-'], values['-AS-DOCX-']), '-END-KEY-')
            window.close()
            break



jobs, headers = get_jobs_list()


def main_window():
    clients = get_clients_list()
    column1 = sg.Column([ [sg.Frame( 'Clients:', [[sg.Column([[sg.Listbox(clients,
                                                key='-CLIENT-LIST-', size=(15, 20), enable_events=True),]], size=(150, 400))]],)], ], pad=(0,0))

    column2 = sg.Column([[sg.Frame('Jobs List:', [[sg.Column([[sg.Table(
        values=[[]],
        headings=headers,
        visible_column_map=[True,True,True, True, True, True, True, True, True, True, True, False,True],
        key='-JOB-LIST-',
        auto_size_columns=False,
        col_widths=15,
        size=(20, 20),
        max_col_width=50,
        vertical_scroll_only=False,
        enable_click_events=True,
        select_mode=sg.TABLE_SELECT_MODE_BROWSE,
    )]],)]], size=(1100, 400)  )]])

    action_column = [[sg.Button('Add Client'), sg.Button('Add Job', key='-Add-Job-', disabled=True), sg.Button('Create invoice', key='-Create-Invoice-', disabled=True), sg.Button('Settings', key='-SETTINGS-'), sg.Button('Profile', key='-PROFILE-'), sg.Button('Exit')]]

    layout = [[column1, column2], action_column]
    window=sg.Window('Main Window', layout, keep_on_top=False)
    return window

def main():

    window = main_window()
    while True:
        if window == None:
            window = main_window()
        main_event, main_values = window.read()

        if main_event in (sg.WIN_CLOSED, 'Exit'):
            break
        if main_event in ['-CLIENT-LIST-']:
            if not main_values['-CLIENT-LIST-'] or 'All' in main_values['-CLIENT-LIST-']:
                window['-Add-Job-'].update(disabled=True)
                window['-Create-Invoice-'].update(disabled=True)
                jobs, headers = get_jobs_list(main_values['-CLIENT-LIST-'][0])
                window['-JOB-LIST-'].update(values=jobs)
            else:
                client = main_values['-CLIENT-LIST-'][0]
                window['-Add-Job-'].update(disabled=False)
                window['-Create-Invoice-'].update(disabled=False)
                jobs, headers = get_jobs_list(client)
                window['-JOB-LIST-'].update(values=jobs)

        if main_event in ['-Create-Invoice-']:
            client = main_values['-CLIENT-LIST-'][0]
            create_invoice_window(client)

        if isinstance(main_event, tuple):
            if main_event[0] == '-JOB-LIST-':
                update_job_window(headers, jobs[main_event[2][0]], main_values['-CLIENT-LIST-'][0])
                window['-JOB-LIST-'].update(values=jobs)


        if main_event in ['Add Client']:
            add_client_window()
            window['-CLIENT-LIST-'].update(values=get_clients_list())

        if main_event in ['Add Job', '-Add-Job-']:
            add_job_window(main_values['-CLIENT-LIST-'][0])
            jobs, headers = get_jobs_list(main_values['-CLIENT-LIST-'][0])
            window['-JOB-LIST-'].update(values=jobs)

        if main_event in ['-SETTINGS-']:
            add_settings_window()
        if main_event in ['-PROFILE-']:
            add_profile_window()




    window.close()

main()

