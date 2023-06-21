import os

show_name = ""
start_season = 5
current_season = 0
cwd = os.getcwd()
for filename in os.listdir(cwd):
    fp = os.path.join(cwd, filename)
    for folder in os.listdir(cwd):
        if(os.path.isdir(os.path.join(cwd, folder))):
            if folder.startswith("Season "):
                current_season=int(folder[7:])
                if current_season < start_season:
                    continue
                current_episode=0
                for file in os.listdir(os.path.join(cwd, folder)):
                    current_episode+=1
                    print(file)
                    header =""
                    footer = ""
                    if file.startswith(header) and file.endswith(footer):
                        new_filename = f"{show_name} S{format(current_season).zfill(2)}E{format(current_episode).zfill(2)} "+file[len(header)+7:-len(footer)].replace('.', ' ').replace('_','-') + file[-4:]
                        print(new_filename)
                    else: 
                        episode_name = input(f"S{format(current_season).zfill(2)}E{format(current_episode).zfill(2)} name:")
                        new_filename = f"{show_name} S{format(current_season).zfill(2)}E{format(current_episode).zfill(2)} {episode_name}{file[-4:]}"
                    os.rename(os.path.join(cwd, folder, file), os.path.join(cwd, folder, new_filename))
                exit(0)