import chemical
import os
import shutil
import subprocess
import argparse as arg

#######################################################################################################################################################################

parser = arg.ArgumentParser(prog = "FDF_Creator", formatter_class = arg.RawDescriptionHelpFormatter, description = "Program used to make the k point test", epilog= """Some Examples: """)

parser.add_argument("-l", dest = "label", type = str, required = True, help = "Label of file")
parser.add_argument("-k", dest = "k_points", nargs ="+", type=int, required = True, metavar = "k_points", help = "k_points values (in order)")
parser.add_argument("-n", dest = "n_proc", type = str, required = True, help = "Number of Procesors")

args = parser.parse_args()

#######################################################################################################################################################################

label_name = args.label

kp_values = args.k_points

fdf_file = label_name + ".fdf"

path_psml = "~/Siesta_Standart_psml/Scalar_Relativistic/"

cell_type = "2D"

n_proc = args.n_proc

#######################################################################################################################################################################

def kp_adjust(fdf_file, kp):
    file_path = os.path.join(dir_aux, fdf_file)
    
    in_block = False

    with open(file_path, "r") as f:
        line = f.read().splitlines()

    new_lines = []
    in_block = False

    for info in line:

        if "MD.VariableCell" in info:
            new_lines.append("MD.VariableCell False")
            continue
        
        if "MD.Steps" in info:
            new_lines.append("MD.Steps 0")
            continue

        if "MD.UseSaveXV" in info:
            new_lines.append("MD.UseSaveXV True")
            continue

        if "DM.UseSaveDM" in info:
            new_lines.append("DM.UseSaveDM False")
            continue

        if "%block kgrid_Monkhorst_Pack" in info:
            in_block = True
            new_lines.append(info)
            block = kp_block(cell_type, kp)
            new_lines.extend(block.splitlines()[1:-1])
            continue

        if "%endblock kgrid_Monkhorst_Pack" in info:
            in_block = False
            new_lines.append(info)
            continue

        if not in_block:
            new_lines.append(info)

    with open(file_path, "w") as f:
        f.write("\n".join(new_lines) + "\n")

def kp_block(cell_type, kp):
    if cell_type == "2D":
        block = f"""%block kgrid_Monkhorst_Pack
    {kp} 0 0 {0.5 if kp % 2 == 0 else 0.0}
    0 {kp} 0 {0.5 if kp % 2 == 0 else 0.0}
    0 0 1 0.0
%endblock kgrid_Monkhorst_Pack"""
    elif cell_type == "3D":
        block = f"""%block kgrid_Monkhorst_Pack
    {kp} 0 0 {0.5 if kp % 2 == 0 else 0.0}
    0 {kp} 0 {0.5 if kp % 2 == 0 else 0.0}
    0 0 {kp} {0.5 if kp % 2 == 0 else 0.0}
%endblock kgrid_Monkhorst_Pack"""
    else:
        print("ERROR, Choose 2D or 3D")
    return block

#######################################################################################################################################################################

os.getcwd()

dir_kp = 'kp'

if os.path.exists(dir_kp):
    shutil.rmtree(dir_kp)
os.makedirs(dir_kp, exist_ok = True)

for i, kp in enumerate(kp_values):
    dir_aux = os.path.join(dir_kp,f'kp_{kp}')
    
    os.makedirs(dir_aux, exist_ok= True)
    
    shutil.copy(fdf_file, dir_aux)
    shutil.copy(label_name + ".XV", dir_aux)
    shutil.copy(label_name + ".DM", dir_aux)

    chemical.psml_find(fdf_file,dir_aux,path_psml)

    kp_adjust(fdf_file,kp)

    os.environ["OMP_NUM_THREADS"] = "1"

    command = ["/usr/bin/mpirun", "-np", str(n_proc), "/home/usr/bin/siesta-5.0.0/MPICH2/bin/siesta"]

    fdf_aux = os.path.join(dir_aux,label_name + ".fdf")
    out_aux = os.path.join(dir_aux,"log.out")
        
    with open(out_aux, 'w') as f_out, open(fdf_aux, 'r') as f_in:
        subprocess.run(
            command,
            cwd =dir_aux,
            stdin =f_in,
            stdout =f_out,
            stderr =subprocess.STDOUT,
            check =True
                          )
