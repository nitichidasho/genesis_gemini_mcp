# Genesis Template Library
# 分析したexamplesとtestsから抽出した包括的なコードテンプレート

class GenesisTemplateLibrary:
    """Genesis World用包括的テンプレートライブラリ"""
    
    def __init__(self):
        self.templates = {
            "basic": self._get_basic_templates(),
            "shapes": self._get_shape_templates(), 
            "physics": self._get_physics_templates(),
            "robots": self._get_robot_templates(),
            "materials": self._get_material_templates(),
            "environments": self._get_environment_templates(),
            "sensors": self._get_sensor_templates(),
            "advanced": self._get_advanced_templates(),
            # Genesis Reference準拠の新テンプレート
            "comprehensive_robots": self._get_comprehensive_robot_templates(),
            "advanced_physics": self._get_advanced_physics_templates(),
        }
    
    def _get_basic_templates(self):
        """基本的なGenesisセットアップテンプレート"""
        return {
            "minimal": '''# 最小限のGenesis実行
import genesis as gs
import time

# GPU初期化（デフォルト）
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(show_viewer=True)

# 必須：地面を追加（物理シミュレーションの基盤）
plane = scene.add_entity(gs.morphs.Plane())

# シーン構築
scene.build()

# シミュレーション実行（100ステップ）
for i in range(100):
    scene.step()
    if i % 10 == 0:
        time.sleep(0.01)
        print(f"Step: {i}")
''',
            
            "with_viewer": '''# ビューワー付きGenesis
import genesis as gs
import time

# GPU初期化
gs.init(backend=gs.gpu)

# シーン作成（ビューワー設定付き）
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
        max_FPS=60
    ),
    show_viewer=True
)

# 必須：地面を追加（物理シミュレーションの基盤）
plane = scene.add_entity(gs.morphs.Plane())

# シーン構築
scene.build()

# シミュレーション実行
for i in range(100):
    scene.step()
    if i % 10 == 0:
        time.sleep(0.01)
''',

            "performance": '''# 高性能設定Genesis
import genesis as gs
import time

# GPU初期化（高精度設定）
gs.init(backend=gs.gpu, precision="32")

# 高性能シーン設定
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,  # より細かいタイムステップ
        substeps=10
    ),
    rigid_options=gs.options.RigidOptions(
        max_collision_pairs=2000,
        use_gjk_collision=True,
        enable_mujoco_compatibility=False
    ),
    show_viewer=False  # パフォーマンス優先でビューワー無効
)

# 必須：地面を追加（物理シミュレーションの基盤）
plane = scene.add_entity(gs.morphs.Plane())''',

            "vnc_optimized": '''# VNC最適化Genesis（スムーズ表示）
import genesis as gs
import time

# GPU初期化
gs.init(backend=gs.gpu)

# VNC最適化シーン設定
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, 2.0, 2.0),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=35,
        res=(800, 600),      # VNCサーバーと統一した解像度
        max_FPS=15           # フレームレート制限で安定化
    ),
    sim_options=gs.options.SimOptions(
        dt=0.02,            # 大きなタイムステップで軽量化
        substeps=5          # サブステップ削減
    ),
    show_viewer=True
)

# 必須：地面を追加
plane = scene.add_entity(gs.morphs.Plane())

# シーンをビルド
scene.build()

# VNC最適化シミュレーションループ
for i in range(50):  # 短縮ループ
    scene.step()
    if i % 5 == 0:  # 5ステップ毎に更新
        time.sleep(0.05)  # VNC描画待機
        print(f"VNC最適化ステップ: {i}/50")

# シーン構築
scene.build()

# 高速シミュレーション
for i in range(100):
    scene.step()
'''
        }
    
    def _get_shape_templates(self):
        """形状作成テンプレート"""
        return {
            "sphere": '''# 球体作成
sphere = scene.add_entity(
    gs.morphs.Sphere(
        radius=0.5,
        pos=(0, 0, 2.0)
    )
)''',
            
            "box": '''# 箱作成
box = scene.add_entity(
    gs.morphs.Box(
        size=(1.0, 1.0, 1.0),
        pos=(0, 0, 1.0)
    )
)''',
            
            "cylinder": '''# 円柱作成
cylinder = scene.add_entity(
    gs.morphs.Cylinder(
        radius=0.5,
        height=1.0,
        pos=(0, 0, 1.0)
    )
)''',
            
            "mesh": '''# メッシュ読み込み
mesh = scene.add_entity(
    gs.morphs.Mesh(
        file="meshes/duck.obj",
        scale=1.0,
        pos=(0, 0, 1.0)
    )
)''',
            
            "multiple_boxes": '''# 複数箱作成（タワー）
box_height = 0.2
for i in range(10):
    box = scene.add_entity(
        gs.morphs.Box(
            size=(0.5, 0.5, box_height),
            pos=(0, 0, i * box_height + box_height/2)
        )
    )''',
            
            "pyramid": '''# ピラミッド作成
import numpy as np
box_size = 0.25
num_levels = 5
for level in range(num_levels):
    for x in range(-level, level+1):
        for y in range(-level, level+1):
            box = scene.add_entity(
                gs.morphs.Box(
                    size=(box_size, box_size, box_size),
                    pos=(x * box_size, y * box_size, level * box_size + box_size/2)
                )
            )'''
        }
    
    def _get_physics_templates(self):
        """物理シミュレーションテンプレート"""
        return {
            "gravity_drop": '''# 重力落下シミュレーション
# 空中に複数オブジェクト配置
objects = []
for i in range(5):
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            radius=0.2,
            pos=(i * 0.5 - 1.0, 0, 5.0 + i * 0.5)
        )
    )
    objects.append(sphere)

scene.build()

# 落下シミュレーション
for i in range(100):
    scene.step()
    if i % 20 == 0:
        print(f"Gravity simulation step: {i}")
''',
            
            "collision": '''# 衝突シミュレーション
# 地面
plane = scene.add_entity(gs.morphs.Plane())

# 衝突設定付きシーン
scene = gs.Scene(
    rigid_options=gs.options.RigidOptions(
        max_collision_pairs=1000,
        use_gjk_collision=True
    )
)

# 衝突オブジェクト
ball = scene.add_entity(
    gs.morphs.Sphere(radius=1.0, pos=(0, 0, 5.0))
)
wall = scene.add_entity(
    gs.morphs.Box(size=(0.1, 2.0, 2.0), pos=(3.0, 0, 1.0))
)''',
            
            "external_force": '''# 外力適用
ball = scene.add_entity(
    gs.morphs.Sphere(radius=0.5, pos=(0, 0, 1.0))
)

scene.build()

# シミュレーション中に外力適用
for i in range(100):
    # 右方向に力を加える
    if i == 20:
        ball.set_external_force([10.0, 0, 0])
    scene.step()
''',
            
            "joint_physics": '''# ジョイント物理
# 連結されたボックス
box1 = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 1.0), pos=(0, 0, 1.0))
)
box2 = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 1.0), pos=(0, 0, 2.5))
)

# ジョイント作成
joint = scene.add_joint(
    parent=box1,
    child=box2,
    type="revolute"
)'''
        }
    
    def _get_robot_templates(self):
        """ロボットテンプレート - 正しいGenesis API使用"""
        return {
            "franka_basic": '''# Frankaロボットアーム - 基本制御
import numpy as np

# 必須：地面を追加
plane = scene.add_entity(gs.morphs.Plane())

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# 関節名の定義（Frankaアームの標準構成）
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)

# DOFインデックスを取得
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 制御ゲインの設定（オプション）
franka.set_dofs_kp(
    np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]),
    motors_dof_idx,
)
franka.set_dofs_kv(
    np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]),
    motors_dof_idx,
)

# シミュレーション実行
for i in range(200):
    scene.step()
''',

            "franka_position_control": '''# Frankaアーム - 位置制御
import numpy as np

# 必須：シーンは既にビルド済みと仮定
# 関節名の定義
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)

# DOFインデックスを取得
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 位置制御：全ての関節を0位置に移動
target_positions = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
franka.control_dofs_position(target_positions, motors_dof_idx)

# シミュレーション実行（アームが目標位置に到達するまで）
for i in range(500):
    scene.step()
''',

            "franka_joint_sequence": '''# Frankaアーム - 関節シーケンス制御
import numpy as np

# 関節名とDOFインデックス取得
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 複数のポーズを順次実行
poses = [
    np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),  # ホームポジション
    np.array([1, 1, 0, 0, 0, 0, 0, 0.04, 0.04]),  # ポーズ1
    np.array([-1, 0.8, 1, -2, 1, 0.5, -0.5, 0.04, 0.04]),  # ポーズ2
]

# シーケンス実行
for pose_idx, target_pose in enumerate(poses):
    print(f"移動中: ポーズ {pose_idx + 1}")
    franka.control_dofs_position(target_pose, motors_dof_idx)
    
    # 各ポーズで十分な時間待機
    for i in range(250):
        scene.step()
''',

            "franka_velocity_control": '''# Frankaアーム - 速度制御
import numpy as np

# 関節名とDOFインデックス取得
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 速度制御：第1関節のみ回転、他は静止
velocity_commands = np.array([1.0, 0, 0, 0, 0, 0, 0, 0, 0])
franka.control_dofs_velocity(velocity_commands, motors_dof_idx)

# 一定時間速度制御を実行
for i in range(500):
    scene.step()
    
    # 途中で停止
    if i == 250:
        stop_commands = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
        franka.control_dofs_velocity(stop_commands, motors_dof_idx)
''',

            "franka_force_control": '''# Frankaアーム - 力制御
import numpy as np

# 関節名とDOFインデックス取得
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 力制御：全関節に0トルクを印加（重力補償等）
force_commands = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
franka.control_dofs_force(force_commands, motors_dof_idx)

# 力制御実行
for i in range(300):
    # 現在の制御力を確認
    current_forces = franka.get_dofs_control_force(motors_dof_idx)
    if i % 50 == 0:
        print(f"制御力: {current_forces}")
    
    scene.step()
''',

            "robot_grasp": '''# ロボットグラスプ - 正しいAPI使用
import numpy as np

# ロボット（既存のfrankaを使用）
# グラスプ対象
cube = scene.add_entity(
    gs.morphs.Box(size=(0.05, 0.05, 0.05), pos=(0.5, 0, 0.1))
)

# 関節名とDOFインデックス取得
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# グラスプシーケンス
# アプローチポーズ
approach_pose = np.array([0, 0, 0, -1.5, 0, 1.5, 0.8, 0.04, 0.04])
franka.control_dofs_position(approach_pose, motors_dof_idx)

for i in range(150):
    scene.step()

# グラスプポーズ（指を閉じる）
grasp_pose = np.array([0, 0, 0, -1.5, 0, 1.5, 0.8, 0.0, 0.0])
franka.control_dofs_position(grasp_pose, motors_dof_idx)

for i in range(100):
    scene.step()
''',
            
            "multi_robot": '''# 複数ロボット
import numpy as np

robots = []
for i in range(3):
    robot = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
        pos=(i * 2.0, 0, 0)
    )
    robots.append(robot)

scene.build()

# 各ロボットを同期制御
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)

for robot_idx, robot in enumerate(robots):
    motors_dof_idx = [robot.get_joint(name).dofs_idx_local[0] for name in joints_name]
    
    # 各ロボットに異なるポーズを設定
    pose = np.array([robot_idx * 0.5, 0, 0, -1.0, 0, 1.0, 0, 0, 0])
    robot.control_dofs_position(pose, motors_dof_idx)

for i in range(300):
    scene.step()
''',
        }
    
    def _get_material_templates(self):
        """材質・表面特性テンプレート"""
        return {
            "bouncy": '''# 弾性材質
bouncy_ball = scene.add_entity(
    gs.morphs.Sphere(radius=0.5, pos=(0, 0, 5.0)),
    material=gs.materials.Rigid(
        restitution=0.9,  # 高い反発係数
        friction=0.1
    )
)''',
            
            "friction": '''# 摩擦設定
# 低摩擦
slippery_box = scene.add_entity(
    gs.morphs.Box(size=(1.0, 1.0, 1.0), pos=(0, 0, 1.0)),
    material=gs.materials.Rigid(friction=0.1)
)

# 高摩擦
sticky_box = scene.add_entity(
    gs.morphs.Box(size=(1.0, 1.0, 1.0), pos=(2, 0, 1.0)),
    material=gs.materials.Rigid(friction=1.5)
)''',
            
            "density": '''# 密度設定
# 重いオブジェクト
heavy_sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.5, pos=(0, 0, 2.0)),
    material=gs.materials.Rigid(density=1000.0)
)

# 軽いオブジェクト
light_sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.5, pos=(1, 0, 2.0)),
    material=gs.materials.Rigid(density=100.0)
)'''
        }
    
    def _get_environment_templates(self):
        """環境設定テンプレート"""
        return {
            "terrain": '''# 地形作成
import numpy as np

# 高さマップ地形
height_field = np.random.random((64, 64)) * 2.0
terrain = scene.add_entity(
    gs.morphs.HeightField(
        height=height_field,
        horizontal_scale=0.1
    )
)''',
            
            "lighting": '''# 照明設定
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        ambient_light=(0.3, 0.3, 0.3),
        directional_light_dir=(-1, -1, -1),
        directional_light_color=(1.0, 1.0, 1.0)
    )
)''',
            
            "camera": '''# カメラ設定
camera = scene.add_camera(
    res=(1280, 720),
    pos=(3.0, 3.0, 3.0),
    lookat=(0, 0, 0),
    fov=45,
    GUI=True
)

# カメラレンダリング
for i in range(100):
    scene.step()
    if i % 10 == 0:
        image = camera.render()
'''
        }
    
    def _get_sensor_templates(self):
        """センサーテンプレート"""
        return {
            "lidar": '''# LiDARセンサー
lidar = scene.add_lidar(
    pos=(0, 0, 1.0),
    range_max=10.0,
    n_rays=360,
    angle_range=(-np.pi, np.pi)
)

for i in range(100):
    scene.step()
    if i % 20 == 0:
        scan_data = lidar.get_data()
        print(f"LiDAR ranges: {scan_data[:10]}")  # 最初の10点を表示
''',
            
            "imu": '''# IMUセンサー
robot = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0, 0, 1.0))
)

imu = scene.add_imu(
    entity=robot,
    local_pos=(0, 0, 0)
)

for i in range(100):
    scene.step()
    if i % 20 == 0:
        acc_data = imu.get_acceleration()
        gyro_data = imu.get_angular_velocity()
        print(f"Accel: {acc_data}, Gyro: {gyro_data}")
'''
        }
    
    def _get_advanced_templates(self):
        """高度なテンプレート"""
        return {
            "soft_body": '''# ソフトボディ
cloth = scene.add_entity(
    gs.morphs.Cloth(
        size=(2.0, 2.0),
        resolution=(20, 20),
        pos=(0, 0, 3.0)
    )
)

# 布の一部を固定
cloth.pin_vertices([0, 19, 380, 399])  # 四隅を固定

for i in range(100):
    scene.step()
    if i % 20 == 0:
        # 風力適用
        cloth.apply_wind_force([1.0, 0, 0])
''',
            
            "fluid": '''# 流体シミュレーション
# 容器作成
container = []
for pos in [(-2, 0, 0), (2, 0, 0), (0, -2, 0), (0, 2, 0)]:
    wall = scene.add_entity(
        gs.morphs.Box(size=(0.1, 4.0, 2.0), pos=pos)
    )
    container.append(wall)

# 流体パーティクル
fluid = scene.add_entity(
    gs.morphs.SPHLiquid(
        n_particles=1000,
        particle_radius=0.02,
        pos=(0, 0, 1.0)
    )
)

for i in range(100):
    scene.step()
''',
            
            "muscle": '''# 筋肉システム
# 骨格
bone1 = scene.add_entity(
    gs.morphs.Box(size=(0.1, 0.1, 1.0), pos=(0, 0, 0.5))
)
bone2 = scene.add_entity(
    gs.morphs.Box(size=(0.1, 0.1, 1.0), pos=(0, 0, 1.5))
)

# 筋肉
muscle = scene.add_muscle(
    attachment_0=bone1,
    attachment_1=bone2,
    max_force=100.0,
    optimal_length=0.8
)

for i in range(100):
    scene.step()
    if i % 20 == 0:
        # 筋肉収縮
        activation = 0.5 + 0.5 * math.sin(i * 0.1)
        muscle.set_activation(activation)
'''
        }
    
    def get_template_by_keywords(self, keywords):
        """キーワードに基づいてテンプレート検索 - 拡張版"""
        keywords = [k.lower() for k in keywords]
        matches = []
        
        # キーワードマッピング拡張
        keyword_mapping = {
            'ロボット': ['robot', 'franka', 'arm', 'manipulation', 'control'],
            '制御': ['control', 'pid', 'position', 'velocity', 'force'],
            '関節': ['joint', 'dof', 'motors'],
            'センサー': ['sensor', 'imu', 'lidar', 'contact', 'force'],
            '物理': ['physics', 'collision', 'gravity', 'dynamics'],
            'グラスプ': ['grasp', 'grip', 'manipulation', 'cube'],
            'IMU': ['imu', 'accelerometer', 'gyroscope'],
            'バッチ': ['batch', 'multi', 'parallel'],
            '重力補償': ['gravity', 'compensation'],
            '外力': ['external', 'force', 'torque'],
            'LiDAR': ['lidar', 'laser', 'distance'],
        }
        
        # 拡張キーワード検索
        expanded_keywords = set(keywords)
        for keyword in keywords:
            for jp_key, en_values in keyword_mapping.items():
                if keyword in jp_key.lower() or keyword in en_values:
                    expanded_keywords.update(en_values)
                    expanded_keywords.add(jp_key.lower())
        
        for category, templates in self.templates.items():
            for name, code in templates.items():
                relevance = 0
                relevance = 0
                for keyword in expanded_keywords:
                    if keyword in name.lower():
                        relevance += 3  # 名前での一致は高得点
                    if keyword in code.lower():
                        relevance += 1  # コード内の一致
                        
                if relevance > 0:
                    matches.append({
                        'category': category,
                        'name': name,
                        'code': code,
                        'relevance': relevance
                    })
        
        # 関連度でソート
        matches.sort(key=lambda x: x['relevance'], reverse=True)
        return matches[:8]  # 上位8件を返す（テンプレートが増えたため）
    
    def get_category_templates(self, category):
        """カテゴリ別テンプレート取得"""
        return self.templates.get(category, {})

    def _get_comprehensive_robot_templates(self):
        """Genesis Reference から抽出した包括的ロボットテンプレート"""
        return {
            "control_franka_complete": '''# 完全なFrankaロボット制御（Genesis Reference準拠）
import argparse
import numpy as np
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# ビューワーオプション
viewer_options = gs.options.ViewerOptions(
    camera_pos=(0, -3.5, 2.5),
    camera_lookat=(0.0, 0.0, 0.5),
    camera_fov=40,
    max_FPS=60,
)

# シーン作成
scene = gs.Scene(
    viewer_options=viewer_options,
    sim_options=gs.options.SimOptions(dt=0.01),
    show_viewer=True,
)

# エンティティ
plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

# シーンビルド
scene.build()

# 関節名とDOFインデックス
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 制御ゲイン設定
franka.set_dofs_kp(
    np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]),
    motors_dof_idx,
)
franka.set_dofs_kv(
    np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]),
    motors_dof_idx,
)
franka.set_dofs_force_range(
    np.array([-87, -87, -87, -87, -12, -12, -12, -100, -100]),
    np.array([87, 87, 87, 87, 12, 12, 12, 100, 100]),
    motors_dof_idx,
)

# ハードリセット
for i in range(150):
    if i < 50:
        franka.set_dofs_position(np.array([1, 1, 0, 0, 0, 0, 0, 0.04, 0.04]), motors_dof_idx)
    elif i < 100:
        franka.set_dofs_position(np.array([-1, 0.8, 1, -2, 1, 0.5, -0.5, 0.04, 0.04]), motors_dof_idx)
    else:
        franka.set_dofs_position(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]), motors_dof_idx)
    scene.step()

# PD制御シーケンス
for i in range(1250):
    if i == 0:
        franka.control_dofs_position(
            np.array([1, 1, 0, 0, 0, 0, 0, 0.04, 0.04]),
            motors_dof_idx,
        )
    elif i == 250:
        franka.control_dofs_position(
            np.array([-1, 0.8, 1, -2, 1, 0.5, -0.5, 0.04, 0.04]),
            motors_dof_idx,
        )
    elif i == 500:
        franka.control_dofs_position(
            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
            motors_dof_idx,
        )
    elif i == 750:
        # 速度制御と位置制御の組み合わせ
        franka.control_dofs_position(
            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])[1:],
            motors_dof_idx[1:],
        )
        franka.control_dofs_velocity(
            np.array([1.0, 0, 0, 0, 0, 0, 0, 0, 0])[:1],
            motors_dof_idx[:1],
        )
    elif i == 1000:
        franka.control_dofs_force(
            np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
            motors_dof_idx,
        )
    
    # 制御力の取得
    print("control force:", franka.get_dofs_control_force(motors_dof_idx))
    scene.step()
''',

            "franka_cube_manipulation": '''# Frankaによるキューブ操作（Genesis Reference準拠）
import numpy as np
import genesis as gs

# 初期化
gs.init(backend=gs.gpu, precision="32")

# シーン作成
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, -1, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        res=(960, 640),
        max_FPS=60,
    ),
    sim_options=gs.options.SimOptions(dt=0.01),
    rigid_options=gs.options.RigidOptions(box_box_detection=True),
    show_viewer=True,
)

# エンティティ
plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)
cube = scene.add_entity(
    gs.morphs.Box(
        size=(0.04, 0.04, 0.04),
        pos=(0.65, 0.0, 0.02),
    )
)

# シーンビルド
scene.build()

# DOFインデックス
motors_dof = np.arange(7)
fingers_dof = np.arange(7, 9)

# 初期姿勢設定
qpos = np.array([-1.0124, 1.5559, 1.3662, -1.6878, -1.5799, 1.7757, 1.4602, 0.04, 0.04])
franka.set_qpos(qpos)
scene.step()

# 逆運動学でキューブ上の位置を計算
end_effector = franka.get_link("hand")
qpos = franka.inverse_kinematics(
    link=end_effector,
    pos=np.array([0.65, 0.0, 0.135]),
    quat=np.array([0, 1, 0, 0]),
)

# 位置制御
franka.control_dofs_position(qpos[:-2], motors_dof)

# ホールド
for i in range(100):
    print("hold", i)
    scene.step()

# グラスプ
finder_pos = -0.0
for i in range(100):
    print("grasp", i)
    franka.control_dofs_position(qpos[:-2], motors_dof)
    franka.control_dofs_position(np.array([finder_pos, finder_pos]), fingers_dof)
    scene.step()

# リフト
qpos = franka.inverse_kinematics(
    link=end_effector,
    pos=np.array([0.65, 0.0, 0.3]),
    quat=np.array([0, 1, 0, 0]),
)
franka.control_dofs_position(qpos[:-2], motors_dof)

for i in range(200):
    print("lift", i)
    scene.step()
''',

            "single_franka_basic": '''# 基本的なFrankaロボット（Genesis Reference準拠）
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
    rigid_options=gs.options.RigidOptions(),
    show_viewer=True,
)

# エンティティ
plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    visualize_contact=True,
)

# カメラ
cam_0 = scene.add_camera(
    res=(1280, 960),
    pos=(3.5, 0.0, 2.5),
    lookat=(0, 0, 0.5),
    fov=30,
    GUI=True,
)

# シーンビルド
scene.build()

# シミュレーション実行
for i in range(1000):
    scene.step()
    # cam_0.render()  # オプション：レンダリング
''',

            "imu_sensor_setup": '''# IMUセンサー付きFranka（Genesis Reference準拠）
import numpy as np
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=1e-2),
    vis_options=gs.options.VisOptions(show_world_frame=False),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
    profiling_options=gs.options.ProfilingOptions(show_FPS=False),
    show_viewer=True,
)

# エンティティ
scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)
end_effector = franka.get_link("hand")
motors_dof = (0, 1, 2, 3, 4, 5, 6)

# IMUセンサーの追加
imu = scene.add_sensor(
    gs.sensors.IMU(
        entity_idx=franka.idx,
        link_idx_local=end_effector.idx_local,
        pos_offset=(0.0, 0.0, 0.15),
        # ノイズパラメータ
        acc_axes_skew=(0.0, 0.01, 0.02),
        gyro_axes_skew=(0.03, 0.04, 0.05),
        acc_noise=(0.01, 0.01, 0.01),
        gyro_noise=(0.01, 0.01, 0.01),
    ),
)

# シーンビルド
scene.build()

# 制御ゲイン設定
franka.set_dofs_kp(1000.0, motors_dof)
franka.set_dofs_kv(100.0, motors_dof)

# シミュレーション実行
target_q = np.array([0.0, -np.pi / 4, 0.0, -3 * np.pi / 4, 0.0, np.pi / 2, np.pi / 4])

for i in range(300):
    # アーム制御
    if i == 0:
        franka.control_dofs_position(target_q, motors_dof)
    elif i == 100:
        # 振動させる
        target_q_vibrate = target_q + 0.1 * np.sin(i * 0.1) * np.ones_like(target_q)
        franka.control_dofs_position(target_q_vibrate, motors_dof)
    
    scene.step()
    
    # IMUデータの取得
    if i % 10 == 0:
        imu_data = imu.get_data()
        print(f"Step {i}: Acceleration: {imu_data['acc']}, Angular velocity: {imu_data['gyro']}")
''',

            "batched_multi_env": '''# バッチ環境でのマルチロボット（Genesis Reference準拠）
import torch
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# マルチ環境設定
num_envs = 10

# シーン作成
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01, substeps=2),
    rigid_options=gs.options.RigidOptions(
        dt=0.01,
        constraint_solver=gs.constraint_solver.Newton,
        enable_collision=True,
        enable_joint_limit=True,
    ),
    vis_options=gs.options.VisOptions(rendered_envs_idx=list(range(10))),
    viewer_options=gs.options.ViewerOptions(
        max_FPS=30,
        camera_pos=(2.0, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
    renderer=gs.options.renderers.BatchRenderer(use_rasterizer=True),
    show_viewer=True,
)

# 複数環境にエンティティを追加
planes = []
frankas = []

for i in range(num_envs):
    plane = scene.add_entity(
        gs.morphs.Plane(),
        env_idx=i,
    )
    franka = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
        env_idx=i,
    )
    planes.append(plane)
    frankas.append(franka)

# シーンビルド
scene.build()

# 制御用DOFインデックス
motors_dof = torch.arange(7, device=gs.device)

# バッチ制御ゲイン設定
kp_values = torch.full((num_envs, 7), 1000.0, device=gs.device)
kv_values = torch.full((num_envs, 7), 100.0, device=gs.device)

for i, franka in enumerate(frankas):
    franka.set_dofs_kp(kp_values[i], motors_dof)
    franka.set_dofs_kv(kv_values[i], motors_dof)

# バッチシミュレーション実行
target_positions = torch.zeros((num_envs, 7), device=gs.device)
target_positions[:, 1] = -torch.pi / 4
target_positions[:, 3] = -3 * torch.pi / 4
target_positions[:, 5] = torch.pi / 2
target_positions[:, 6] = torch.pi / 4

for i in range(500):
    # 各環境で異なる目標を設定
    if i % 100 == 0:
        for j, franka in enumerate(frankas):
            # 環境ごとに少し異なる目標
            offset = torch.randn(7, device=gs.device) * 0.1
            franka.control_dofs_position(target_positions[j] + offset, motors_dof)
    
    scene.step()
    
    if i % 50 == 0:
        print(f"Step {i}: Multi-environment simulation running")
''',
        }

    def _get_advanced_physics_templates(self):
        """高度な物理シミュレーションテンプレート"""
        return {
            "contact_force_sensor": '''# 接触力センサー（Genesis Reference準拠）
import numpy as np
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    rigid_options=gs.options.RigidOptions(enable_collision=True),
    show_viewer=True,
)

# エンティティ
plane = scene.add_entity(gs.morphs.Plane())
robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/go2/go2.xml"),  # または他のロボット
)

# 接触力センサーの追加
contact_sensor = scene.add_sensor(
    gs.sensors.ContactForceSensor(
        entity_idx=robot.idx,
        link_name="foot_l",  # ロボットの足部
    ),
)

# シーンビルド
scene.build()

# シミュレーション実行
for i in range(1000):
    scene.step()
    
    # 接触力データの取得
    if i % 10 == 0:
        contact_data = contact_sensor.get_data()
        if contact_data is not None:
            print(f"Step {i}: Contact force: {contact_data['force']}")
''',

            "lidar_sensor": '''# LiDARセンサー（Genesis Reference準拠）
import numpy as np
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(5, 5, 3),
        camera_lookat=(0, 0, 0),
    ),
    show_viewer=True,
)

# 環境の作成
plane = scene.add_entity(gs.morphs.Plane())

# 障害物の追加
for i in range(10):
    scene.add_entity(
        gs.morphs.Box(
            size=(0.5, 0.5, 1.0),
            pos=(np.random.uniform(-5, 5), np.random.uniform(-5, 5), 0.5),
        )
    )

# ロボットの追加
robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/go2/go2.xml"),
)

# LiDARセンサーの追加
lidar = scene.add_sensor(
    gs.sensors.LiDAR(
        entity_idx=robot.idx,
        link_name="base",
        pos_offset=(0, 0, 0.3),
        min_range=0.1,
        max_range=10.0,
        num_rays=360,
        fov=2 * np.pi,
    ),
)

# シーンビルド
scene.build()

# シミュレーション実行
for i in range(1000):
    scene.step()
    
    # LiDARデータの取得
    if i % 20 == 0:
        lidar_data = lidar.get_data()
        distances = lidar_data['distance']
        print(f"Step {i}: LiDAR min distance: {np.min(distances):.2f}, max: {np.max(distances):.2f}")
''',

            "gravity_compensation": '''# 重力補償制御（Genesis Reference準拠）
import numpy as np
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    show_viewer=True,
)

# エンティティ
plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

# シーンビルド
scene.build()

# DOFインデックス
motors_dof = np.arange(7)

# 初期姿勢
qpos_init = np.array([0, -np.pi/4, 0, -3*np.pi/4, 0, np.pi/2, np.pi/4])
franka.set_qpos(qpos_init)

# 制御ゲイン（重力補償用）
franka.set_dofs_kp(np.zeros(7), motors_dof)  # 位置ゲインを0に
franka.set_dofs_kv(np.full(7, 10.0), motors_dof)  # 小さい速度ゲイン

# シミュレーション実行
for i in range(1000):
    # 現在の関節角度と速度を取得
    qpos = franka.get_dofs_position(motors_dof)
    qvel = franka.get_dofs_velocity(motors_dof)
    
    # 重力補償トルクの計算（簡易版）
    # 実際の重力補償には動力学モデルが必要
    gravity_torque = franka.compute_inverse_dynamics(qpos, qvel, np.zeros(7))
    
    # 重力補償制御
    franka.control_dofs_force(gravity_torque, motors_dof)
    
    scene.step()
    
    if i % 100 == 0:
        print(f"Step {i}: Gravity compensation active")
''',

            "external_force_application": '''# 外力印加（Genesis Reference準拠）
import numpy as np
import genesis as gs

# 初期化
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    show_viewer=True,
)

# エンティティ
plane = scene.add_entity(gs.morphs.Plane())
box = scene.add_entity(
    gs.morphs.Box(
        size=(0.2, 0.2, 0.2),
        pos=(0, 0, 1.0),
        material=gs.materials.Rigid(density=1000.0),
    )
)

# シーンビルド
scene.build()

# シミュレーション実行
for i in range(1000):
    # 周期的な外力の印加
    if 100 <= i < 200:
        # X方向に力を印加
        force = np.array([50.0, 0.0, 0.0])
        torque = np.array([0.0, 0.0, 0.0])
        box.apply_external_force_and_torque(
            force=force,
            torque=torque,
            link_idx=0,  # メインボディ
        )
    elif 300 <= i < 400:
        # Y方向に力を印加
        force = np.array([0.0, 50.0, 0.0])
        torque = np.array([0.0, 0.0, 10.0])  # Z軸回りのトルクも印加
        box.apply_external_force_and_torque(
            force=force,
            torque=torque,
            link_idx=0,
        )
    
    scene.step()
    
    if i % 50 == 0:
        pos = box.get_pos()
        print(f"Step {i}: Box position: {pos}")
''',
        }

# 既存のテンプレートライブラリを拡張
def enhance_genesis_templates():
    """GenesisTemplateLibraryに新しいテンプレートを追加"""
    # この関数は新しいテンプレートをライブラリに統合するために使用
    pass