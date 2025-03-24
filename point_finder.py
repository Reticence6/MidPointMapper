import numpy as np
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import requests

class EquidistantPointsFinder:
    def __init__(self, config):
        self.geolocator = Nominatim(user_agent="my_agent")
        self.config = config
        self.amap_key = config["amap_key"]
        
    def get_location_by_name(self, address):
        """通过地址名称获取经纬度"""
        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {
            "key": self.amap_key,
            "address": address
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data["status"] == "1" and data["geocodes"]:
                location = data["geocodes"][0]["location"].split(",")
                return {
                    "name": address,
                    "longitude": float(location[0]),
                    "latitude": float(location[1])
                }
            else:
                print(f"警告：无法找到地址 '{address}' 的经纬度信息")
                return None
        except Exception as e:
            print(f"获取地址 '{address}' 的经纬度信息时出错: {e}")
            return None
    
    def calculate_distance(self, point1, point2):
        """计算两点之间的距离（公里）"""
        return geodesic(point1, point2).kilometers
    
    def find_equidistant_points(self, points):
        """
        查找距离所有给定点距离相等的点
        points: 列表，包含(lat, lon)元组
        """
        # 从配置文件获取搜索范围
        bounds = self.config["map_bounds"]
        grid_size = self.config["search_params"]["grid_size"]
        tolerance = self.config["search_params"]["tolerance"]
        
        lat_range = np.linspace(bounds["min_lat"], bounds["max_lat"], grid_size)
        lon_range = np.linspace(bounds["min_lon"], bounds["max_lon"], grid_size)
        
        equidistant_points = []
        
        for lat in lat_range:
            for lon in lon_range:
                distances = [self.calculate_distance((lat, lon), point) for point in points]
                if max(distances) - min(distances) <= tolerance:
                    equidistant_points.append((lat, lon))
        
        return equidistant_points

    def find_fuzzy_equidistant_points(self, points, max_distance=None, distance_ratio=1.2):
        """
        查找模糊等距点，这些点到所有给定点的距离相对均衡
        points: 列表，包含(lat, lon)元组
        max_distance: 最大允许距离（公里），如果为None则自动计算
        distance_ratio: 允许的最大距离与最小距离的比率
        """
        # 从配置文件获取搜索范围
        bounds = self.config["map_bounds"]
        grid_size = self.config["search_params"]["grid_size"]
        
        # 如果没有指定最大距离，则用输入点之间的最大距离作为参考
        if max_distance is None:
            max_distance = 0
            for i, p1 in enumerate(points):
                for j, p2 in enumerate(points[i+1:], i+1):
                    dist = self.calculate_distance(p1, p2)
                    max_distance = max(max_distance, dist)
            max_distance *= 1.5  # 将最大距离扩大1.5倍作为搜索范围
        
        lat_range = np.linspace(bounds["min_lat"], bounds["max_lat"], grid_size)
        lon_range = np.linspace(bounds["min_lon"], bounds["max_lon"], grid_size)
        
        fuzzy_points = []
        
        for lat in lat_range:
            for lon in lon_range:
                distances = [self.calculate_distance((lat, lon), point) for point in points]
                max_dist = max(distances)
                min_dist = min(distances)
                
                # 判断条件：
                # 1. 最大距离不超过指定值
                # 2. 最大距离和最小距离的比率不超过指定值
                if max_dist <= max_distance and max_dist/min_dist <= distance_ratio:
                    fuzzy_points.append((lat, lon))
        
        # 按照距离标准差排序，返回方差最小的前N个点
        fuzzy_points.sort(key=lambda p: np.std([self.calculate_distance(p, point) for point in points]))
        return fuzzy_points
    
    def get_nearby_cities(self, lat, lon):
        """获取指定点附近的城市信息"""
        url = f"https://restapi.amap.com/v3/geocode/regeo"
        params = {
            "key": self.amap_key,
            "location": f"{lon},{lat}",
            "radius": self.config["search_params"]["radius"],
            "extensions": "all"
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data["status"] == "1":
                address_component = data["regeocode"]["addressComponent"]
                
                # 检查是否是中国城市
                if address_component.get("country") != "中国":
                    return None
                
                # 如果是海边城市，获取附近城市
                if "海" in address_component.get("province", "") or "海" in address_component.get("city", ""):
                    # 扩大搜索半径获取更多城市
                    params["radius"] = "100000"  # 增加到100公里
                    response = requests.get(url, params=params)
                    data = response.json()
                    if data["status"] == "1":
                        # 获取周边城市列表
                        pois = data["regeocode"].get("pois", [])
                        nearby_cities = []
                        for poi in pois:
                            if poi.get("type") == "地名地址信息":
                                city_info = {
                                    "province": poi.get("adname", "").split(" ")[0],
                                    "city": poi.get("adname", "").split(" ")[1] if len(poi.get("adname", "").split(" ")) > 1 else "",
                                    "distance": float(poi.get("distance", 0))
                                }
                                if city_info["province"] and city_info["city"]:
                                    nearby_cities.append(city_info)
                        
                        # 按距离排序，返回最近的3个城市
                        nearby_cities.sort(key=lambda x: x["distance"])
                        if nearby_cities:
                            return nearby_cities[:3]
                
                return address_component
            return None
        except Exception as e:
            print(f"获取城市信息时出错: {e}")
            return None 