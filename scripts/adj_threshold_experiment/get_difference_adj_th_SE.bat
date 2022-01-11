@echo off 

set input_file="data/train_data/spot_info_id_table.csv"
set adjs=(0,0.00124,0.03739,0.20827,0.34703)

for %%d in %adjs% do (
    python data_helper_SE.py --file_path %input_file% ^
    --output_folder "data/train_data/SE/test_adj/adj%%d" ^
    --adj_threshold %%d --id_col new_id --longitude_col lng --latitude_col lat 
)

pause