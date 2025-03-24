import numpy as np
import matplotlib.pyplot as plt
import requests
from PIL import Image
from io import BytesIO
import time

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class MapVisualizer:
    def __init__(self, config):
        self.config = config
        self.amap_key = config["amap_key"]
    
    def get_static_map(self, points, equidistant_points, fuzzy_points):
        """获取高德地图静态图"""
        # 计算所有点的边界
        all_points = points + (equidistant_points if equidistant_points else []) + (fuzzy_points if fuzzy_points else [])
        lats, lons = zip(*all_points)
        
        # 计算中心点和缩放级别
        center_lon = (max(lons) + min(lons)) / 2
        center_lat = (max(lats) + min(lats)) / 2
        
        # 计算合适的缩放级别
        lat_span = max(lats) - min(lats)
        lon_span = max(lons) - min(lons)
        # 根据跨度计算合适的缩放级别，确保所有点都在视野内
        zoom = min(8, max(4, int(-1.2 * np.log2(max(lat_span, lon_span)))))
        
        # 构建静态地图URL
        markers = []
        # 添加输入点标记（大号点）
        for i, point in enumerate(points):
            # 使用数字1-9作为输入点标记
            markers.append(f"large,0xFF0000,{i+1}:{point[1]},{point[0]}")
        
        # 添加严格等距点标记（蓝色）
        if equidistant_points:
            for i, point in enumerate(equidistant_points[:10]):
                letter = chr(65 + i)
                markers.append(f"large,0x0000FF,{letter}:{point[1]},{point[0]}")
        
        # 添加模糊等距点标记（绿色）
        if fuzzy_points:
            for i, point in enumerate(fuzzy_points[:10]):
                letter = chr(65 + i + len(equidistant_points[:10]))  # 继续使用字母标记
                markers.append(f"large,0x00FF00,{letter}:{point[1]},{point[0]}")
        
        markers_str = "|".join(markers)
        
        url = f"https://restapi.amap.com/v3/staticmap"
        params = {
            "key": self.amap_key,
            "location": f"{center_lon},{center_lat}",
            "zoom": zoom,
            "size": "1024*768",
            "markers": markers_str,
            "scale": 2
        }
        
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                print(f"正在请求地图... (尝试 {attempt + 1}/{max_retries})")
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    # 保存响应内容以便调试
                    with open(f"map_response_{attempt}.png", "wb") as f:
                        f.write(response.content)
                    
                    try:
                        return Image.open(BytesIO(response.content))
                    except Exception as e:
                        print(f"解析图片时出错: {str(e)}")
                        if attempt < max_retries - 1:
                            print(f"等待 {retry_delay} 秒后重试...")
                            time.sleep(retry_delay)
                            continue
                else:
                    print(f"请求失败，状态码: {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
            except Exception as e:
                print(f"请求地图时出错: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
        
        print("所有重试都失败了")
        return None
    
    def visualize_points(self, input_points, equidistant_points, fuzzy_points, equidistant_infos, fuzzy_infos):
        """可视化输入点、严格等距点和模糊等距点"""
        # 获取静态地图
        map_image = self.get_static_map(input_points, equidistant_points, fuzzy_points)
        if map_image:
            # 创建图形和子图
            fig = plt.figure(figsize=(20, 12))
            gs = fig.add_gridspec(1, 2, width_ratios=[3, 1])
            ax_map = fig.add_subplot(gs[0])
            ax_legend = fig.add_subplot(gs[1])
            
            # 显示地图
            ax_map.imshow(map_image)
            ax_map.axis('off')
            ax_map.set_title('等距点分布图', fontsize=14, pad=10)
            
            # 准备图例信息
            legend_elements = []
            legend_labels = []
            
            # 添加输入点图例
            for i, point in enumerate(input_points):
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                                markerfacecolor='red', markersize=15))
                legend_labels.append(f"输入点{i+1}: {self.config['input_points'][i]}")
            
            # 添加严格等距点图例
            if equidistant_points:
                for i, (point, info) in enumerate(zip(equidistant_points[:10], equidistant_infos[:10])):
                    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                                    markerfacecolor='blue', markersize=15))
                    legend_labels.append(info)
            
            # 添加模糊等距点图例
            if fuzzy_points:
                for i, (point, info) in enumerate(zip(fuzzy_points[:10], fuzzy_infos[:10])):
                    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                                    markerfacecolor='green', markersize=15))
                    legend_labels.append(info)
            
            # 在右侧子图中显示图例
            ax_legend.axis('off')
            ax_legend.legend(legend_elements, legend_labels,
                           loc='center left',
                           bbox_to_anchor=(0, 0.5),
                           fontsize=12,
                           frameon=True,
                           framealpha=0.8,
                           edgecolor='gray',
                           title='点位信息',
                           title_fontsize=14)
            
            plt.tight_layout()
            
            # 保存完整图片（包含图例）
            plt.savefig('equidistant_points_map.png', 
                       bbox_inches='tight',
                       dpi=300,
                       facecolor='white',
                       edgecolor='none')
            print("已保存完整地图（含图例）到 equidistant_points_map.png")
            
            plt.show()
        else:
            print("无法生成地图可视化") 