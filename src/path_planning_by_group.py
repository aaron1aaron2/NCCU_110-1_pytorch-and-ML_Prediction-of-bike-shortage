# encoding: utf-8
"""
Author: yen-nan ho
Contact: aaron1aaron2@gmail.com
GitHub: https://github.com/aaron1aaron2
Create Date:  20211210
"""
# from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import pandas as pd 
import numpy as np
import itertools
from geopy.distance import geodesic

__all__ =['get_linear_distance', 'to_whole_Htable', 'optimize_distance', 'Get_STP_route']

##############################################################################
#part 1: 整理資料，獲取每個區域點到點的距離table

def get_linear_distance(df, group:str=None, coor_col:str='coordinate', id_col:str='no', unit='km')->pd.DataFrame:
    '''輸入資料表需包含經緯、地址、id，會依序執行下列步驟
        1. 依造 group ，生成群組內每點到每點的資料表
        2. 依據每筆資料的經緯(起始、結束)算出直線距離
        3. 輸出資料

        注意:
        - coor_col 作為點的經緯欄位，格式必須為 `'緯度,經度'` 。
        - unit 可以選擇 meter 或是 km。
    '''
    if group==None:
        df['group'] = 1
        group = 'group'

    # 檢查輸入參數
    for arg in [group, coor_col, id_col]:
        assert arg in df.columns, "'{}' not in dataframe! please check a column name.".format(arg)

    df = df[[group, coor_col, id_col]]
    #產生配對
    df_AB = df.groupby(df[group]).apply(lambda x:pd.DataFrame(list(itertools.combinations(x[id_col], 2))))
    df.drop([group], axis=1, inplace=True)

    #資料合併
    df_AB = df_AB.rename(columns={0:'start_id',1:'end_id'})

    df_start = df.rename(columns={
        '{}'.format(coor_col):'start_coordinate',
        '{}'.format(id_col):'start_id'
        })
    
    del df

    df_AB = pd.merge(df_AB, df_start, on=['start_id'],how='left')

    df_end = df_start.rename(columns={
        'start_coordinate':'end_coordinate',
        'start_id':'end_id'
        })

    df_AB = pd.merge(df_AB, df_end, on=['end_id'], how='left')
    
    #配合 geopy的資料格式
    if unit=='meter':
        df_AB['linear_distance'] = df_AB.apply(lambda x:geodesic(x['start_coordinate'].split(','),x['end_coordinate'].split(',')).meters,axis=1)
    if unit=='km':
        df_AB['linear_distance'] = df_AB.apply(lambda x:geodesic(x['start_coordinate'].split(','),x['end_coordinate'].split(',')).kilometers,axis=1)
    
    
    return df_AB

def to_whole_Htable(df, distance_Table, coor_col='coordinate', id_col='no')->pd.DataFrame:
    '''補上自己到自己，B到A，到可以產生 distance matrix的狀態'''

    # 檢查參數
    for arg in [coor_col, id_col]:
        assert arg in df.columns, "[{}] not in dataframe input".format(arg)

    df = df[[coor_col, id_col]]

    # 自己到自己補零
    df.rename(columns={
        '{}'.format(id_col):'start_id',
        '{}'.format(coor_col):'start_coordinate'}, inplace=True)

    df_end = df.rename(columns={
                'start_id':'end_id',
                'start_coordinate':'end_coordinate'
                })

    df_self = pd.concat([df, df_end], sort=True, axis=1)
    df_self['linear_distance'] = np.zeros(shape=(len(df),1))

    # 建立來回
    distance_Table_T = distance_Table.rename(columns={
        'start_coordinate':'end_coordinate',
        'end_coordinate':'start_coordinate',
        'start_id':'end_id',
        'end_id':'start_id'
        })
    
    # 合併
    distance_Table_all = pd.concat([distance_Table, distance_Table_T, df_self],sort=True)

    return distance_Table_all[distance_Table.columns]

def optimize_distance(df_back, distance_Table_all, start_coor:str, end_coor:str)->pd.DataFrame:
    '''將爬取回的資料併回原本資料，並填補為爬取到的資料'''
    #翻轉AB
    df_back = df_back.dropna()
    df_back = df_back.drop_duplicates()
    df_reverse = df_back.rename(columns={
                                    start_coor:end_coor,
                                    end_coor:start_coor
                                    })

    df_all = pd.concat([df_back,df_reverse], sort=True)
    
    #使用經緯(latlong)合併其他資料
    df_optimize = pd.merge(distance_Table_all , df_all, on=[start_coor,end_coor], how='left')
    
    return df_optimize

#############################################################################
# part 2: 用 Google or_tool 計算STP路徑。
def create_data_model(distance_matrix):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = distance_matrix
    data['num_vehicles'] = 1 #The number of vehicles in the problem, which is 1 because this is a TSP. For general routing problems, the number of vehicles can be greater than 1.
    data['depot'] = 0  # 起點，the starting location for the route. In this case, the depot is 0, which corresponds to New York City.
    return data

def print_solution(route):
    """Prints assignment on console."""
    manager, routing, assignment=route
    print('Objective: {} meters'.format(assignment.ObjectiveValue())) # 目標最短距離
    index = routing.Start(0) 
    plan_output = 'Route for vehicle 0:\n' 
    route_distance = 0
    tmp=[]
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(manager.IndexToNode(index)) 
        previous_index = index
        tmp.append(index)
        index = assignment.Value(routing.NextVar(index)) #到下個點
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)#到下個點的距離
    tmp.append(0) #回到原點
    plan_output += ' {}\n'.format(manager.IndexToNode(index))
    plan_output += 'Route distance: {} meters\n'.format(route_distance)
    print(plan_output)
    return {'path':tmp,'distance':route_distance}
    
def STP_route(distance_matrix):
    data = create_data_model(distance_matrix)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']), data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if assignment:
        return manager,routing, assignment

def Get_STP_route(distance_Table_all, group, target_col):  
    '''每個區域跑一個最佳路徑，注意distance這行為參考的變量'''
    # 生成區域編號，google需要有從0開始的編號
    distance_Table_all = distance_Table_all.loc[distance_Table_all[group].dropna().index.to_list()]
    distance_Table_input = distance_Table_all[[target_col,'start_id','end_id']]
    distance_Table_input = distance_Table_input.drop_duplicates(subset=['start_id','end_id'])
    distance_Table_input.rename(columns={target_col:'value'}, inplace=True)
    distance_Table_all['value'] = distance_Table_all[target_col].fillna(0)


    def routeing_in_area(group):
        '''對每個group 規劃路徑'''
        id_ls = list(group.start_id.unique())
        no_ls = [i for i in range(len(id_ls))]
        no_df = pd.DataFrame(zip(id_ls, no_ls), columns=['start_id', 'start_no'])
        group = group.merge(no_df, how='left')

        no_df.rename(columns={'start_id':'end_id', 'start_no':'end_no'}, inplace=True)

        group = group.merge(no_df, how='left')

        distance_matrix_area = group.pivot(index='start_no', columns='end_no', values='value')
       
        # 丟給 google 計算最佳路徑    
        route = STP_route(distance_matrix_area)
        path_distance = print_solution(route) #返回distance(總距離)、path(路徑id_list)
        
        # 生成區域path table
        path = pd.DataFrame(path_distance['path'][:-1],columns=['start_no'])
        path['end_no'] = path_distance['path'][1:]
        path_table = path.merge(group[['start_id','end_id','start_no','end_no']], on=['start_no','end_no'],how='left')


        return path_table

    distance_Table_path = distance_Table_input.groupby(distance_Table_all[group]).apply(routeing_in_area)
    distance_Table_path = distance_Table_path.reset_index(drop=True)
    path_table = distance_Table_path.merge(distance_Table_all, on=['start_id','end_id'], how='left')
    
    path_table['total_value'] = 0
    for gp in path_table.group.unique():
        path_table.loc[path_table.group==gp, 'total_value'] = path_table.loc[path_table.group==gp, 'value'].sum()
    return path_table
    

if __name__=='__main__':
    path = ''