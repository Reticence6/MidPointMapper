import json
from point_finder import EquidistantPointsFinder
from map_visualizer import MapVisualizer

def load_config(config_file="config.json"):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return None

def get_city_key(city_info):
    """获取城市的唯一标识"""
    if not city_info:
        return None
    return f"{city_info.get('province', '')}_{city_info.get('city', '')}"

def process_points(finder, points, is_fuzzy=False):
    """处理并返回点的信息，去除重复城市"""
    point_infos = []
    city_dict = {}  # 用于存储已处理的城市
    
    for i, point in enumerate(points[:10]):
        city_info = finder.get_nearby_cities(point[0], point[1])
        if city_info:
            # 处理海边城市的情况
            if isinstance(city_info, list):
                # 海边城市，显示最近的3个城市
                letter = chr(65 + i)
                point_type = "模糊等距点" if is_fuzzy else "等距点"
                info_text = f"{point_type}{letter}:\n"
                info_text += f"  坐标: ({point[0]:.4f}, {point[1]:.4f})\n"
                info_text += "  临近城市:\n"
                for j, city in enumerate(city_info, 1):
                    info_text += f"    {j}. {city['province']} {city['city']} (距离: {city['distance']:.1f}公里)\n"
                point_infos.append((point, info_text))
                
                # 打印到控制台
                print(f"\n{point_type}{letter}:")
                print(f"坐标: {point}")
                print("临近城市:")
                for j, city in enumerate(city_info, 1):
                    print(f"  {j}. {city['province']} {city['city']} (距离: {city['distance']:.1f}公里)")
            else:
                # 普通城市
                city_key = get_city_key(city_info)
                if city_key and city_key not in city_dict:
                    letter = chr(65 + i)
                    point_type = "模糊等距点" if is_fuzzy else "等距点"
                    info_text = f"{point_type}{letter}:\n"
                    info_text += f"  省份: {city_info.get('province', '未知')}\n"
                    info_text += f"  城市: {city_info.get('city', '未知')}\n"
                    info_text += f"  坐标: ({point[0]:.4f}, {point[1]:.4f})"
                    point_infos.append((point, info_text))
                    city_dict[city_key] = True
                    
                    # 打印到控制台
                    print(f"\n{point_type}{letter}:")
                    print(f"坐标: {point}")
                    print(f"省份: {city_info.get('province', '未知')}")
                    print(f"城市: {city_info.get('city', '未知')}")
    
    return point_infos

def find_and_visualize_points(config_file="config.json"):
    """主函数：查找并可视化等距点"""
    # 加载配置
    config = load_config(config_file)
    if not config:
        return
    
    # 创建查找器和可视化器
    finder = EquidistantPointsFinder(config)
    visualizer = MapVisualizer(config)
    
    # 获取所有输入点的经纬度
    input_points = []
    print("正在获取输入点的经纬度信息...")
    for address in config["input_points"]:
        location = finder.get_location_by_name(address)
        if location:
            input_points.append((location["latitude"], location["longitude"]))
            print(f"成功获取 '{address}' 的经纬度: {location['latitude']}, {location['longitude']}")
        else:
            print(f"无法获取 '{address}' 的经纬度信息，程序退出")
            return
    
    if len(input_points) < 2:
        print("至少需要两个有效的输入点才能计算等距点")
        return
    
    # 查找严格等距点
    print("\n开始计算严格等距点...")
    equidistant_points = finder.find_equidistant_points(input_points)
    print(f"\n找到 {len(equidistant_points)} 个严格等距点")
    
    # 查找模糊等距点
    print("\n开始计算模糊等距点...")
    fuzzy_points = finder.find_fuzzy_equidistant_points(input_points)
    print(f"找到 {len(fuzzy_points)} 个模糊等距点")
    
    # 处理严格等距点信息
    equidistant_point_infos = []
    if equidistant_points:
        print("\n严格等距点详细信息：")
        equidistant_point_infos = process_points(finder, equidistant_points)
    
    # 处理模糊等距点信息，去除与严格等距点重复的城市
    fuzzy_point_infos = []
    if fuzzy_points:
        print("\n模糊等距点详细信息：")
        fuzzy_point_infos = process_points(finder, fuzzy_points, is_fuzzy=True)
    
    # 分离点和信息
    equidistant_points = [p for p, _ in equidistant_point_infos]
    equidistant_infos = [i for _, i in equidistant_point_infos]
    fuzzy_points = [p for p, _ in fuzzy_point_infos]
    fuzzy_infos = [i for _, i in fuzzy_point_infos]
    
    # 可视化所有点
    if equidistant_points or fuzzy_points:
        print("\n正在生成可视化图表...")
        visualizer.visualize_points(input_points, equidistant_points, fuzzy_points, 
                                  equidistant_infos, fuzzy_infos)
    else:
        print("\n未找到任何等距点或模糊等距点")

if __name__ == "__main__":
    find_and_visualize_points() 