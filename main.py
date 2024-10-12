import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel
import json
from datetime import datetime, timedelta
import re
import pandas as pd
# Class to represent a classroom
class Classroom:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity
        self.schedule = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}

# Class to manage schedules
class ScheduleManager:
    def __init__(self):
        self.classrooms = []
        self.groups = {}  # Track groups by their number
        self.predefined_classes = {
            1: ["Cálculo Diferencial", "Mecánica Clásica", "Ecología", "Química Universitaria"],
            2: ["Cálculo Integral", "Lab de Mediciones y Mecánica", "Ondas Calor Fluidos", "Probabilidad Estadística",
                "Álgebra Lineal"],
            3: ["Cálculo de Varias Variables", "Electricidad Magnetismo", "Laboratorio Física",
                "Circuitos Eléctricos 1", "Fundamentos de Programación", "Fundamentos Diseño Lógico"],
            4: ["Ecuaciones Diferenciales", "Campos Electromagnéticos", "Dispositivos Electrónicos",
                "Circuitos Eléctricos 2", "Métodos Numéricos"],
            5: ["Matemáticas para ICT", "Acondicionamiento de Señales Eléctricas", "Programación Orientada a Objetos",
                "Diseño Lógico Avanzado"],
            6: ["Señales Sistemas", "Administración de Organizaciones", "Comunicaciones Analógicas",
                "Algoritmos Estructuras de Datos", "Sistemas Basados en Microcontroladores"],
            7: ["Control Analógico", "Bases de Datos", "Sistemas Operativos"],
            8: ["Comunicaciones Digitales", "Óptica Física Moderna", "Fundamentos de Admin de Proyectos de SW",
                "Redes de Comunicación"],
            9: ["Procesamiento Digital de Señales", "Teoría de Información Codificación", "Física Electrónica",
                "Formulación de proyecto fundamento económico"],
            10: ["Control Digital", "Laboratorio de Control", "Factibilidad tec económica financiera"],
            11: ["Emprendimiento social"],
            12: []  # Group 12 has no classes (thesis work)
        }
        self.current_group = 1
        self.group_tracker = {}  # Track the group number for each class
        self.saved_schedule = {}  # To save the schedules
        self.class_pools = {}  # To save created classes per group
        self.current_classroom_idx = 0  # Track which classroom is being viewed

        # Define trimester colors
        self.trimester_colors = {
            1: "#FFCCCC", 2: "#FF9999", 3: "#FF6666", 4: "#FF3333", 5: "#FF0000",
            6: "#CCFFCC", 7: "#99FF99", 8: "#66FF66", 9: "#33FF33", 10: "#00FF00",
            11: "#CCCCFF", 12: "#9999FF"
        }

    def add_classroom(self, name, capacity):
        self.classrooms.append(Classroom(name, capacity))

    def get_available_classrooms(self, required_capacity):
        return [room.name for room in self.classrooms if room.capacity >= required_capacity]

    def is_time_slot_free(self, room, day, time_slot):
        return time_slot not in room.schedule[day]

    def assign_class_to_time_slot(self, room, day, time_slot, class_info):
        room.schedule[day][time_slot] = class_info

    def save_schedule(self, file_name="schedule.json"):
        data = {
            "classrooms": [
                {"name": room.name, "capacity": room.capacity, "schedule": room.schedule}
                for room in self.classrooms
            ],
            "saved_schedule": self.saved_schedule,
            "class_pools": self.class_pools
        }
        with open(file_name, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    def load_schedule(self, file_name="schedule.json"):
        with open(file_name, 'r') as infile:
            data = json.load(infile)
        self.classrooms = []
        for room_data in data["classrooms"]:
            room = Classroom(room_data["name"], room_data["capacity"])
            room.schedule = room_data["schedule"]
            self.classrooms.append(room)
        self.saved_schedule = data["saved_schedule"]
        self.class_pools = data["class_pools"]

# Class to manage the GUI and interaction
class DragDropInterface(tk.Frame):
    def __init__(self, master=None, manager=None):
        super().__init__(master)
        self.manager = manager
        self.view_mode = 'group'  # Can be 'classroom' or 'group'
        self.grid_widgets = []  # Track the grid widgets
        self.class_blocks = []  # Store created class blocks
        self.class_pool_widgets = []  # Widgets in the class pool (right sidebar)
        self.dragged_class_info = None  # Track class being dragged
        self.drag_data = {"x": 0, "y": 0}  # Track drag data
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()

    def create_widgets(self):
        # Buttons for switching views
        self.group_buttons_frame = tk.Frame(self)
        self.group_buttons_frame.pack(side=tk.TOP, padx=10, pady=10)

        # Create a button for each group
        for group_num in self.manager.predefined_classes.keys():
            tk.Button(self.group_buttons_frame, text=f"Group {group_num}",
                      command=lambda g=group_num: self.switch_to_group(g)).pack(side=tk.LEFT, padx=5)

        # Add a Load Button to load saved schedule manually
        load_button = tk.Button(self, text="Load Schedule", command=self.load_schedule)
        load_button.pack(side=tk.TOP, padx=10, pady=5)

        # Create a special frame for the backup and export buttons, placed at the bottom left corner
        backup_frame = tk.Frame(self, padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)
        backup_frame.pack(side=tk.LEFT, anchor='sw', padx=10, pady=10)

        # Add a label to the backup frame to give it a descriptive title
        tk.Label(backup_frame, text="Backup Controls", font=('Arial', 12, 'bold')).pack(pady=5)

        # Add the Save Backup button to the backup frame
        save_button = tk.Button(backup_frame, text="Save Backup", command=self.save_backup)
        save_button.pack(side=tk.TOP, padx=10, pady=5)

        # Add the Load Backup button to the backup frame
        load_backup_button = tk.Button(backup_frame, text="Load Backup", command=self.load_backup)
        load_backup_button.pack(side=tk.TOP, padx=10, pady=5)

        # Add the Export to Excel button to the backup frame
        export_button = tk.Button(backup_frame, text="Export to Excel", command=self.export_schedule_to_excel)
        export_button.pack(side=tk.TOP, padx=10, pady=5)

        # Buttons for classrooms
        self.classroom_buttons_frame = tk.Frame(self)
        self.classroom_buttons_frame.pack(side=tk.TOP, padx=10, pady=10)

        # Create a button for each classroom
        for idx, classroom in enumerate(self.manager.classrooms):
            tk.Button(self.classroom_buttons_frame, text=classroom.name,
                      command=lambda i=idx: self.switch_to_classroom(i)).pack(side=tk.LEFT, padx=5)

        # Scrollable frame for schedule grid
        self.grid_canvas = tk.Canvas(self)
        self.grid_frame = tk.Frame(self.grid_canvas)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.grid_canvas.yview)
        self.grid_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.grid_canvas.pack(side="left", fill="both", expand=True)
        self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        # Configure scrolling
        self.grid_frame.bind("<Configure>",
                             lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")))

        # Enable mouse wheel scrolling
        self.grid_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Right side: Class Pool
        self.class_pool_frame = tk.Frame(self, width=200, padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)
        self.class_pool_frame.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(self.class_pool_frame, text="Class Pool", font=('Arial', 14)).pack(pady=10)

        self.update_class_list()

        # Time slots for Monday to Friday
        self.time_slots = self.generate_time_slots()
        self.days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        self.update_schedule_grid()

    def _on_mousewheel(self, event):
        # For Windows and Linux systems
        self.grid_canvas.yview_scroll(-1 * int((event.delta / 120)), "units")

        # For macOS (which uses event.delta differently)
        # If you need macOS support, uncomment the following:
        # if event.delta < 0:
        #     self.grid_canvas.yview_scroll(1, "units")
        # else:
        #     self.grid_canvas.yview_scroll(-1, "units")

    def export_schedule_to_excel(self):
        # Export group schedules
        group_writer = pd.ExcelWriter('group_schedules.xlsx', engine='openpyxl')

        for group_key, group_schedule in self.manager.saved_schedule.items():
            if 'Group' in group_key:
                group_df = pd.DataFrame(columns=self.days_of_week, index=self.time_slots)
                for day, time_slots in group_schedule.items():
                    for time_slot, class_info in time_slots.items():
                        group_df.at[time_slot, day] = class_info
                group_df.to_excel(group_writer, sheet_name=group_key)

        group_writer.close()  # Corrected from save() to close()

        # Export room schedules
        room_writer = pd.ExcelWriter('room_schedules.xlsx', engine='openpyxl')

        for room in self.manager.classrooms:
            room_df = pd.DataFrame(columns=self.days_of_week, index=self.time_slots)
            for day, time_slots in room.schedule.items():
                for time_slot, class_info in time_slots.items():
                    room_df.at[time_slot, day] = class_info
            room_df.to_excel(room_writer, sheet_name=room.name)

        room_writer.close()  # Corrected from save() to close()

        messagebox.showinfo("Export Successful", "Schedules have been exported to Excel.")

    def load_backup(self):
        try:
            # Open the backup file and load its contents
            with open("backup.json", "r") as backup_file:
                data = json.load(backup_file)

            # Restore the classrooms, saved schedule, and class pools
            self.manager.classrooms = []
            for room_data in data["classrooms"]:
                room = Classroom(room_data["name"], room_data["capacity"])
                room.schedule = room_data["schedule"]
                self.manager.classrooms.append(room)

            # Restore the saved schedule
            self.manager.saved_schedule = data["saved_schedule"]

            # Clear and recreate the class pool from the saved schedule
            self.recreate_class_pool_from_schedule()

            # Refresh the UI to reflect the loaded data
            self.update_schedule_grid()

            messagebox.showinfo("Backup Loaded", "Your schedule and class pools have been restored from backup.json")
        except FileNotFoundError:
            messagebox.showerror("Error", "No backup file found!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading the backup: {e}")

    def save_backup(self):
        # Create a dictionary to hold all the data we want to save
        data = {
            "classrooms": [
                {"name": room.name, "capacity": room.capacity, "schedule": room.schedule}
                for room in self.manager.classrooms
            ],
            "saved_schedule": self.manager.saved_schedule,
            "class_pools": {
                group: [class_info for class_info in class_list]
                for group, class_list in self.manager.class_pools.items()
            }  # Save all dynamically created class info
        }

        # Save this data to a JSON file called backup.json
        with open("backup.json", "w") as backup_file:
            json.dump(data, backup_file, indent=4)

        # Notify the user that the backup was successful
        messagebox.showinfo("Backup", "Your schedule and class pools have been successfully saved to backup.json")

    def recreate_class_pool_from_schedule(self):
        # Clear the current class pool
        for widget in self.class_pool_widgets:
            widget.destroy()
        self.class_pool_widgets.clear()

        recreated_classes = set()  # To avoid duplicating the same classes

        # Iterate over the saved schedule and extract class details
        for group_key, group_schedule in self.manager.saved_schedule.items():
            for day, time_slots in group_schedule.items():
                for time_slot, class_info in time_slots.items():
                    # Extract class details from the saved schedule
                    match = re.search(r'(\d+)T: (.+?) \(Group (\d+), ([A-Za-z0-9]+), (\d+) students\)', class_info)

                    if match:
                        trimester = match.group(1)
                        class_name = match.group(2)
                        group_num = match.group(3)
                        room_name = match.group(4)
                        num_students = match.group(5)

                        # Create a unique identifier to avoid duplicates
                        class_id = f"{class_name} (Group {group_num}, {room_name}, {num_students} students)"

                        # Avoid duplicating the class
                        if class_id not in recreated_classes:
                            # Recreate the class block using this extracted information
                            self.create_class_block_in_pool(class_id, is_dynamic=True)
                            recreated_classes.add(class_id)

        # Refresh the class pool for predefined classes
        self.update_class_list()

    def is_time_slot_free(self, room, day, time_slot):
        # Debugging: Print current room schedule before checking
        print(f"Checking time slot for {room.name} on {day} at {time_slot}. Room schedule: {room.schedule[day]}")

        # Check if the time slot is free in the room's internal schedule
        if day in room.schedule and time_slot in room.schedule[day]:
            print(f"Time slot {time_slot} on {day} is occupied in {room.name}'s internal schedule")
            return False  # The slot is occupied in the room

        # Check the saved schedule for both groups and classrooms
        for group_key, group_schedule in self.saved_schedule.items():
            if day in group_schedule and time_slot in group_schedule[day]:
                class_info = group_schedule[day][time_slot]
                if room.name in class_info:  # If the class info contains the room's name
                    print(f"Time slot {time_slot} on {day} is occupied by {class_info} in the saved_schedule")
                    return False  # The slot is occupied in the saved schedule

        print(f"Time slot {time_slot} on {day} is free in {room.name}")
        return True  # The slot is free

    def update_schedule_grid(self):
        # Clear existing grid widgets
        for widget in self.grid_widgets:
            widget.destroy()
        self.grid_widgets = []

        # Create the header row with day names
        for idx, day in enumerate(self.days_of_week):
            day_label = tk.Label(self.grid_frame, text=day, relief="ridge", padx=10, pady=5, font=("Arial", 10))
            day_label.grid(row=2, column=idx + 1)
            self.grid_widgets.append(day_label)

        # Create time slots in the first column
        for row_idx, time_slot in enumerate(self.time_slots):
            time_label = tk.Label(self.grid_frame, text=time_slot, relief="ridge", padx=10, pady=5, font=("Arial", 8))
            time_label.grid(row=row_idx + 3, column=0)
            self.grid_widgets.append(time_label)

            # Populate the grid with schedule data
            for col_idx, day in enumerate(self.days_of_week):
                slot_label = tk.Label(self.grid_frame, text="", relief="sunken", width=30, height=6, font=("Arial", 8))
                slot_label.grid(row=row_idx + 3, column=col_idx + 1)

                # Determine whether we're in group or classroom view
                if self.view_mode == 'group':
                    # Get the group's saved schedule
                    saved_schedule = self.manager.saved_schedule.get(f'Group {self.manager.current_group}', {})
                else:
                    # Get the classroom's saved schedule
                    current_classroom = self.manager.classrooms[self.manager.current_classroom_idx]
                    saved_schedule = self.manager.saved_schedule.get(current_classroom.name, {})

                # If there is a class assigned to this time slot, set it
                if day in saved_schedule and time_slot in saved_schedule[day]:
                    class_info = saved_schedule[day][time_slot]
                    slot_label.config(text=class_info, bg="lightgray", wraplength=150, justify="center",
                                      font=("Arial", 8))

                # Bind the time slot to handle drag-and-drop
                slot_label.bind("<ButtonRelease-1>",
                                lambda e, t=time_slot, d=day, slot_label=slot_label: self.drop_in_time_slot(t, d,
                                                                                                            slot_label))
                self.grid_widgets.append(slot_label)

    def switch_to_group(self, group_num):
        self.manager.current_group = group_num
        self.update_group_label()
        self.load_current_state()

    def switch_to_classroom(self, idx):
        # Set the current classroom index
        self.manager.current_classroom_idx = idx

        # Clear the grid to prepare for displaying the classroom's schedule
        self.clear_schedule()

        # Load the current classroom's state and schedule
        self.load_classroom_state()

        # Update the label to reflect the current classroom
        self.group_label.config(
            text=f"{self.manager.classrooms[idx].name} (Capacity: {self.manager.classrooms[idx].capacity})")

    def save_schedule(self):
        data = {
            "classrooms": [
                {"name": room.name, "capacity": room.capacity, "schedule": room.schedule}
                for room in self.classrooms
            ],
            "saved_schedule": self.saved_schedule,  # Make sure the saved schedule is stored
            "class_pools": self.class_pools  # Ensure class pools are saved
        }
        with open("schedule.json", 'w') as outfile:
            json.dump(data, outfile, indent=4)

    def load_schedule(self):
        self.manager.load_schedule()
        self.update_schedule_grid()

    def update_group_label(self):
        # Update the label for the current group
        self.group_label = tk.Label(self.grid_frame, text=f"Group {self.manager.current_group}", font=('Arial', 14))
        self.group_label.grid(row=0, column=0, columnspan=3, padx=5, pady=5)

    def load_current_state(self):
        # Load the current group's schedule and class pool
        if self.manager.current_group in self.manager.saved_schedule:
            self.set_schedule(self.manager.saved_schedule[self.manager.current_group])  # Load the group schedule
        else:
            self.clear_schedule()  # If no saved schedule exists, clear the grid

        # Refresh the class pool for the current group
        self.update_class_list()

    def save_current_state(self):
        # Save the current group's schedule
        self.manager.saved_schedule[self.manager.current_group] = self.get_current_schedule()

        # Save the class pool for the current group
        class_pool = [block.cget("text") for block in self.class_pool_widgets]
        self.manager.class_pools[self.manager.current_group] = class_pool

    def load_classroom_state(self):
        # Get the current classroom based on the selected index
        current_classroom = self.manager.classrooms[self.manager.current_classroom_idx]
        classroom_name = current_classroom.name

        # Clear the grid first
        self.clear_schedule()

        # We'll gather the schedule for this classroom from the group schedules
        classroom_schedule = {}

        # Iterate through all groups to find classes scheduled in this classroom
        for group_key, group_schedule in self.manager.saved_schedule.items():
            for day, time_slots in group_schedule.items():
                for time_slot, class_info in time_slots.items():
                    # Check if the class is assigned to the current classroom
                    if classroom_name in class_info:  # e.g., "Room A" in the class_info
                        if day not in classroom_schedule:
                            classroom_schedule[day] = {}
                        classroom_schedule[day][time_slot] = class_info

        # Check if any schedule was found for the classroom
        if classroom_schedule:
            print(f"Loading schedule for {classroom_name}: {classroom_schedule}")
            self.set_schedule(classroom_schedule)
        else:
            # If no saved schedule exists for this classroom, notify the user
            messagebox.showinfo("No Saved Schedule", f"No saved schedule for {classroom_name}")

    def set_schedule(self, schedule_data):
        # Set the current schedule from saved data (for groups or classrooms)
        for day, slots in schedule_data.items():
            for time_slot, class_info in slots.items():
                # Make sure the time slot and day exist in the grid
                if time_slot in self.time_slots and day in self.days_of_week:
                    row_idx = self.time_slots.index(time_slot)
                    col_idx = self.days_of_week.index(day)
                    slot_label = self.grid_frame.grid_slaves(row=row_idx + 3, column=col_idx + 1)
                    if slot_label:
                        # Apply the saved schedule data to the grid
                        slot_label[0].config(text=class_info, bg="lightgray", wraplength=150, justify="center",
                                             font=("Arial", 8))

    def clear_schedule(self):
        # Clear the schedule from the grid, but not from saved data
        for row_idx in range(len(self.time_slots)):
            for col_idx in range(len(self.days_of_week)):
                slot_label = self.grid_frame.grid_slaves(row=row_idx + 3, column=col_idx + 1)
                if slot_label:
                    slot_label[0].config(text="", bg="white")

    def update_class_list(self):
        # Clear existing class pool widgets
        for widget in self.class_pool_widgets:
            widget.destroy()
        self.class_pool_widgets.clear()

        recreated_classes = set()  # Track classes we already added to avoid duplication

        # Load dynamically created classes from the saved pool for this group
        if self.manager.current_group in self.manager.class_pools:
            for class_info in self.manager.class_pools[self.manager.current_group]:
                if class_info not in recreated_classes:
                    self.create_class_block_in_pool(class_info, is_dynamic=True)
                    recreated_classes.add(class_info)

        # Predefined classes for this group (ensure these are always shown once)
        for class_name in self.manager.predefined_classes.get(self.manager.current_group, []):
            if class_name not in recreated_classes:
                self.create_class_block_in_pool(class_name)  # Predefined classes are not draggable
                recreated_classes.add(class_name)

    def create_class_block_in_pool(self, class_info, is_dynamic=False):
        # Create the class block label
        class_block = tk.Label(self.class_pool_frame, text=class_info, relief="raised", padx=10, pady=5, bg="lightblue")
        class_block.pack(pady=5)

        # If it's a dynamically created class, make it draggable
        if is_dynamic:
            class_block.bind("<Button-1>", self.start_drag_block)
        else:
            # Predefined classes will trigger the class creation process
            class_block.bind("<Button-1>", self.start_class_creation)

        # Track the block in the class pool
        self.class_pool_widgets.append(class_block)

    def start_class_creation(self, event):
        class_name = event.widget.cget("text")
        students = simpledialog.askinteger("Number of Students", "Enter the number of students:")
        if not students or students <= 0:
            messagebox.showerror("Invalid Input", "Please enter a valid number of students.")
            return

        available_classrooms = self.manager.get_available_classrooms(students)
        if not available_classrooms:
            messagebox.showerror("No Classrooms", f"No classrooms available for {students} students.")
            return

        top = Toplevel(self)
        top.title("Select Classroom")
        tk.Label(top, text="Choose a classroom").pack(pady=10)

        variable = tk.StringVar(top)
        variable.set(available_classrooms[0])

        tk.OptionMenu(top, variable, *available_classrooms).pack(pady=10)

        def on_select():
            classroom = variable.get()

            # Determine the next group number for this class
            group_num = self.manager.group_tracker.get(class_name, 1)  # Start at group 1 if not tracked yet
            self.manager.group_tracker[class_name] = group_num + 1  # Increment group number for future instances

            trimester = self.manager.current_group  # Track current trimester
            class_name_with_trimester = f"{trimester}T: {class_name}"

            self.manager.groups[group_num] = {
                "class": class_name_with_trimester,
                "students": students,
                "classroom": classroom
            }

            # Increment the group counter for this class
            self.create_class_block(class_name_with_trimester, students, group_num, classroom)
            top.destroy()

        tk.Button(top, text="OK", command=on_select).pack(pady=10)

    def create_class_block(self, class_name_with_trimester, students, group_num, classroom):
        # Display the class with the correct group number and classroom details
        class_info = f"{class_name_with_trimester} (Group {group_num}, {classroom}, {students} students)"

        # Create the class block for the dynamically created class
        class_block = tk.Label(self.class_pool_frame, text=class_info, relief="raised", padx=10, pady=5, bg="lightblue")
        class_block.pack(pady=5)

        # Make the class block draggable
        class_block.bind("<Button-1>", self.start_drag_block)

        # Add the class block to the pool widget list
        self.class_pool_widgets.append(class_block)

        # Store this class in the manager's class pool for the current group
        if self.manager.current_group not in self.manager.class_pools:
            self.manager.class_pools[self.manager.current_group] = []
        self.manager.class_pools[self.manager.current_group].append(class_info)

    def start_drag_block(self, event):
        widget = event.widget
        self.dragged_class_info = widget.cget("text")
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

        widget.bind("<B1-Motion>", self.on_drag_motion)
        widget.bind("<ButtonRelease-1>", self.on_drop)

    def on_drag_motion(self, event):
        widget = event.widget
        x = widget.winfo_x() - self.drag_data["x"] + event.x
        y = widget.winfo_y() - self.drag_data["y"] + event.y
        widget.place(x=x, y=y)

    def on_drop(self, event):
        widget = event.widget
        widget.unbind("<B1-Motion>")
        widget.unbind("<ButtonRelease-1>")

    def generate_time_slots(self):
        start_time = datetime.strptime("08:00 AM", "%I:%M %p")
        end_time = datetime.strptime("04:30 PM", "%I:%M %p")
        time_slots = []
        current_time = start_time
        while current_time <= end_time:
            time_slots.append(current_time.strftime("%I:%M %p"))
            current_time += timedelta(minutes=30)
        return time_slots

    def drop_in_time_slot(self, time_slot, day, slot_label):
        if self.dragged_class_info:
            match = re.search(r'Group (\d+), ([A-Za-z0-9]+)', self.dragged_class_info)


            if match:
                group_num = int(match.group(1))
                room_name = match.group(2)

                if self.view_mode == 'group':
                    # Update the group schedule
                    selected_classroom = next((room for room in self.manager.classrooms if room.name == room_name),
                                              None)
                    if selected_classroom:
                        if not self.manager.is_time_slot_free(selected_classroom, day, time_slot):
                            messagebox.showerror("Time Slot Occupied",
                                                 f"The time slot at {time_slot} on {day} is already booked.")
                        else:
                            self.manager.assign_class_to_time_slot(selected_classroom, day, time_slot,
                                                                   self.dragged_class_info)
                            self.save_class_to_schedule(self.dragged_class_info, day, time_slot)
                            slot_label.config(text=self.dragged_class_info, bg="lightgray", wraplength=150,
                                              justify="center", font=("Arial", 8))

                elif self.view_mode == 'classroom':
                    # Update the classroom schedule
                    selected_classroom = self.manager.classrooms[self.current_classroom_idx]
                    if not self.manager.is_time_slot_free(selected_classroom, day, time_slot):
                        messagebox.showerror("Time Slot Occupied",
                                             f"The time slot at {time_slot} on {day} is already booked.")
                    else:
                        self.manager.assign_class_to_time_slot(selected_classroom, day, time_slot,
                                                               self.dragged_class_info)
                        self.save_class_to_schedule(self.dragged_class_info, day, time_slot)
                        slot_label.config(text=self.dragged_class_info, bg="lightgray", wraplength=150,
                                          justify="center", font=("Arial", 8))

            self.dragged_class_info = None  # Reset drag state

    def save_class_to_schedule(self, class_info, day, time_slot):
        if self.view_mode == 'group':
            # Use "Group X" format for group keys
            group_key = f"Group {self.manager.current_group}"

            # Save group schedule
            group_schedule = self.manager.saved_schedule.setdefault(group_key, {})
            group_schedule[day] = group_schedule.get(day, {})
            group_schedule[day][time_slot] = class_info
        elif self.view_mode == 'classroom':
            # Save classroom schedule using the classroom name as the key
            current_classroom = self.manager.classrooms[self.manager.current_classroom_idx]
            classroom_key = current_classroom.name

            classroom_schedule = self.manager.saved_schedule.setdefault(classroom_key, {})
            classroom_schedule[day] = classroom_schedule.get(day, {})
            classroom_schedule[day][time_slot] = class_info

        # Debugging: Print saved schedule after adding class
        print(f"Saved schedule after adding class: {self.manager.saved_schedule}")

    def get_current_schedule(self):
        current_schedule = {}
        for col_idx, day in enumerate(self.days_of_week):
            current_schedule[day] = {}
            for row_idx, time_slot in enumerate(self.time_slots):
                slot_label = self.grid_frame.grid_slaves(row=row_idx + 3, column=col_idx + 1)
                if slot_label and slot_label[0].cget("text"):
                    current_schedule[day][time_slot] = slot_label[0].cget("text")
        return current_schedule

    def confirm_delete_class(self, time_slot, day):
        # Get the current schedule based on view mode
        if self.view_mode == 'group':
            group_key = f'Group {self.manager.current_group}'
            saved_schedule = self.manager.saved_schedule.get(group_key, {})
        else:
            current_classroom = self.manager.classrooms[self.manager.current_classroom_idx]
            saved_schedule = self.manager.saved_schedule.get(current_classroom.name, {})

        # Debugging: Print saved schedule and room schedule before deletion
        print(f"Before deletion - Saved Schedule: {self.manager.saved_schedule}")
        print(f"Before deletion - Room Schedule: {[room.schedule for room in self.manager.classrooms]}")

        # Check if a class is scheduled at this time
        if day in saved_schedule and time_slot in saved_schedule[day]:
            class_info = saved_schedule[day][time_slot]

            # Ask for confirmation to delete
            confirm = messagebox.askyesno("Delete Class", f"Do you want to delete this class?\n\n{class_info}")
            if confirm:
                # Delete the class from the saved schedule
                del saved_schedule[day][time_slot]
                if not saved_schedule[day]:  # If no more classes for the day, remove the day entry
                    del saved_schedule[day]

                # Now, ensure the class is also deleted from the internal room schedule
                # Match the room name within parentheses, e.g., "(Group 1, P310, 25 students)"
                class_info_match = re.search(r'\(Group \d+, ([A-Za-z0-9]+), \d+ students\)', class_info)

                if class_info_match:
                    room_name = class_info_match.group(1)

                    # Debugging: Print room name being matched
                    print(f"Attempting to match room: {room_name}")

                    # Find the correct room by name
                    room = next((r for r in self.manager.classrooms if r.name == room_name), None)

                    if room:
                        print(f"Matched room: {room.name}")
                        if day in room.schedule and time_slot in room.schedule[day]:
                            print(f"Deleting from room.schedule: {room.schedule[day][time_slot]}")
                            # Explicitly delete the entry from the room's internal schedule
                            del room.schedule[day][time_slot]  # Clear the internal room schedule
                        else:
                            print(f"Error: Time slot {time_slot} not found in room {room.name} for {day}")
                    else:
                        print(f"Error: Room {room_name} not found")
                else:
                    print("Error: Could not extract room from class info")

                # Debugging: Print saved schedule and room schedule after deletion
                print(f"After deletion - Saved Schedule: {self.manager.saved_schedule}")
                print(f"After deletion - Room Schedule: {[room.schedule for room in self.manager.classrooms]}")

                # Update the schedule grid to reflect the deletion
                self.update_schedule_grid()

                # Save the updated schedule to the JSON file
                self.manager.save_schedule()

                # Notify user of successful deletion
                messagebox.showinfo("Deleted", "The class has been deleted.")

    def update_schedule_grid(self):
        # Clear existing grid widgets
        for widget in self.grid_widgets:
            widget.destroy()
        self.grid_widgets = []

        # Create the header row with day names
        for idx, day in enumerate(self.days_of_week):
            day_label = tk.Label(self.grid_frame, text=day, relief="ridge", padx=10, pady=5, font=("Arial", 10))
            day_label.grid(row=2, column=idx + 1)
            self.grid_widgets.append(day_label)

        # Create time slots in the first column
        for row_idx, time_slot in enumerate(self.time_slots):
            time_label = tk.Label(self.grid_frame, text=time_slot, relief="ridge", padx=10, pady=5, font=("Arial", 8))
            time_label.grid(row=row_idx + 3, column=0)
            self.grid_widgets.append(time_label)

            # Add saved schedule data to the grid
            for col_idx, day in enumerate(self.days_of_week):
                slot_label = tk.Label(self.grid_frame, text="", relief="sunken", width=30, height=6, font=("Arial", 8))
                slot_label.grid(row=row_idx + 3, column=col_idx + 1)

                # Get saved schedule for this time slot and day
                saved_schedule = self.manager.saved_schedule.get(f'Group {self.manager.current_group}', {})
                if day in saved_schedule and time_slot in saved_schedule[day]:
                    class_info = saved_schedule[day][time_slot]
                    slot_label.config(text=class_info, bg="lightgray", wraplength=150, justify="center",
                                      font=("Arial", 8))

                # Bind the time slot to handle drop event and deletion prompt
                slot_label.bind("<ButtonRelease-1>",
                                lambda e, t=time_slot, d=day, slot_label=slot_label: self.drop_in_time_slot(t, d,
                                                                                                            slot_label))
                # Bind a left-click event to handle deletion
                slot_label.bind("<Button-1>", lambda e, t=time_slot, d=day: self.confirm_delete_class(t, d))

                self.grid_widgets.append(slot_label)

    def save_classroom_state(self, classroom):
        # Save the current classroom's schedule
        self.manager.saved_schedule[classroom.name] = self.get_current_schedule()
    def toggle_view(self):
        # Save the current state before toggling views
        if self.view_mode == 'group':
            self.save_current_state()  # Save current group's schedule
        elif self.view_mode == 'classroom':
            current_classroom = self.manager.classrooms[self.manager.current_classroom_idx]
            self.save_classroom_state(current_classroom)  # Save the current classroom's schedule

        # Toggle between Classroom and Group views
        if self.view_mode == 'classroom':
            self.view_mode = 'group'
            self.load_current_state()  # Load the group schedule and class pool
        else:
            self.view_mode = 'classroom'
            self.load_classroom_state()  # Load the classroom schedule

        # Refresh the schedule grid and class pool after toggling views
        self.update_schedule_grid()  # Update the grid with the loaded schedule
        self.update_class_list()  # Reload the class pool

    def drop_in_time_slot(self, time_slot, day, slot_label):
        if self.dragged_class_info:
            match = re.search(r'Group (\d+), ([A-Za-z0-9]+)', self.dragged_class_info)

            if match:
                group_num = int(match.group(1))
                room_name = match.group(2)

                if self.view_mode == 'group':
                    # Update the group schedule
                    selected_classroom = next((room for room in self.manager.classrooms if room.name == room_name),
                                              None)
                    if selected_classroom:
                        # Check if time slot is free
                        if not self.manager.is_time_slot_free(selected_classroom, day, time_slot):
                            messagebox.showerror("Time Slot Occupied",
                                                 f"The time slot at {time_slot} on {day} is already booked.")
                        else:
                            # Assign the class and save the schedule
                            self.manager.assign_class_to_time_slot(selected_classroom, day, time_slot,
                                                                   self.dragged_class_info)
                            self.save_class_to_schedule(self.dragged_class_info, day, time_slot)
                            slot_label.config(text=self.dragged_class_info, bg="lightgray", wraplength=150,
                                              justify="center", font=("Arial", 8))

                elif self.view_mode == 'classroom':
                    # Update the classroom schedule
                    selected_classroom = self.manager.classrooms[self.manager.current_classroom_idx]
                    if not self.manager.is_time_slot_free(selected_classroom, day, time_slot):
                        messagebox.showerror("Time Slot Occupied",
                                             f"The time slot at {time_slot} on {day} is already booked.")
                    else:
                        # Assign the class and save the schedule
                        self.manager.assign_class_to_time_slot(selected_classroom, day, time_slot,
                                                               self.dragged_class_info)
                        self.save_class_to_schedule(self.dragged_class_info, day, time_slot)
                        slot_label.config(text=self.dragged_class_info, bg="lightgray", wraplength=150,
                                          justify="center", font=("Arial", 8))

            self.dragged_class_info = None  # Reset drag state

    def load_schedule(self):
        # Convert current_group to the correct key format ("Group X")
        group_key = f"Group {self.manager.current_group}"

        # Debugging step: Print the saved schedule
        print(f"Saved schedule: {self.manager.saved_schedule}")

        if self.view_mode == 'group':
            if group_key in self.manager.saved_schedule:  # Check using the correct key format
                print(f"Loading schedule for {group_key}")
                self.set_schedule(self.manager.saved_schedule[group_key])
            else:
                messagebox.showinfo("No Saved Schedule", f"No saved schedule for {group_key}")
        else:
            # For classrooms, use the classroom name as the key
            current_classroom = self.manager.classrooms[self.manager.current_classroom_idx]
            classroom_key = current_classroom.name

            # Check if the saved schedule for the classroom exists
            if classroom_key in self.manager.saved_schedule:
                print(f"Loading schedule for {classroom_key}")
                self.set_schedule(self.manager.saved_schedule[classroom_key])
            else:
                messagebox.showinfo("No Saved Schedule", f"No saved schedule for {classroom_key}")


# ======= Main Application =======
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Interactive Scheduler")
    root.geometry("1400x800")
    # Initialize the schedule manager
    manager = ScheduleManager()

    # Add some example classrooms
    manager.add_classroom("P310", 25)
    manager.add_classroom("B3", 50)

    # Start the Tkinter interface
    app = DragDropInterface(master=root, manager=manager)
    app.switch_to_group(1)
    app.mainloop()
