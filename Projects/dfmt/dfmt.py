import json
import uuid
import math
import subprocess
import tkinter as tk
import shutil
from tkinter import messagebox, filedialog, ttk
from inc.conversions import steps, img_to_xml, hash_query, hashdb_create
from inc.sql_loader import load, hash_lister
import os
import inc.extract_bloom as bloom
import inc.B as B
import inc.A2 as A2
import re
from inc.exceptions import HashException
from time import strftime, localtime, time
from datetime import datetime

config_file = open("config.json")
config = json.loads(config_file.read())
md5deep64 = config["filePaths"]["md5deep64"]
hashdb = config["filePaths"]["hashDB"]


patterns = {
    "hash_store": re.compile(r"hash store: (\d+)"),
    "sources": re.compile(b'"filename":"(.+)",')
}

def close_application(master):
    def wrapper():
        config_file.close()
        master.destroy()

        raise SystemExit

    return wrapper


def db_info(master):
    def wrapper(file_path=None):
        window = tk.Toplevel(master)

        database = file_path or filedialog.askdirectory()

        try:
            output_1 = str(subprocess.check_output([hashdb, "size", database]))
            output_2 = subprocess.check_output([hashdb, "sources", database])

        except subprocess.CalledProcessError:
            messagebox.showerror("dfmt", "This isn't a valid hashdb folder!")
            return

        hash_store = patterns["hash_store"].search(output_1).group(1)
        sources = patterns["sources"].findall(output_2)

        sources = map(lambda x: str(x, "utf-8"), sources)
        sources = "\n\t".join(sources)

        tk.Label(window, text=f"Number of hashes: {hash_store}").grid(row=0, column=0, sticky="w", padx=20)
        tk.Label(window, text=f"Sources: {sources}").grid(row=1, column=0, sticky="w", padx=20)

        return hash_store, sources

    return wrapper



class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(StartPage)

    def switch_frame(self, frame):
        try:
            new_frame = frame(self)
            new_frame.resizable = (False, False)

            if self._frame is not None:
                self._frame.destroy()

            self._frame = new_frame
            self._frame.pack()
        except HashException as e:
            messagebox.showerror("dfmt", e)


class StartPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        master.title("dfmt")
        master.resizable = (False, False)

        # menu bar
        menu_bar = tk.Menu(master)

        #submenu = tk.Menu(menu_bar)
        #submenu.add_command(label="Sources")
        #submenu.add_command(label="test 2")
        #submenu.add_command(label="test 3")


        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Load Media", command=lambda: master.switch_frame(LoadMediaPage))
        file_menu.add_command(label="Query Media", command=lambda: master.switch_frame(QueryMediaPage))
        file_menu.add_separator()
        #file_menu.add_command(
        #	label="Bloom Insert", command=lambda: master.switch_frame(BloomInsert))
        file_menu.add_command(label="Bloom Export", command=lambda: master.switch_frame(BloomExport))
        file_menu.add_command(label="Bloom Import", command=lambda: master.switch_frame(BloomImport))

        file_menu.add_separator()
        file_menu.add_command(label="Triage", command=lambda: master.switch_frame(Triage))
        #file_menu.add_command(
        #	label="Bloom Export", command=lambda: master.switch_frame(BloomExport))

        file_menu.add_separator()

        file_menu.add_command(label="DB Info", command=db_info(master))

        file_menu.add_separator()

        file_menu.add_command(label="Help", command=lambda: master.switch_frame(HelpMenu))

        file_menu.add_command(label="Exit", command=close_application(master))

        menu_bar.add_cascade(label="Main", menu=file_menu)

        master.config(menu=menu_bar)

        master.minsize(350, 200)

class Triage(tk.Frame):
    def __init__(self, master):
        self.default_db = config.get("defaults", {}).get("databaseName", "").strip(".hdb")

        if not self.default_db:
            raise HashException("Must supply a default database name in config.json")

        self.master = master

        tk.Frame.__init__(self, master)

        self._browse_data = {}

        self.media_file_selected = tk.Label(self, text="No file selected")
        self.file_selected = tk.Label(self, text="No file selected")

        self.media_file_selected.grid(row=0, column=1, sticky="w")
        self.file_selected.grid(row=1, column=1, sticky="w")

        tk.Button(self, text="Browse for Media", command=self.browse_file("media")).grid(row=0, column=0, sticky="w")
        tk.Button(self, text="Browse for File", command=self.browse_file("file")).grid(row=1, column=0, sticky="w")

        tk.Button(self, text="Cancel", command=self.cancel).grid(row=3, column=1, pady=10, sticky="w")
        tk.Button(self, text="Submit", command=self.submit).grid(row=3, column=1, padx=55, sticky="w")

        self.include_compute1 = tk.IntVar()
        self.include_compute3 = tk.IntVar()

        self.hiding = True

        self.default_compute_method = config.get("defaults", {}).get("queryMediaComputationMethod", "compute3")

        self.show_advanced_options_btn = tk.Button(self, text="Show advanced options", command=self.show_advanced_options)
        self.show_advanced_options_btn.grid(row=2, column=0, sticky="w")

        self.c1 = None
        self.c2 = None
        self.loaded_already = False


    def browse_file(self, type):
        def browse():
            file_path = filedialog.askopenfilename(parent=self.master, title="Choose a File")
            skip_confirm = config.get("skipConfirmationDialog", False)

            if file_path:
                with open(file_path, "rb") as f:
                    file_name = os.path.basename(f.name)

                    if not skip_confirm:
                        file_size = os.stat(file_path).st_size

                        res = messagebox.askokcancel("dfmt","Would you like to load the file:\n"
                                                            f"File Name: {file_name}\n"
                                                            f"File Path: {file_path}\n"
                                                            f"File Size: {file_size} bytes\n")

                        if not res:
                            return

                    self._browse_data[type] = {
                        "file_path": file_path,
                        "file_name": file_name
                    }

                    file_path = len(file_path) > 20 and f"...{file_path[len(file_path)-20:]}" or file_path

                    if type == "media":
                        self.media_file_selected.config(text=file_path)
                    else:
                        self.file_selected.config(text=file_path)

        return browse


    def cancel(self):
        self.master.switch_frame(StartPage)

    def submit(self):
        if not self._browse_data:
            messagebox.showerror("Invalid Usage", "Please make sure all fields are filled.")
            return

        time_start = time()

        try:
            steps(self.default_db, self._browse_data["media"]["file_path"])
            load(f"{self.default_db}.db")
            messagebox.showinfo("dfmt", "Done.")
        except HashException as e:
            messagebox.showerror("Error", e)


        file_path = self._browse_data["file"]["file_path"]
        #file_path_xml = img_to_xml(file_path_media)
        #db_name = self.db_name.get()

        total, file_path_xml = hash_query(self.default_db, file_path)

        nonce = str(uuid.uuid4())

        show_results_options = {}

        #with open(json_name, "a+") as f:
        json_data = {}
        json_data[nonce] = {}
        using_options = {}

        if self.loaded_already:
            using_options["compute1"] = self.include_compute1.get()
            using_options["compute3"] = self.include_compute3.get()
        else:
            using_options[self.default_compute_method] = True

        if using_options.get("compute1"):
            c1_time = strftime("%m/%d/%Y: %H:%M:%S", localtime())
            score1, count1 = A2.compute1(file_path_xml, total)
            json_data[nonce]["compute1"] = {"queried_file": file_path , "count": count1, "score": score1, "total sectors in media": total, "timestamp": c1_time}
            show_results_options["c1"] = {"score": score1, "count": count1, "total sectors in media": total, "timestamp": c1_time}

        if using_options.get("compute3"):
            c3_time = strftime("%m/%d/%Y: %H:%M:%S", localtime())
            harmonic_means, count3, c2 = A2.compute3(file_path_xml, total)
            json_data[nonce]["compute3"] = {"queried_file": file_path, "count": count3, "harmonic_means": harmonic_means, "total sectors in media": total, "compute2": c2, "timestamp": c3_time}
            show_results_options["c3"] = {"harmonic_means": harmonic_means, "count": count3, "total sectors in media": total, "compute2": c2, "timestamp": c3_time}

        # if json_data[nonce]:
        # 	f_1 = filedialog.asksaveasfile(mode="a", defaultextension=".json")
        # 	json_data = json.dumps(json_data)

        # 	if f_1:
        # 		f_1.write(json_data)
        # 		f_1.close()
        if json_data[nonce]:
            file_name = datetime.today().strftime("results_%Y%M%d_%H%M%S_HQ_scores")
            json_name = f"{file_name}.json"

            with open(json_name, "a+") as f:
                f.write("\n" + json.dumps(json_data))
                messagebox.showinfo("dfmt", "Done.")
                f.close()

        else:
            messagebox.showerror("dfmt", f"Error: nothing to add to file.")

        if show_results_options:
            self.show_results(**show_results_options)

        del_args = "del scan.txt; del /Q/S comp1.db; del /Q/S comp2.db; del /Q/S comp3.db"
        subprocess.call(del_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        new_file_name = datetime.today().strftime("results_%Y%M%d_%H%M%S_HQ_detail")
        os.rename("scan_edited.txt", new_file_name+".json")
        os.remove("database/test3.db")
        shutil.rmtree('database/test3')

        print(f"Triage time taken: {time() - time_start} seconds.")

    def show_advanced_options(self):
        self.hiding = not self.hiding

        if self.hiding:
            if self.c1 and self.c2:
                self.c1.destroy()
                self.c2.destroy()

                self.c1 = None
                self.c2 = None

            self.show_advanced_options_btn.config(text="Show advanced options")
        else:
            self.c1 = tk.Checkbutton(
                self, text="Include frequency weighted matches?", variable=self.include_compute1)
            self.c1.grid(row=3, column=0, sticky="w")

            self.c2 = tk.Checkbutton(self, text="Include frequency per source weighted\nmatches with sequencing factor?", variable=self.include_compute3, justify="left")
            self.c2.grid(row=4, column=0, sticky="w")

            self.show_advanced_options_btn.config(text="Hide advanced options")

            if not self.loaded_already:
                if self.default_compute_method == "compute1":
                    self.c1.select()
                elif self.default_compute_method == "compute3":
                    self.c2.select()
                else:
                    raise HashException("Invalid computation method in config file. Value must be 'compute1' or 'compute3'.")

        self.loaded_already = True

    def show_results(self, **kwargs):
        # show_results_options["c1"] = {"score": score1, "matched": count1, "total": total, "timestamp": c1_time}
        # show_results_options["c3"] = {"harmonic_means": harmonic_means, "matched": count3, "total": total, "compute2": c2, "timestamp": c3_time}

        if kwargs:
            row = 0

            for c, options in kwargs.items():
                window = tk.Toplevel(self.master)
                tk.Label(window, text=f"Results with {c == 'c1' and 'frequency weighted matches' or 'frequency per source weighted matches with sequencing factor'}").grid(row=row, column=0, sticky="w", padx=20)

                if c == "c1":
                    tk.Label(window, text=f"Score: {math.floor(options['score']*100)}").grid(row=row+1, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Matched sectors: {options['timestamp']}").grid(row=row+2, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Total sectors in media: {options['total sectors in media']}").grid(row=row+3, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Timestamp: {options['timestamp']}").grid(row=row+4, column=0, sticky="w", padx=20)
                    row += 4

                elif c == "c3":
                    if options["harmonic_means"] == "none":
                        tk.Label(window, text="There were no matches.").grid(row=row+1, column=0, sticky="w", padx=20)

                        return

                    sorted_hm = sorted(options["harmonic_means"].values(), key=lambda x: x[1], reverse=True)

                    for source_data in sorted_hm:
                        image = source_data[0]
                        image = len(image) > 20 and f"...{image[len(image)-20:]}" or image
                        tk.Label(window, text=f"Image: {image}").grid(row=row+1, column=0, sticky="w", padx=20)
                        tk.Label(window, text=f"Score: {source_data[1]:.3f}").grid(row=row+2, column=0, sticky="w", padx=20)
                        # ttk.Separator(window).grid(row=row+3, rowspan=row+3, column=0, sticky="ew", padx=20)
                        row += 3

                    tk.Label(window, text=f"Total sectors in media: {options['total sectors in media']}").grid(row=row+1, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Matched sectors: {options['count']}").grid(row=row+2, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Timestamp: {options['timestamp']}").grid(row=row+3, column=0, sticky="w", padx=20)
                    row += 3

class LoadMediaPage(tk.Frame):
    def __init__(self, master):
        self.master = master

        tk.Frame.__init__(self, master)

        self._browse_data = {}
        self.creating_db = tk.IntVar()
        self.media_file_selected = tk.Label(self, text="No file selected")
        self.create_db_box = tk.Checkbutton(self, text="Create new DB", variable=self.creating_db, command=self.create_db_show)
        #self.db_file_selected = tk.Label(self, text="No file selected")
        self.db_name = self.db_file_selected = self.db_name_label = self.browse_db_button = None

        self.media_file_selected.grid(row=0, column=1, sticky="w")
        self.create_db_box.grid(row=1, column=0, sticky="w")
        #self.db_file_selected.grid(row=2, column=1, sticky="w")

        #tk.Label(self, text="Database Name: ").grid(row=1, column=0, sticky="w")
        #self.db_name = tk.Entry(self, background="white", width=24)
        #self.db_name.grid(row=1, column=1, sticky="w")


        #tk.Button(self, text="Browse for Database File", command=self.browse_file("db")).grid(row=2, column=0, sticky="w")
        tk.Button(self, text="Browse for Media", command=self.browse_file("media")).grid(row=0, column=0, sticky="w")
        #tk.Button(self, text="Save new Hash Database", command=self.save_db_file).grid(row=1, column=0, sticky="w")

        tk.Button(self, text="Cancel", command=self.cancel).grid(row=3, column=1, pady=10, sticky="w")
        tk.Button(self, text="Submit", command=self.submit).grid(row=3, column=1, padx=55, sticky="w")

        self.create_db_show()


    def create_db_show(self):
        if self.db_name_label:
            self.db_name_label.destroy()
        if self.db_name:
            self.db_name.destroy()
        if self.db_file_selected:
            self.db_file_selected.destroy()
        if self.browse_db_button:
            self.browse_db_button.destroy()

        # self._browse_data = {}

        if self.creating_db.get():
            # creating new db
            self.db_name_label = tk.Label(self, text="Database Name: ")
            self.db_name_label.grid(row=2, column=0, sticky="w")
            self.db_name = tk.Entry(self, background="white", width=24)
            self.db_name.grid(row=2, column=1, sticky="w")
        else:
            self.db_file_selected = tk.Label(self, text="No file selected")
            self.db_file_selected.grid(row=2, column=1, sticky="w")
            self.browse_db_button = tk.Button(self, text="Browse for Database File", command=self.browse_file("db"))
            self.browse_db_button.grid(row=2, column=0, sticky="w")



    def browse_file(self, type):
        def browse():
            file_path = filedialog.askopenfilename(parent=self.master, title="Choose a File")
            skip_confirm = config.get("skipConfirmationDialog", False)

            if file_path:
                with open(file_path, "rb") as f:
                    file_name = os.path.basename(f.name)

                    if not skip_confirm:
                        file_size = os.stat(file_path).st_size

                        res = messagebox.askokcancel("dfmt","Would you like to load the file:\n"
                                                            f"File Name: {file_name}\n"
                                                            f"File Path: {file_path}\n"
                                                            f"File Size: {file_size} bytes\n")

                        if not res:
                            return

                    self._browse_data[type] = {
                        "file_path": file_path,
                        "file_name": file_name
                    }

                    file_path = len(file_path) > 20 and f"...{file_path[len(file_path)-20:]}" or file_path

                    if type == "media":
                        self.media_file_selected.config(text=file_path)
                    else:
                        self.db_file_selected.config(text=file_path)

        return browse


    def cancel(self):
        self.master.switch_frame(StartPage)

    def submit(self):
        if self.creating_db.get():
            db_name = self.db_name.get().strip(".hdb")
            hashdb_path = f".\\database\\{db_name}"

            if not (self._browse_data and db_name):
                messagebox.showerror("Invalid Usage", "Please make sure all fields are filled.")
                return

            media_path = self._browse_data["media"]["file_path"]

        else:
            db_name = self._browse_data.get("db", {}).get("file_name", "").strip(".hdb")
            hashdb_path = f".\\database\\{db_name}"

            if not (self._browse_data and db_name):
                messagebox.showerror("Invalid Usage", "Please make sure all fields are filled.")
                return

            media_path = self._browse_data["media"]["file_path"]
            media_path_hashdb_comp = media_path.replace("/", "\\")

            output_sources = subprocess.check_output([hashdb, "sources", hashdb_path])

            sources = patterns["sources"].findall(output_sources)

            sources = map(lambda x: str(x, "utf-8"), sources)
            sources = "\n\t".join(sources)

            if media_path_hashdb_comp in sources:
                res = messagebox.askokcancel("dfmt","Caution! This image appears to be already loaded. Load it anyway?")

                if not res:
                    return

        #if not os.path.exists(hashdb_path):
        #    print(f"creating hashdb: {db_name}", flush=True)
        #    hashdb_create(db_name)

        time_start = time()

        try:
            #steps(self._db_file_path, self._browse_data["file_path"])
            #load(self._db_file_path)
            steps(db_name, media_path)
            load(f"{db_name}.db")
            messagebox.showinfo("dfmt", "Done.")
        except HashException as e:
            messagebox.showerror("Error", e)
        else:
            print(f"Load Media time taken: {time() - time_start} seconds.")


class QueryMediaPage(tk.Frame):
    def __init__(self, master):
        self.master = master

        tk.Frame.__init__(self, master)

        self._browse_data = {}
        self.expanded = False

        self.file_selected = tk.Label(self, text="No file selected")
        self.file_selected.grid(row=0, column=1, sticky="w", padx=20)

        self.file_db_selected = tk.Label(self, text="No file selected")
        self.file_db_selected.grid(row=1, column=1, sticky="w", padx=20)

        tk.Button(self, text="Browse for File", command=self.browse_file("file")).grid(row=0, column=0, sticky="w")


        tk.Button(self, text="Browse for Database File", command=self.browse_file("db")).grid(row=1, column=0, sticky="w")



        #tk.Label(self, text="Database Name: ").grid(row=1, column=0, sticky="w")
        #self.db_name = tk.Entry(self, background="white", width=24)
        #self.db_name.grid(row=1, column=1, sticky="w")


        self.include_compute1 = tk.IntVar()
        self.include_compute3 = tk.IntVar()

        self.hiding = True

        self.default_compute_method = config.get("defaults", {}).get("queryMediaComputationMethod", "compute3")

        self.show_advanced_options_btn = tk.Button(self, text="Show advanced options", command=self.show_advanced_options)
        self.show_advanced_options_btn.grid(row=2, column=0, sticky="w")

        self.c1 = None
        self.c2 = None
        self.loaded_already = False

        """
        c1 = tk.Checkbutton(
            self, text="Include frequency weighted matches?",
                  variable=self.include_compute1)
        c1.grid(row=2, column=0, sticky="w")

        c2 = tk.Checkbutton(
            self, text="Include frequency per source weighted\nmatches with sequencing factor?",
                  variable=self.include_compute3, justify="left")
        c2.grid(row=3, column=0, sticky="w")
        """

        self.cancel_button = tk.Button(self, text="Cancel", command=self.cancel)

        self.cancel_button.grid(row=7, column=0, padx=20, sticky="w")

        self.submit_button = tk.Button(self, text="Submit", command=self.submit)

        self.submit_button.grid(row=7, column=0, padx=85, sticky="w")

    def show_advanced_options(self):
        self.hiding = not self.hiding

        if self.hiding:
            if self.c1 and self.c2:
                self.c1.destroy()
                self.c2.destroy()

                self.c1 = None
                self.c2 = None

            self.show_advanced_options_btn.config(text="Show advanced options")
        else:
            self.c1 = tk.Checkbutton(
                self, text="Include frequency weighted matches?", variable=self.include_compute1)
            self.c1.grid(row=3, column=0, sticky="w")

            self.c2 = tk.Checkbutton(self, text="Include frequency per source weighted\nmatches with sequencing factor?", variable=self.include_compute3, justify="left")
            self.c2.grid(row=4, column=0, sticky="w")

            self.show_advanced_options_btn.config(text="Hide advanced options")

            if not self.loaded_already:
                if self.default_compute_method == "compute1":
                    self.c1.select()
                elif self.default_compute_method == "compute3":
                    self.c2.select()
                else:
                    raise HashException("Invalid computation method in config file. Value must be 'compute1' or 'compute3'.")

        self.loaded_already = True



    def cancel(self):
        self.master.switch_frame(StartPage)

    def submit(self):
        if not self._browse_data.get("file"):
            messagebox.showerror("Invalid Usage", "Please make sure you select your media.")
            return

        time_start = time()

        file_path_media = self._browse_data["file"]["file_path"]
        file_path_db = self._browse_data["db"]["file_path"]
        file_name = os.path.basename(file_path_media)
        #file_path_xml = img_to_xml(file_path_media)
        #db_name = self.db_name.get()
        db_name = self._browse_data["db"]["file_name"].strip(".hdb")
        new_file_name = datetime.today().strftime("results_%Y%M%d_%H%M%S_HQ_detail")

        total, file_path_xml = hash_query(db_name, file_path_media)

        nonce = str(uuid.uuid4())

        show_results_options = {}

        #with open(json_name, "a+") as f:
        json_data = {}
        json_data[nonce] = {}
        using_options = {}

        if self.loaded_already:
            using_options["compute1"] = self.include_compute1.get()
            using_options["compute3"] = self.include_compute3.get()
        else:
            using_options[self.default_compute_method] = True


        if using_options.get("compute1"):
            c1_time = strftime("%m/%d/%Y: %H:%M:%S", localtime())
            score1, count1 = A2.compute1(file_path_xml, total)
            json_data[nonce][file_path_media] = {
                "compute1": {"file_path_db": file_path_db, "file_name": file_name, "db_name": db_name, "count": count1, "score": score1, "total sectors in media": total, "timestamp": c1_time}
            }
            #json_data[nonce][file_path_media]["compute1"] =  {"file_path_db": file_path_db, "file_name": file_name, "db_name": db_name, "count": count1, "score": score1, "total sectors in media": total, "timestamp": c1_time}
            #json_data[nonce]["compute1"] = {"file_path": file_path_media, "file_path_db": file_path_db, "file_name": file_name, "db_name": db_name, "count": count1, "score": score1, "total sectors in media": total, "timestamp": c1_time}
            show_results_options["c1"] = {"score": score1, "count": count1, "total sectors in media": total, "timestamp": c1_time}

        if using_options.get("compute3"):
            c3_time = strftime("%m/%d/%Y: %H:%M:%S", localtime())
            harmonic_means, count3, c2 = A2.compute3(file_path_xml, total)
            json_data[nonce][file_path_media] = {
                "compute3": {"file_path_db": file_path_db, "file_name": file_name, "db_name": db_name, "count": count3, "harmonic_means": harmonic_means, "total sectors in media": total, "compute2": c2, "timestamp": c3_time}
            }
            #json_data[nonce]["compute3"] = {"file_path": file_path_media, "file_path_db": file_path_db, "file_name": file_name, "db_name": db_name, "count": count3, "harmonic_means": harmonic_means, "total sectors in media": total, "compute2": c2, "timestamp": c3_time}
            show_results_options["c3"] = {"harmonic_means": harmonic_means, "count": count3, "total sectors in media": total, "compute2": c2, "timestamp": c3_time}

        if json_data[nonce]:
            # f_1 = filedialog.asksaveasfile(mode="a", defaultextension=".json")
            folder_selected = filedialog.askdirectory()
            with open(f"{folder_selected}/{new_file_name}.txt", "a+") as f:
                f.write(json.dumps(json_data))
                f.close()


            """
            file_name = strftime("results_%Y%m%d_%H%M%S_HQ", localtime())
            json_name = f"{file_name}.json"

            with open(json_name, "a+") as f:
                f.write("\n" + json.dumps(json_data))
                messagebox.showinfo("dfmt", "Done.")
                f.close()
            """

        else:
            messagebox.showerror("dfmt", "Error: nothing to add to file.")

        if show_results_options:
            self.show_results(**show_results_options)

        del_args = "del scan.txt; del /Q/S comp1.db; del /Q/S comp2.db; del /Q/S comp3.db"
        subprocess.call(del_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        os.rename("scan_edited.txt", f"{folder_selected}/{new_file_name}.json")
        print(f"Query media time taken: {time()-time_start} seconds.")


    def browse_file(self, type):
        def browse():
            file_path = filedialog.askopenfilename(parent=self.master, title="Choose a File")
            skip_confirm = config.get("skipConfirmationDialog", False)

            if file_path:
                with open(file_path, "rb") as f:
                    file_name = os.path.basename(f.name)

                    if not skip_confirm:
                        file_size = os.stat(file_path).st_size

                        res = messagebox.askokcancel("dfmt","Would you like to load the file:\n"
                                                            f"File Name: {file_name}\n"
                                                            f"File Path: {file_path}\n"
                                                            f"File Size: {file_size} bytes\n")

                        if not res:
                            return
                    self._browse_data[type] = {
                        "file_path": file_path,
                        "file_name": file_name
                    }

                    file_path = len(file_path) > 20 and f"...{file_path[len(file_path)-20:]}" or file_path

                    if type == "file":
                        self.file_selected.config(text=file_path)
                    else:
                        self.file_db_selected.config(text=file_path)

        return browse

    def show_results(self, **kwargs):
        window = tk.Toplevel(self.master)

        if kwargs:
            tk.Label(window, text=f"File path: {self._browse_data['file']['file_path']}").grid(row=1, column=0, sticky="w", padx=20)
            tk.Label(window, text=f"File name: {self._browse_data['file']['file_name']}").grid(row=2, column=0, sticky="w", padx=20)

            tk.Label(window, text=f"DB path: {self._browse_data['db']['file_path']}").grid(row=3, column=0, sticky="w", padx=20)
            tk.Label(window, text=f"DB name: {self._browse_data['db']['file_name']}").grid(row=4, column=0, sticky="w", padx=20)

            row = 5

            for c, options in kwargs.items():

                tk.Label(window, text=f"Results with {c == 'c1' and 'frequency weighted matches' or 'frequency per source weighted matches with sequencing factor'}").grid(row=row, column=0, sticky="w", padx=20)

                row += 1

                if c == "c1":
                    tk.Label(window, text=f"Score: {math.floor(options['score']*100)}").grid(row=row+1, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Matched sectors: {options['timestamp']}").grid(row=row+2, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Total sectors in media: {options['total sectors in media']}").grid(row=row+3, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Timestamp: {options['timestamp']}").grid(row=row+4, column=0, sticky="w", padx=20)
                    row += 4

                elif c == "c3":
                    if options["harmonic_means"] == "none":
                        tk.Label(window, text="There were no matches.").grid(row=row+1, column=0, sticky="w", padx=20)

                        return

                    sorted_hm = sorted(options["harmonic_means"].values(), key=lambda x: x[1], reverse=True)

                    for source_data in sorted_hm:
                        image = source_data[0]
                        image = len(image) > 20 and f"...{image[len(image)-20:]}" or image
                        tk.Label(window, text=f"Image: {image}").grid(row=row+1, column=0, sticky="w", padx=20)
                        tk.Label(window, text=f"Score: {source_data[1]:.3f}").grid(row=row+2, column=0, sticky="w", padx=20)
                        # ttk.Separator(window).grid(row=row+3, rowspan=row+3, column=0, sticky="ew", padx=20)
                        row += 3

                    tk.Label(window, text=f"Total sectors in media: {options['total sectors in media']}").grid(row=row+1, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Matched sectors: {options['count']}").grid(row=row+2, column=0, sticky="w", padx=20)
                    tk.Label(window, text=f"Timestamp: {options['timestamp']}").grid(row=row+3, column=0, sticky="w", padx=20)
                    row += 3


class BloomExport(tk.Frame):
    def __init__(self, master):
        self.master = master

        tk.Frame.__init__(self, master)

        self._browse_data = {}
        self.file_db_selected = tk.Label(self, text="No file selected")
        self.file_db_selected.grid(row=0, column=1, sticky="w", padx=20)

        tk.Button(
            self, text="Browse for SQLite Database", command=self.browse_file).grid(
                  row=0, column=0, sticky="w")

        tk.Button(self, text="Submit", command=self.submit).grid(row=2, column=0, padx=55, sticky="w")

    def browse_file(self):
        file_path = filedialog.askopenfilename(parent=self.master, title="Choose a File")
        skip_confirm = config.get("skipConfirmationDialog", False)

        if file_path:
            with open(file_path, "rb") as f:
                file_name = os.path.basename(f.name)

                if not skip_confirm:
                    file_size = os.stat(file_path).st_size

                    res = messagebox.askokcancel("dfmt","Would you like to load the file:\n"
                                                        f"File Name: {file_name}\n"
                                                        f"File Path: {file_path}\n"
                                                        f"File Size: {file_size} bytes\n")

                    if not res:
                        return

                self._browse_data = {
                    "file_path": file_path,
                    #"data": data
                }

                file_path = len(file_path) > 20 and f"...{file_path[len(file_path)-20:]}" or file_path

                self.file_db_selected.config(text=file_path)

    def submit(self):
        if not (self._browse_data):
            messagebox.showerror("Invalid Usage", "Please make sure you select an SQLite Database file.")
            return

        time_start = time()

        hash_list = hash_lister(self._browse_data["file_path"])

        if bloom.size() < len(hash_list):
            bloom.new_blooms(len(hash_list))

        for entry in hash_list:
            bloom.insert(entry[0].strip(""), entry[1])

        bloom_data = bloom.extract()

        file_name = strftime("triage_filter_%Y%m%d_%H%M%S_HQ", localtime())
        txt_name = file_name + ".txt"
        md5_name = file_name + ".md5"

        with open(txt_name, "w+") as f:
            f.write(json.dumps(bloom_data))

        subprocess.call(f"{md5deep64} {txt_name} > {md5_name}", shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        print(f"Bloom Export time taken: {time() - time_start} seconds.")

        messagebox.showinfo("dfmt", "Done.")


class BloomImport(tk.Frame):
    def __init__(self, master):
        self.master = master

        tk.Frame.__init__(self, master)

        #self.blooms = []
        self._browse_data = {
            "media": {},
            "bloom_file": {}
        }

        #self.new_bloom_button = None
        #self.submit_button = None
        self.media_file_selected = None
        #self.browse_button = None

        #source = tk.Entry(self, background="white", width=24)
        #source.grid(row=0, column=1, sticky="w")

        #self.new_bloom()

        self.bloom_file_selected = tk.Label(self, text="No file selected")
        self.bloom_file_selected.grid(row=0, column=0, sticky="w")

        tk.Button(self, text="Browse for Bloom File", command=self.browse_file("bloom")).grid(row=0, column=1, sticky="w")

        self.media_file_selected = tk.Label(self, text="No file selected")
        self.media_file_selected.grid(row=1, column=0, sticky="w")

        tk.Button(self, text="Browse for Media", command=self.browse_file("media")).grid(row=1, column=1, sticky="w")

        self.submit_button = tk.Button(self, text="Submit", command=self.submit)
        self.submit_button.grid(row=2, column=1, padx=55, sticky="w")

    def browse_file(self, type):
        def browse():
            file_path = filedialog.askopenfilename(parent=self.master, title="Choose a File")
            skip_confirm = config.get("skipConfirmationDialog", False)

            if file_path:
                with open(file_path, "rb") as f:
                    file_name = os.path.basename(f.name)

                    if not skip_confirm:
                        file_size = os.stat(file_path).st_size

                        res = messagebox.askokcancel("dfmt","Would you like to load the file:\n"
                                                            f"File Name: {file_name}\n"
                                                            f"File Path: {file_path}\n"
                                                            f"File Size: {file_size} bytes\n")

                        if not res:
                            return

                    if type == "bloom":
                        self._browse_data["bloom_file"] = {
                            "file_path": file_path,
                            #"data": data
                        }
                        self.bloom_file_selected.config(text=file_path)
                    else:
                        self._browse_data["media"] = {
                            "file_path": file_path,
                            #"data": data
                        }

                        self.media_file_selected.config(text=file_path)

        return browse

    def submit(self):
        if not (self._browse_data["media"] and self._browse_data["bloom_file"]):
            messagebox.showerror("Error", "You must select the files.")
            return

        time_start = time()

        #image_path = img_to_xml(self._browse_data["media"]["file_path"])
        bloom_path = self._browse_data["bloom_file"]["file_path"]
        #size, _ = db_info(self.master)(self._browse_data["media"])
        #print(size, flush=True)
        matched, total, empty, score = B.compute(bloom_path)

        nonce = str(uuid.uuid4())

        print(f"Bloom Import time taken: {time() - time_start} seconds.")

        with open("results-bloom.json", "a+") as f:
            json_data = {}

            json_data[nonce] = {}

            json_data[nonce] = {"matched": matched, "total": total, "empty": empty, "score": score, "queried_file": self._browse_data["media"]["file_path"]}

            if json_data[nonce]:
                f.write( '\n' + json.dumps(json_data))
                messagebox.showinfo("dfmt", "Done. See results-bloom.json.")
            else:
                messagebox.showerror("dfmt", "Error: nothing to add to results-bloom.json")

        self.master.switch_frame(StartPage)


class HelpMenu(tk.Frame):
    def __init__(self, master):
        self.master = master

        tk.Frame.__init__(self, master)

        self._browse_data = {}

        tk.Label(self, text="""
DFMT: Digital Fragment Matching Tool

Given one or more intact or partial files of interest, the DFMT tool finds matching fragments in disk images and computes a likelihood that the entire input file was previously present on the disk image or images being examined.
The typical use case for this tool is to identify post-deletion residual fragments of digital files on digital media. For full application documentation and tutorials, see the /Docs folder in the tool distribution.

Basic Usage:

Load a media image or images:
Main -> Load Media -> Browse for Media -> [select media file]
Database Name -> [type a name or browse for an existing database file]
Submit
OK
Repeat as needed for additional media images

Query a group of media images for a full or partial file:
Main -> Query Media -> Browse for File -> [select query file]
Submit
Select output folder location
Save
Results will be presented in a pop-up window and saved in the folder location specified

Field Usage:

Export a compressed version of the database:
Main -> Bloom Export -> Browse for SQLite Database -> [select database file] and [OK]
Submit
OK
Copy the Bloom File and transport as needed
Main -> Bloom Import -> Browse for Bloom File -> [select bloom filter file] and [OK]
Browse for File -> [select query file]
OK
Submit
OK
Results will be in the file results.json in the main application folder
        """).grid(row=0, column=0, sticky="w", padx=20)

        tk.Button(self, text="Cancel", command=self.master.switch_frame(StartPage)).grid(row=1, column=0, padx=30, pady=20)






if __name__ == "__main__":
    try:
        Application().mainloop()
    except HashException as e:
        messagebox.showerror("dfmt", e)

    print("Closing application.", flush=True)
