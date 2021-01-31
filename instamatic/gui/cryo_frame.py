import threading
import time
from pathlib import Path
from datetime import datetime
from tkinter import filedialog
from tkinter import *
from tkinter.ttk import *
from tqdm import tqdm

import numpy as np
import pandas as pd

from instamatic import config
from instamatic import TEMController
from instamatic.utils import suppress_stderr
from instamatic.gui.grid_frame import GridFrame
from instamatic.utils.widgets import MultiListbox, Hoverbox

class CryoED(LabelFrame):
    """GUI panel for Cryo electron diffraction data collection protocol."""

    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text='Cryo electron diffraction protocol')
        self.parent = parent
        self.crystal_list = None
        self.df_grid = pd.DataFrame(columns=['grid', 'pos_x', 'pos_y'])
        self.df_square = pd.DataFrame(columns=['grid', 'square', 'pos_x', 'pos_y', 'pos_z'])
        self.df_target = pd.DataFrame(columns=['grid', 'square', 'target', 'pos_x', 'pos_y', 'pos_z'])
        self.grid_dir = None
        self.last_grid = None
        self.last_square = None
        self.ctrl = TEMController.get_instance()

        self.init_vars()

        frame = Frame(self)

        self.e_level = OptionMenu(frame, self.var_level, 'Whole', 'Whole', 'Square', 'Target')
        self.e_level.config(width=7)
        self.e_level.grid(row=0, column=0, sticky='EW')
        Label(frame, text='Area(um):', anchor="center").grid(row=0, column=1, sticky='EW')
        self.e_radius = Spinbox(frame, textvariable=self.var_radius, width=8, from_=0.0, to=500.0, increment=1)
        self.e_radius.grid(row=0, column=2, sticky='EW', padx=5)
        Label(frame, text='Exp Name:', anchor="center").grid(row=0, column=3, sticky='EW')
        self.e_name = Entry(frame, textvariable=self.var_name, width=8)
        self.e_name.grid(row=0, column=4, sticky='EW', padx=5)

        self.CollectMapButton = Button(frame, text='Collect Map', width=11, command=self.collect_map, state=NORMAL)
        self.CollectMapButton.grid(row=1, column=0, sticky='EW')
        self.OpenMapButton = Button(frame, text='Get Pos', width=11, command=self.get_pos, state=NORMAL)
        self.OpenMapButton.grid(row=1, column=1, sticky='EW', padx=5)
        self.SaveGridButton = Button(frame, text='Change Grid', width=11, command=self.change_grid, state=NORMAL)
        self.SaveGridButton.grid(row=1, column=2, sticky='EW')
        self.SaveGridButton = Button(frame, text='Save Grid', width=11, command=self.save_grid, state=NORMAL)
        self.SaveGridButton.grid(row=1, column=3, sticky='EW', padx=5)
        self.LoadGridButton = Button(frame, text='Load Grid', width=11, command=self.load_grid, state=NORMAL)
        self.LoadGridButton.grid(row=1, column=4, sticky='EW')

        self.lb_coll1 = Label(frame, text='')
        self.lb_coll1.grid(row=2, column=0, columnspan=5, sticky='EW', pady=5)
        

        self.AddTargetButton = Button(frame, text='Add Target', width=11, command=self.add_target, state=NORMAL)
        self.AddTargetButton.grid(row=3, column=0, sticky='EW')
        self.DelTargetButton = Button(frame, text='Del Target', width=11, command=self.del_target, state=NORMAL)
        self.DelTargetButton.grid(row=3, column=1, sticky='EW', padx=5)
        self.DelSquareButton = Button(frame, text='Del Square', width=11, command=self.del_square, state=NORMAL)
        self.DelSquareButton.grid(row=3, column=2, sticky='EW')
        self.DelGridButton = Button(frame, text='Del Grid', width=11, command=self.del_grid, state=NORMAL)
        self.DelGridButton.grid(row=3, column=3, sticky='EW', padx=5)
        

        self.UpdateZButton = Button(frame, text='Z Square', width=11, command=self.update_z_square, state=NORMAL)
        self.UpdateZButton.grid(row=4, column=0, sticky='EW')
        self.UpdateZButton = Button(frame, text='Z Target', width=11, command=self.update_z_target, state=NORMAL)
        self.UpdateZButton.grid(row=4, column=1, sticky='EW', padx=5)
        self.GoXYButton = Button(frame, text='Go to XY', width=11, command=self.go_xy, state=NORMAL)
        self.GoXYButton.grid(row=4, column=2, sticky='EW')
        self.GoXYZButton = Button(frame, text='Go to XYZ', width=11, command=self.go_xyz, state=NORMAL)
        self.GoXYZButton.grid(row=4, column=3, sticky='EW', padx=5)

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        frame = Frame(self)

        Label(frame, width=16, text='Whole Grid Level', anchor="center").grid(row=0, column=0, sticky='EW')
        Label(frame, width=24, text='Grid Square Level', anchor="center").grid(row=0, column=2, sticky='EW')
        Label(frame, width=24, text='Individual target Level', anchor="center").grid(row=0, column=4, sticky='EW')

        self.tv_whole_grid = Treeview(frame, height=12, selectmode='browse')
        self.tv_whole_grid["columns"] = ("1", "2")
        self.tv_whole_grid['show'] = 'headings'
        self.tv_whole_grid.column("1", width=12, anchor='c')
        self.tv_whole_grid.column("2", width=12, anchor='c')
        self.tv_whole_grid.heading("1", text="Pos_x")
        self.tv_whole_grid.heading("2", text="Pos_y")
        self.tv_whole_grid.grid(row=1, column=0, sticky='EW')
        self.tv_whole_grid.bind("<Double-1>", self.update_grid)
        self.tv_whole_grid.bind("<Button-2>", self.update_grid)
        self.tv_whole_grid.bind("<Button-3>", self.update_grid)
        self.scroll_tv_grid = ttk.Scrollbar(frame, orient="vertical", command=self.tv_whole_grid.yview)
        self.scroll_tv_grid.grid(row=1, column=1, sticky='NS')
        self.tv_whole_grid.configure(yscrollcommand=self.scroll_tv_grid.set)

        self.tv_grid_square = Treeview(frame, height=12, selectmode='browse')
        self.tv_grid_square["columns"] = ("1", "2", "3")
        self.tv_grid_square['show'] = 'headings'
        self.tv_grid_square.column("1", width=12, anchor='c')
        self.tv_grid_square.column("2", width=12, anchor='c')
        self.tv_grid_square.column("3", width=12, anchor='c')
        self.tv_grid_square.heading("1", text="Pos_x")
        self.tv_grid_square.heading("2", text="Pos_y")
        self.tv_grid_square.heading("3", text="Pos_z")
        self.tv_grid_square.grid(row=1, column=2, sticky='EW')
        self.tv_grid_square.bind("<Double-1>", self.update_square)
        self.tv_grid_square.bind("<Button-2>", self.update_square)
        self.tv_grid_square.bind("<Button-3>", self.update_square)
        self.scroll_tv_square = ttk.Scrollbar(frame, orient="vertical", command=self.tv_grid_square.yview)
        self.scroll_tv_square.grid(row=1, column=3, sticky='NS')
        self.tv_grid_square.configure(yscrollcommand=self.scroll_tv_square.set)

        self.tv_target = Treeview(frame, height=12, selectmode='browse')
        self.tv_target["columns"] = ("1", "2", "3")
        self.tv_target['show'] = 'headings'
        self.tv_target.column("1", width=12, anchor='c')
        self.tv_target.column("2", width=12, anchor='c')
        self.tv_target.column("3", width=12, anchor='c')
        self.tv_target.heading("1", text="Pos_x")
        self.tv_target.heading("2", text="Pos_y")
        self.tv_target.heading("3", text="Pos_z")
        self.tv_target.grid(row=1, column=4, sticky='EW')
        self.scroll_tv_target = ttk.Scrollbar(frame, orient="vertical", command=self.tv_target.yview)
        self.scroll_tv_target.grid(row=1, column=5, sticky='NS')
        self.tv_target.configure(yscrollcommand=self.scroll_tv_target.set)
        
        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

    def init_vars(self):
        self.var_radius = IntVar(value=200)
        self.var_name = StringVar(value="")
        self.var_level = StringVar(value='Whole')

    @suppress_stderr
    def show_progress(self, n):
        tot = 50
        interval = tot / n
        with tqdm(total=100, ncols=60, bar_format='{l_bar}{bar}') as pbar:
            for i in range(n):
                self.lb_coll1.config(text=str(pbar))
                time.sleep(interval)
                pbar.update(100/n)
            self.lb_coll1.config(text=str(pbar))

    def collect_map(self):
        if self.grid_dir is None:
            num = 1
            self.grid_dir = config.locations['work'] / f'Grid_{num}'
            success = False
            while not success:
                try:
                    self.grid_dir.mkdir(parents=True)
                    success = True
                except OSError:
                    num += 1
                    self.grid_dir = config.locations['work'] / f'Grid_{num}'

        level = self.e_level.get()
        if level == 'Whole':
            if self.ctrl.tem.interface == "fei":
                self.ctrl.magnification.index = 5
            elif:
                pass
        elif level == 'Square':
            if self.ctrl.tem.interface == "fei":
                pass
            elif:
                pass
        elif level == 'Target':
            if self.ctrl.tem.interface == "fei":
                pass
            elif:
                pass

    def get_pos(self):
        self.position_list = GridFrame(self).get_selected_positions()
        level = self.var_level.get()

        if len(self.position_list) != 0:
            if level == 'Whole':
                last_num_grid = len(self.df_grid)
                self.df_grid = self.df_grid.append(self.position_list, ignore_index=True)
                for index in range(len(self.position_list)):
                    self.tv_whole_grid.insert("",'end', text="Item_"+str(last_num_grid+index), 
                                        values=(self.position_list.loc[index,'pos_x'],self.position_list.loc[index,'pos_y']))
                    self.df_grid.loc[last_num_grid+index, 'grid'] = last_num_grid + index
                print(self.df_grid)
            elif level == 'Square':
                if self.df_grid is None:
                    raise RuntimeError('Please collect whole grid map first!')
                else:
                    try:
                        grid_num = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
                    except IndexError: 
                        raise RuntimeError('Please select a grid position before get positions in square level')

                    last_num_square = len(self.df_square)
                    existing_num_square = len(self.df_square[self.df_square['grid'] == grid_num])
                    self.df_square = self.df_square.append(self.position_list, ignore_index=True)
                    for index in range(len(self.position_list)):
                        self.tv_grid_square.insert("",'end', text="Item_"+str(last_num_square+index), 
                                        values=(self.position_list.loc[index,'pos_x'],self.position_list.loc[index,'pos_y'],0))
                        self.df_square.loc[last_num_square+index, 'grid'] = grid_num
                        self.df_square.loc[last_num_square+index, 'square'] = existing_num_square + index
                        self.df_square.loc[last_num_square+index, 'pos_z'] = 0
                    print(self.df_square)

            elif level == 'Target':
                if self.df_square is None:
                    raise RuntimeError('Please collect grid square map first!')
                else:
                    try:
                        grid_num = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
                        square_num = self.tv_grid_square.get_children().index(self.tv_grid_square.selection()[0])
                    except IndexError:
                        raise RuntimeError('Please select a grid and square before get positions in target level')

                    last_num_target = len(self.df_target)
                    existing_num_targets = len(self.df_target[(self.df_target['grid'] == grid_num) & (self.df_target['square'] == square_num)])
                    self.df_target = self.df_target.append(self.position_list, ignore_index=True)
                    for index in range(len(self.position_list)):
                        self.tv_target.insert("",'end', text="Item_"+str(last_num_target+index), 
                                        values=(self.position_list.loc[index,'pos_x'],self.position_list.loc[index,'pos_y'],0))
                        self.df_target.loc[last_num_target+index, 'grid'] = grid_num
                        self.df_target.loc[last_num_target+index, 'square'] = square_num
                        self.df_target.loc[last_num_target+index, 'target'] = existing_num_targets+index
                        self.df_target.loc[last_num_target+index, 'pos_z'] = 0
                    print(self.df_target)

    def change_grid(self):
        self.df_grid = pd.DataFrame(columns=['grid', 'pos_x', 'pos_y'])
        self.df_square = pd.DataFrame(columns=['grid', 'square', 'pos_x', 'pos_y', 'pos_z'])
        self.df_target = pd.DataFrame(columns=['grid', 'square', 'target', 'pos_x', 'pos_y', 'pos_z'])
        self.tv_whole_grid.delete(*self.tv_whole_grid.get_children())
        self.tv_grid_square.delete(*self.tv_grid_square.get_children())
        self.tv_target.delete(*self.tv_target.get_children())

    def update_grid(self, event):
        selected = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
        if self.last_grid != selected:
            self.last_grid = selected
            self.tv_grid_square.delete(*self.tv_grid_square.get_children())
            self.tv_target.delete(*self.tv_target.get_children())
            selected_square_df = self.df_square[self.df_square['grid'] == selected].reset_index().drop(['index'], axis=1)
            for index in range(len(selected_square_df)):
                self.tv_grid_square.insert("",'end', text="Item_"+str(index), 
                                        values=(selected_square_df.loc[index,'pos_x'],selected_square_df.loc[index,'pos_y'],0))

    def update_square(self, event):
        selected_grid = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
        selected_square = self.tv_grid_square.get_children().index(self.tv_grid_square.selection()[0])
        if self.last_square != selected_square or self.last_grid != selected_grid:
            self.last_square = selected_square
            self.last_grid = selected_grid
            self.tv_target.delete(*self.tv_target.get_children())
            selected_target_df = self.df_target[(self.df_target['grid']==selected_grid) & (self.df_target['square']==selected_square)].reset_index().drop(['index'], axis=1)
            for index in range(len(selected_target_df)):
                self.tv_target.insert("",'end', text="Item_"+str(index), 
                                        values=(selected_target_df.loc[index,'pos_x'],selected_target_df.loc[index,'pos_y'],0))

    def update_z_square(self):
        pass

    def update_z_target(self):
        pass

    def go_xy(self):
        pass

    def go_xyz(self):
        pass

    def add_target(self):
        try:
            selected_grid = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
            selected_square = self.tv_grid_square.get_children().index(self.tv_grid_square.selection()[0])
        except IndexError:
            raise RuntimeError('Please select grid and square level.')

    def del_target(self):
        try:
            selected_grid = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
            selected_square = self.tv_grid_square.get_children().index(self.tv_grid_square.selection()[0])
            selected_target = self.tv_target.get_children().index(self.tv_target.selection()[0])
            existing_targets = self.tv_target.get_children()
        except IndexError:
            raise RuntimeError('Please select grid, square and target level.')

        self.tv_target.delete(existing_targets[selected_target])
        self.df_target = self.df_target[(self.df_target['grid']!=selected_grid) | 
                                        (self.df_target['square']!=selected_square) |
                                         self.df_target['target']!=selected_target].reset_index().drop(['index'], axis=1)
        num = 0
        for index, _ in self.df_target[(self.df_target['grid']==selected_grid) & (self.df_target['square']==selected_square)].iterrows():
            self.df_target.loc[index, 'target'] = num
            num += 1
        print(self.df_target)

    def del_square(self):
        try:
            selected_grid = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
            selected_square = self.tv_grid_square.get_children().index(self.tv_grid_square.selection()[0])
            existing_square = self.tv_grid_square.get_children()
        except IndexError:
            raise RuntimeError('Please select grid and square level.')

        self.tv_target.delete(*self.tv_target.get_children())
        self.tv_grid_square.delete(existing_square[selected_square])
        self.df_square_org_index = self.df_square[(self.df_square['grid']==selected_grid) & (self.df_square['square']!=selected_square)]
        self.df_square = self.df_square[(self.df_square['grid']!=selected_grid) | (self.df_square['square']!=selected_square)].reset_index().drop(['index'], axis=1)
        self.df_target = self.df_target[(self.df_target['grid']!=selected_grid) | (self.df_target['square']!=selected_square)].reset_index().drop(['index'], axis=1)

        num = 0
        for index, _ in self.df_square[self.df_square['grid']==selected_grid].iterrows():
            self.df_square.loc[index, 'square'] = num
            num+=1

        num = 0
        for index, _ in self.df_square_org_index.iterrows():
            self.df_target.loc[self.df_target['square']==index, 'square'] = num
            num+=1
        print(self.df_square)

    def del_grid(self):
        try:
            selected_grid = self.tv_whole_grid.get_children().index(self.tv_whole_grid.selection()[0])
            existing_grid = self.tv_whole_grid.get_children()
        except IndexError:
            raise RuntimeError('Please select grid level.')

        self.tv_grid_square.delete(*self.tv_grid_square.get_children())
        self.tv_target.delete(*self.tv_target.get_children())
        self.tv_whole_grid.delete(existing_grid[selected_grid])
        self.df_grid_org_index = self.df_grid[(self.df_grid['grid']!=selected_grid)]
        self.df_grid = self.df_grid[(self.df_grid['grid']!=selected_grid)].reset_index().drop(['index'], axis=1)
        self.df_square = self.df_square[(self.df_square['grid']!=selected_grid)].reset_index().drop(['index'], axis=1)
        self.df_target = self.df_target[(self.df_target['grid']!=selected_grid)].reset_index().drop(['index'], axis=1)

        num = 0
        for index, _ in self.df_grid.iterrows():
            self.df_grid.loc[index, 'grid'] = num
            num += 1
        
        num = 0
        for index, _ in self.df_grid_org_index.iterrows():
            self.df_square.loc[self.df_square['grid']==index, 'grid'] = num
            self.df_target.loc[self.df_target['grid']==index, 'grid'] = num
            num += 1
        
    def save_grid(self):
        # grid g_x g_y 
        # grid square s_x_sy 
        # square target t_x t_y
        if self.grid_dir is not None:
            dir_name = Path(self.grid_dir)
            sample_name = self.var_name.get()
            self.df_grid.to_csv(dir_name/f'grid_{sample_name}.csv', index=False)
            self.df_square.to_csv(dir_name/f'square_{sample_name}.csv', index=False)
            self.df_target.to_csv(dir_name/f'target_{sample_name}.csv', index=False)

    def load_grid(self):
        dir_name = filedialog.askdirectory(initialdir=self.grid_dir, title='Load Whole Grid')
        dir_name = Path(dir_name)
        files = dir_name.glob('*.csv')
        for file in files:
            if 'grid' in file:
                self.df_grid = pd.read_csv(file)
            elif 'square' in file:
                self.df_square = pd.read_csv(file)
            elif 'target' in file:
                self.df_target = pd.read_csv(file)
                             

if __name__ == '__main__':
    root = Tk()
    CryoED(root).pack(side='top', fill='both', expand=True)
    root.mainloop()