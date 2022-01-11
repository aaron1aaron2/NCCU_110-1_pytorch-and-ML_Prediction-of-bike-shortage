@REM 關掉回傳命令，不會回傳 bat 程式碼本身
@echo off 

@REM 設置變數用 set
set testonevar=True
set input_file="data/train_data/spot_info_id_table.csv"
set vars=("adjs","walklenghts","numwalks","ps","qs")

@REM set dims=(32,64,100) 需要改 k、d
@REM set windowsizes=(2,6,10)
set walklengths=(50,80,100)
set numwalks=(50,80,100)
set ps=(0.5,1,2)
set qs=(0.5,1,1.5)
set adjs=(0,0.077,0.412)

@REM 注意當不是測試變數時會使用 data_helper_SE.py 的預設參數
if %testonevar%==True (
    echo test with one var
    for %%v in %vars% do (
        echo %%v
        if %%v=="adjs" (
            for %%d in %adjs% do (
                python data_helper_SE.py --file_path %input_file% ^
                --output_folder "data/train_data/SE/test_%%v/D%%d_WS10_WL80_NW100_P2_Q1" ^
                --adj_threshold %%d --id_col new_id --longitude_col lng --latitude_col lat 
            )
        )

        @REM if %%v=="dims" (
        @REM     for %%d in %dims% do (
        @REM         python data_helper_SE.py --file_path %input_file%^
        @REM         --output_folder "data/train_data/SE/test_%%v/D%%d_WS10_WL80_NW100_P2_Q1"^
        @REM         --dimensions %%d 
        @REM     )
        @REM )

        @REM if %%v=="windowsizes" (
        @REM     for %%w in %windowsizes% do (
        @REM         python data_helper_SE.py --file_path %input_file%^
        @REM         --output_folder "data/train_data/SE/test_%%v/D64_WS%%w_WL80_NW100_P2_Q1"^
        @REM         --window_size %%w 
        @REM     )
        @REM )

        if %%v=="walklenghts" (
            for %%l in %walklengths% do (
                python data_helper_SE.py --file_path %input_file%^
                --output_folder "data/train_data/SE/test_%%v/D64_WS10_WL%%l_NW100_P2_Q1"^
                --walk_length %%l --id_col new_id --longitude_col lng --latitude_col lat 
            )
        )

        if %%v=="numwalks" (
            for %%n in %numwalks% do (
                python data_helper_SE.py --file_path %input_file%^
                --output_folder "data/train_data/SE/test_%%v/D64_WS10_WL80_NW%%n_P2_Q1"^
                --num_walks %%n --id_col new_id --longitude_col lng --latitude_col lat 
            )     
        )

        if %%v=="ps" (
            for %%p in %ps% do (
                python data_helper_SE.py --file_path %input_file%^
                --output_folder "data/train_data/SE/test_%%v/D64_WS10_WL80_NW100_P%%p_Q1"^
                --p %%p --id_col new_id --group_col sarea --longitude_col lng --latitude_col lat 
            )
        )

        if %%v=="qs" (
            for %%q in %qs% do (
                python data_helper_SE.py --file_path %input_file%^
                --output_folder "data/train_data/SE/test_%%v/D64_WS10_WL80_NW100_P2_Q%%q"^
                --q %%q --id_col new_id --group_col sarea --longitude_col lng --latitude_col lat 
            )                        
        )
    )
)

pause

