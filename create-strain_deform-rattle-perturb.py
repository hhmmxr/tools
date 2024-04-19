"""
    Purpose:
        对已有不同原型结构，利用hiphive和dpdata两个python包生成应变(generate_strained_structure)、
        形变(generate_deformed_structure)、扩胞后的应变+原子坐标微扰(rattled_structure)、
        晶格+原子坐标都微扰(perturbed_system) 四种
    Notice:
        hiphive导出POSCAR好像有bug，所以先输出了xyz再转换成POSCAR，扩胞后的perturb没写(应该够了)
        准备好原始构型、INCAR、POTCAR 直接python3 create-strain_deform-rattle-perturb.py即可
"""
import numpy as np
from ase.io import write,read
from hiphive.structure_generation.rattle import generate_mc_rattled_structures
from ovito.io import import_file, export_file
from ovito.modifiers import WrapPeriodicImagesModifier
import os
import shutil
import subprocess
import dpdata
import string

prototype_structures = {}
prototype_structures['1'] = read('POSCAR1') #读取原型结构，想读几个写几个
prototype_structures['2'] = read('POSCAR2') #
prototype_structures['3'] = read('POSCAR3')
prototype_structures['4'] = read('POSCAR4')
prototype_structures['5'] = read('POSCAR5')
prototype_structures['6'] = read('POSCAR6')

def generate_strained_structure(prim, strain_lim):
    strains = np.random.uniform(*strain_lim, (3, ))
    atoms = prim.copy()
    cell_new = prim.cell[:] * (1 + strains)
    atoms.set_cell(cell_new, scale_atoms=True)
    return atoms

def generate_deformed_structure(prim, strain_lim):
    R = np.random.uniform(*strain_lim, (3, 3))
    M = np.eye(3) + R
    atoms = prim.copy()
    cell_new = M @ atoms.cell[:]
    atoms.set_cell(cell_new, scale_atoms=True)
    return atoms

strain_lim = [-0.05, 0.05] #形变范围
n_structures = 10 #生成个数
training_structures = []
strain_deform_folder = 'strain_deform'
os.makedirs(strain_deform_folder, exist_ok=True)

for name, prim in prototype_structures.items():
    for it in range(n_structures):
        prim_strained = generate_strained_structure(prim, strain_lim)
        prim_deformed = generate_deformed_structure(prim, strain_lim)
        training_structures.append(prim_strained)
        training_structures.append(prim_deformed)

for i, structure in enumerate(training_structures):
    folder_name = f'train-{i+1}'
    folder_path = os.path.join(strain_deform_folder, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    output_file_path = os.path.join(folder_path, f'structure_{i+1}.xyz')
    structure.info['config_type'] = f'structure_{i+1}'
    structure.write(output_file_path, format='extxyz')

def convert_train_xyz_to_poscar():
     train_folder_path = os.path.join(os.getcwd(), 'strain_deform')
     folders = os.listdir(train_folder_path)
     for folder_name in folders:
         folder_path = os.path.join(train_folder_path, folder_name)
         xyz_files = [f for f in os.listdir(folder_path) if f.endswith('.xyz')]
         for xyz_file in xyz_files:
             xyz_filepath = os.path.join(folder_path, xyz_file)
             poscar_filepath = os.path.join(folder_path, xyz_file.replace('.xyz', '.vasp'))
             pipeline = import_file(xyz_filepath)
             pipeline.modifiers.append(WrapPeriodicImagesModifier())
             export_file(pipeline, poscar_filepath, 'vasp')
             new_poscar_filepath = os.path.join(folder_path, 'POSCAR')
             os.rename(poscar_filepath, new_poscar_filepath)
convert_train_xyz_to_poscar()

print('Number of training structures:', len(training_structures))

n_structures = 10 #生成个数
rattle_std = 0.03 #原子位移决定参数
d_min = 1.8 #最小原子间距离
n_iter = 5 #原子位移决定参数
#位移=n_iter**0.5 * rattle_std
size_vals = {}
size_vals['1'] = [(1,1,1), (1,2,1)] #扩胞大小
size_vals['2'] = [(1,1,1)] #前面中括号名要跟上面一样
size_vals['3'] = [(1,1,1)]
size_vals['4'] = [(1,1,1)]
size_vals['5'] = [(1,1,1)]
size_vals['6'] = [(1,1,1)]

rattle_folder = 'rattle'
for name, prim in prototype_structures.items():
    for size in size_vals[name]:
        for it in range(n_structures):
            folder_name = f"{name}_size_{size}_iter_{it}"
            folder_path = os.path.join(rattle_folder, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            supercell = generate_strained_structure(prim.repeat(size), strain_lim)
            rattled_supercells = generate_mc_rattled_structures(supercell, n_structures=1, rattle_std=rattle_std, d_min=d_min, n_iter=n_iter)
            print(f'{name}, size {size}, natoms {len(supercell)},  volume {supercell.get_volume() / len(supercell):.3f}')
            training_structures.extend(rattled_supercells)
            for i, rattled_structure in enumerate(rattled_supercells):
                output_file_path = f'{name}_size_{size}_iter_{it}_structure_{i}.xyz'
                structure_file_path = os.path.join(folder_path, output_file_path)
                rattled_structure.info['config_type'] = f'{name}_size_{size}_iter_{it}_structure_{i}'
                rattled_structure.write(structure_file_path, format='extxyz')

def convert_train_xyz_to_poscar():
     train_folder_path = os.path.join(os.getcwd(), 'rattle')
     folders = os.listdir(train_folder_path)
     for folder_name in folders:
         folder_path = os.path.join(train_folder_path, folder_name)
         xyz_files = [f for f in os.listdir(folder_path) if f.endswith('.xyz')]
         for xyz_file in xyz_files:
             xyz_filepath = os.path.join(folder_path, xyz_file)
             poscar_filepath = os.path.join(folder_path, xyz_file.replace('.xyz', '.vasp'))
             pipeline = import_file(xyz_filepath)
             pipeline.modifiers.append(WrapPeriodicImagesModifier())
             export_file(pipeline, poscar_filepath, 'vasp')
             new_poscar_filepath = os.path.join(folder_path, 'POSCAR')
             os.rename(poscar_filepath, new_poscar_filepath)
convert_train_xyz_to_poscar()

def remove_parentheses(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for folder in dirs:
            translation_table = str.maketrans("", "", "() ")
            new_folder_name = folder.translate(translation_table)
            if new_folder_name != folder:
                old_path = os.path.join(root, folder)
                new_path = os.path.join(root, new_folder_name)
                os.rename(old_path, new_path)

if __name__ == "__main__":
    target_directory = "./"
    remove_parentheses(target_directory)

original_cwd = os.getcwd()
for i in range(1, 7): #几个原始构型就写到几+1，我这是6个原始构型
    perturb_directory = f'perturb-{i}'
    os.makedirs(perturb_directory, exist_ok=True)
    shutil.copyfile(f'POSCAR{i}', os.path.join(f'perturb-{i}', 'CONTCAR'))
    os.chdir(perturb_directory)

    for j in range(1, 26): #与下面两个25对应，生成25个微扰结构和文件夹
        train_directory = f'train-{j}'
        os.makedirs(train_directory, exist_ok=True)
        directory = os.getcwd()
        perturbed_system = dpdata.System('CONTCAR').perturb(pert_num=25,
                                                           cell_pert_fraction=0.03,
                                                           atom_pert_distance=0.2,
                                                           atom_pert_style='normal')

        for k in range(25):
            poscar_filename = f'POSCAR{k+1}'
            perturbed_system.to_vasp_poscar(poscar_filename, frame_idx=k)
            shutil.move(poscar_filename, os.path.join(train_directory, 'POSCAR'))
    os.chdir('..')
os.chdir(original_cwd)

original_cwd = os.getcwd()
for folder_name in os.listdir(original_cwd):
    folder_path = os.path.join(original_cwd, folder_name)
    if os.path.isdir(folder_path):
        for subfolder_name in os.listdir(folder_path):
            subfolder_path = os.path.join(folder_path, subfolder_name)
            if os.path.isdir(subfolder_path):
                shutil.copy("INCAR", subfolder_path)
                os.chdir(subfolder_path)
                vaspkit_command = "vaspkit -task 102 -kpr 0.04" #K-Spacing取0.04
                subprocess.run(vaspkit_command, shell=True)
                os.chdir(original_cwd)

